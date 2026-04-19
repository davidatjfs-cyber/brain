from app.brain_core import make_decision
from app.models import StoreInput
import uuid


def run_shadow(input_data: dict, real_decision: dict) -> dict:
    defaults = {
        "store_id": input_data.get("store_id", f"shadow_{uuid.uuid4().hex[:8]}"),
        "date": input_data.get("date", "2026-04-11"),
        "menu": input_data.get("menu", []),
        "feedback": input_data.get("feedback", []),
    }

    store_input = StoreInput(**{**defaults, **input_data})
    brain_result = make_decision(store_input)

    return {
        "real_decision": real_decision,
        "brain_decision": brain_result,
    }
