import json
import time
import os
import requests as http_requests
from typing import Optional

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from app.synapse.chat_handler import process_message, handle_evaluation_feedback

router = APIRouter(prefix="/feishu", tags=["feishu"])

_pending_responses = {}
_debug_log = []
_access_token_cache = {"token": "", "expires": 0}


def _get_access_token() -> str:
    app_id = os.environ.get("FEISHU_APP_ID", "")
    app_secret = os.environ.get("FEISHU_APP_SECRET", "")

    if not app_id or not app_secret:
        return ""

    now = time.time()
    if _access_token_cache["token"] and _access_token_cache["expires"] > now:
        return _access_token_cache["token"]

    resp = http_requests.post(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": app_id, "app_secret": app_secret},
        timeout=10,
    )
    data = resp.json()
    token = data.get("tenant_access_token", "")
    expire = data.get("expire", 7200)

    if token:
        _access_token_cache["token"] = token
        _access_token_cache["expires"] = now + expire - 300

    return token


def _send_feishu_message(receive_id: str, text: str, receive_id_type: str = "open_id", msg_type: str = "text") -> dict:
    token = _get_access_token()
    if not token:
        _debug_log.append({"ts": time.time(), "error": "no_token"})
        return {"status": "no_token"}

    if msg_type == "interactive":
        content = json.dumps(text, ensure_ascii=False)
    else:
        content = json.dumps({"text": text}, ensure_ascii=False)

    resp = http_requests.post(
        f"https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type={receive_id_type}",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={
            "receive_id": receive_id,
            "msg_type": msg_type,
            "content": content,
        },
        timeout=15,
    )
    result = resp.json()
    _debug_log.append({
        "ts": time.time(),
        "action": "send_message",
        "receive_id": receive_id[:30],
        "receive_id_type": receive_id_type,
        "code": result.get("code"),
        "msg": str(result.get("msg", ""))[:100],
    })
    return result


def _send_reply_in_chat(chat_id: str, text: str) -> dict:
    token = _get_access_token()
    if not token:
        return {"status": "no_token"}

    content = json.dumps({"text": text}, ensure_ascii=False)
    resp = http_requests.post(
        "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={
            "receive_id": chat_id,
            "msg_type": "text",
            "content": content,
        },
        timeout=15,
    )
    result = resp.json()
    _debug_log.append({
        "ts": time.time(),
        "action": "send_to_chat",
        "chat_id": chat_id[:20],
        "code": result.get("code"),
        "msg": str(result.get("msg", ""))[:100],
    })
    return result


def _build_card(reply_text: str, agent_name: str = "", suggestions: list = None) -> dict:
    elements = []

    elements.append({
        "tag": "markdown",
        "content": reply_text[:4000],
    })

    if suggestions:
        buttons = []
        for s in suggestions[:6]:
            buttons.append({
                "tag": "button",
                "text": {"tag": "plain_text", "content": s.get("text", "")[:20]},
                "value": {"action": "suggest", "value": s.get("value", "")},
                "type": "default",
            })
        if buttons:
            elements.append({
                "tag": "action",
                "actions": buttons,
            })

    return {
        "header": {
            "template": "blue",
            "title": {"tag": "plain_text", "content": "🧙🏾‍♂️ Professor Synapse"},
        },
        "elements": elements,
    }


def _send_reply_to_user(open_id: str, user_id: str, result: dict, chat_id: str = ""):
    text = result.get("text", "")
    suggestions = result.get("suggestions")

    if chat_id:
        reply_text = text
        if suggestions:
            btns = "\n".join(f"• {s['text']}" for s in suggestions[:6])
            reply_text += f"\n\n{btns}"
        resp = _send_reply_in_chat(chat_id, reply_text)
        if resp.get("code") == 0:
            return resp
        _debug_log.append({"ts": time.time(), "chat_send_failed": True, "code": resp.get("code"), "msg": str(resp.get("msg", ""))[:100]})

    for rid_type, rid in [("open_id", open_id), ("user_id", user_id)]:
        if not rid:
            continue

        if suggestions:
            card = _build_card(text, result.get("agent_name", ""), suggestions)
            resp = _send_feishu_message(rid, card, receive_id_type=rid_type, msg_type="interactive")
        else:
            resp = _send_feishu_message(rid, text, receive_id_type=rid_type, msg_type="text")

        if resp.get("code") == 0:
            return resp

    return {"status": "all_send_failed", "debug": _debug_log[-3:], "chat_id": chat_id, "open_id": open_id, "user_id": user_id}


