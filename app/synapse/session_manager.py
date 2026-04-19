import json
import time
import os
from typing import Dict, Any, Optional

CONVERSATION_STORE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "synapse", "conversations.json"
)

SESSION_TIMEOUT = 1800


def _ensure_dir():
    os.makedirs(os.path.dirname(CONVERSATION_STORE), exist_ok=True)


def _load_conversations() -> dict:
    _ensure_dir()
    if not os.path.exists(CONVERSATION_STORE):
        return {}
    with open(CONVERSATION_STORE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_conversations(conv: dict):
    _ensure_dir()
    with open(CONVERSATION_STORE, "w", encoding="utf-8") as f:
        json.dump(conv, f, ensure_ascii=False, indent=2)


def get_session(user_id: str) -> dict:
    convs = _load_conversations()
    session = convs.get(user_id, {})
    if session and time.time() - session.get("updated_at", 0) > SESSION_TIMEOUT:
        session = {}
    return session


def update_session(user_id: str, state: str, context: dict = None):
    convs = _load_conversations()
    session = convs.get(user_id, {})
    session["state"] = state
    if context:
        session.setdefault("context", {}).update(context)
    session["updated_at"] = time.time()
    convs[user_id] = session
    _save_conversations(convs)


def clear_session(user_id: str):
    convs = _load_conversations()
    convs.pop(user_id, None)
    _save_conversations(convs)