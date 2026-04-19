import json
import re
import time

import requests

from app.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

_TIMEOUT = 120
_MAX_RETRIES = 3


def call_llm(prompt: str, model: str = DEEPSEEK_MODEL) -> str:
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 2048,
    }
    for attempt in range(_MAX_RETRIES):
        try:
            resp = requests.post(
                DEEPSEEK_BASE_URL,
                headers=headers,
                json=payload,
                timeout=_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except (
            requests.exceptions.HTTPError,
            requests.exceptions.ConnectionError,
            KeyError,
        ) as e:
            if attempt < _MAX_RETRIES - 1:
                time.sleep(3 * (attempt + 1))
            else:
                raise


def extract_json(text: str) -> dict:
    fences = re.findall(r"```(?:json)?\s*([\s\S]*?)```", text)
    for block in fences:
        try:
            return json.loads(block.strip())
        except json.JSONDecodeError:
            continue

    brace_match = re.search(r"\{[\s\S]*\}", text)
    if brace_match:
        try:
            return json.loads(brace_match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"无法从 LLM 输出中提取 JSON:\n{text[:500]}")