@router.post("/webhook")
async def feishu_webhook(request: Request):
    body = await request.json()

    _debug_log.append({"ts": time.time(), "raw_keys": list(body.keys()), "has_challenge": bool(body.get("challenge"))})
    _debug_log.append({"ts": time.time(), "raw_body_sample": json.dumps(body, ensure_ascii=False)[:500]})

    if body.get("challenge"):
        return {"challenge": body["challenge"]}

    header = body.get("header", {})
    event = body.get("event", {})

    msg_event = event.get("message", {})
    if not msg_event:
        _debug_log.append({"ts": time.time(), "note": "no_message_event", "event_keys": list(event.keys())})
        return {"status": "no_message"}

    sender = event.get("sender", {}) or msg_event.get("sender", {})
    sender_id = sender.get("sender_id", sender.get("user_id", {}))
    open_id = ""
    if isinstance(sender_id, dict):
        open_id = sender_id.get("open_id", "")
        user_id = sender_id.get("user_id", "")
        union_id = sender_id.get("union_id", "")
    elif isinstance(sender_id, str):
        open_id = sender_id
        user_id = sender_id
    else:
        user_id = str(sender_id)

    chat_id = msg_event.get("chat_id", "")
    chat_type = msg_event.get("chat_type", "")
    message_id = msg_event.get("message_id", "")

    if not open_id and not user_id and not chat_id:
        all_sender_keys = list(sender.keys()) if isinstance(sender, dict) else []
        all_msg_keys = list(msg_event.keys())
        all_event_keys = list(event.keys())
        _debug_log.append({
            "ts": time.time(),
            "note": "NO_IDS",
            "sender_keys": all_sender_keys,
            "sender_id_type": str(type(sender_id)),
            "msg_keys": all_msg_keys,
            "event_keys": all_event_keys,
            "chat_id": chat_id,
        })

    msg_type = msg_event.get("message_type", "text")
    content = msg_event.get("content", "{}")

    text = ""
    try:
        content_data = json.loads(content) if isinstance(content, str) else content
        if msg_type == "text":
            text = content_data.get("text", "")
        elif msg_type == "post":
            content_list = content_data.get("content", [[]])
            for paragraph in content_list:
                for elem in paragraph:
                    if isinstance(elem, dict) and elem.get("tag") == "text":
                        text += elem.get("text", "")
        else:
            text = str(content_data)
    except (json.JSONDecodeError, AttributeError):
        text = str(content)

    _debug_log.append({
        "ts": time.time(),
        "action": "received",
        "open_id": open_id[:20] if open_id else "",
        "user_id": user_id[:20] if user_id else "",
        "msg_type": msg_type,
        "text": text[:100],
    })

    if not text.strip():
        return {"status": "empty_message"}

    try:
        result = process_message(text, open_id or user_id)
    except Exception as e:
        _debug_log.append({"ts": time.time(), "error": str(e)[:200]})
        return {"status": "process_error"}

    _pending_responses[open_id or user_id] = {
        "result": result,
        "timestamp": time.time(),
    }

    try:
        send_result = _send_reply_to_user(open_id, user_id, result, chat_id=chat_id)
        _debug_log.append({"ts": time.time(), "send_result": str(send_result.get("code") or send_result.get("status", ""))[:50]})
    except Exception as e:
        _debug_log.append({"ts": time.time(), "send_error": str(e)[:200]})

    return {"status": "processed"}


@router.post("/send")
async def feishu_send_message(body: dict):
    user_id = body.get("user_id", "")
    message = body.get("message", "")

    if not user_id or not message:
        raise HTTPException(status_code=422, detail="user_id和message必填")

    result = process_message(message, user_id)

    try:
        _send_reply_to_user(user_id, user_id, result)
    except Exception:
        pass

    return result


@router.post("/feedback")
async def feishu_feedback(body: dict):
    agent_name = body.get("agent_name", "")
    feedback_type = body.get("feedback_type", "")
    user_message = body.get("user_message", "")
    agent_response = body.get("agent_response", "")

    if not agent_name or feedback_type not in ("thumbs_up", "thumbs_down"):
        raise HTTPException(status_code=422, detail="需要agent_name和有效feedback_type")

    from app.synapse.feedback_loop import record_feedback
    return record_feedback(agent_name, feedback_type, user_message, agent_response)


@router.post("/evaluation/callback")
async def evaluation_callback(body: dict):
    decision_id = body.get("decision_id", "")
    eval_score = body.get("eval_score", 0)
    decision_type = body.get("decision_type", "")

    if not decision_id:
        raise HTTPException(status_code=422, detail="decision_id必填")

    return handle_evaluation_feedback(decision_id, float(eval_score), decision_type)


@router.get("/response/{user_id}")
async def get_pending_response(user_id: str):
    resp = _pending_responses.pop(user_id, None)
    if not resp:
        return {"status": "no_response"}
    return resp["result"]


@router.get("/debug")
async def get_debug_log():
    return {"entries": _debug_log[-30:], "total": len(_debug_log)}


@router.get("/agent/scores")
async def get_agent_scores():
    from app.synapse.feedback_loop import get_all_agent_scores
    return get_all_agent_scores()


@router.post("/sync/patterns")
async def manual_sync():
    from app.synapse.pattern_bridge import full_sync
    return full_sync()


@router.get("/agents")
async def list_agents():
    from app.synapse.agent_manager import load_agents
    agents = load_agents()
    return {"agents": agents, "total": len(agents)}


@router.post("/debate")
async def trigger_debate(body: dict):
    question = body.get("question", "")
    if not question:
        raise HTTPException(status_code=422, detail="question必填")
    from app.synapse.convener import debate
    return debate(question)


@router.post("/research")
async def trigger_research(body: dict):
    domain = body.get("domain", "")
    if not domain:
        raise HTTPException(status_code=422, detail="domain必填")
    from app.synapse.domain_researcher import research_and_expand_knowledge
    return research_and_expand_knowledge(domain, body.get("query", ""))