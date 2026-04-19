import json
import os

PATH = "data/system_params.json"

DEFAULT_PARAMS = {
    "risk_penalty": 0.2,
    "revenue_factor": 1.0,
    "profit_factor": 1.0,
    "turnover_factor": 1.0,
    "explore_rate": 0.15,
    "confidence_threshold": 0.7,
    "pattern_match_threshold": 0.6,
}


def load_params() -> dict:
    os.makedirs("data", exist_ok=True)
    try:
        with open(PATH, "r") as f:
            return json.load(f)
    except:
        return DEFAULT_PARAMS.copy()


def save_params(params: dict) -> None:
    os.makedirs("data", exist_ok=True)
    with open(PATH, "w") as f:
        json.dump(params, f, indent=2, ensure_ascii=False)


def get_param(key: str, default=None):
    params = load_params()
    return params.get(key, default)


def set_param(key: str, value) -> dict:
    params = load_params()
    params[key] = value
    save_params(params)
    return params


def reset_params() -> dict:
    save_params(DEFAULT_PARAMS.copy())
    return DEFAULT_PARAMS.copy()


def get_all_params() -> dict:
    return load_params()


def init_params():
    if not os.path.exists(PATH):
        save_params(DEFAULT_PARAMS.copy())
