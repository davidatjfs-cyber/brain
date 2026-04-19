import os

GLOBAL_OBJECTIVE = {
    "mode": "balance",
    "weights": {
        "revenue": 0.4,
        "profit": 0.3,
        "turnover": 0.3,
    },
}

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1/chat/completions")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

VALID_DECISION_TYPES = {"marketing", "pricing", "menu", "operation"}
VALID_RISK_LEVELS = {"low", "medium", "high"}
LOW_CONFIDENCE_THRESHOLD = 0.7
REVIEW_CONFIDENCE_THRESHOLD = 0.6
