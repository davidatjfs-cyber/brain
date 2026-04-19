import json
import os
from typing import List

from app.models import DecisionRecord

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DATA_FILE = os.path.join(DATA_DIR, "decisions.json")


def _ensure_file():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False)


def load_all() -> List[DecisionRecord]:
    _ensure_file()
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return [DecisionRecord(**r) for r in raw]


def save(record: DecisionRecord):
    records = load_all()
    records.append(record)
    _write_all(records)


def update(record: DecisionRecord):
    records = load_all()
    for i, r in enumerate(records):
        if r.decision.decision_id == record.decision.decision_id:
            records[i] = record
            break
    _write_all(records)


def _write_all(records: List[DecisionRecord]):
    _ensure_file()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(
            [r.model_dump() for r in records],
            f,
            ensure_ascii=False,
            indent=2,
        )


def get_recent_decisions(n: int = 5) -> List[DecisionRecord]:
    records = load_all()
    if len(records) <= n:
        return records

    evaluated = [r for r in records if r.evaluation is not None]
    if len(evaluated) <= n:
        return sorted(records, key=lambda r: r.timestamp, reverse=True)[:n]

    sorted_by_score = sorted(
        evaluated,
        key=lambda r: r.evaluation.score,
        reverse=True,
    )

    picked_ids = set()
    result = []

    top2 = sorted_by_score[:2]
    for r in top2:
        picked_ids.add(r.decision.decision_id)
        result.append(r)

    bottom2 = sorted_by_score[-2:]
    for r in bottom2:
        if r.decision.decision_id not in picked_ids:
            picked_ids.add(r.decision.decision_id)
            result.append(r)

    others = [r for r in records if r.decision.decision_id not in picked_ids]
    others.sort(key=lambda r: r.timestamp, reverse=True)
    for r in others:
        if len(result) >= n:
            break
        picked_ids.add(r.decision.decision_id)
        result.append(r)

    return result
