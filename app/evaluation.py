from app.config import GLOBAL_OBJECTIVE


def evaluate(metrics: dict) -> dict:
    w = GLOBAL_OBJECTIVE["weights"]

    score = (
        metrics.get("revenue_change", 0.0) * w["revenue"]
        + metrics.get("profit_change", 0.0) * w["profit"]
        + metrics.get("turnover_change", 0.0) * w["turnover"]
    )

    if score > 0.05:
        judgement = "positive"
    elif score < -0.05:
        judgement = "negative"
    else:
        judgement = "neutral"

    return {
        "score": round(score, 4),
        "metrics": metrics,
        "final_judgement": judgement,
    }
