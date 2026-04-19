from app.config import (
    LOW_CONFIDENCE_THRESHOLD,
    REVIEW_CONFIDENCE_THRESHOLD,
)


def calibrate_confidence(decision) -> float:
    c = decision.confidence

    if decision.risk_level == "high":
        c -= 0.1

    if decision.decision_type == "pricing":
        c -= 0.05

    if decision.decision_type == "menu":
        c -= 0.05

    return max(0.0, min(1.0, c))


def assign_status(confidence: float) -> str:
    if confidence >= LOW_CONFIDENCE_THRESHOLD:
        return "approved"
    elif confidence >= REVIEW_CONFIDENCE_THRESHOLD:
        return "review"
    else:
        return "rejected"
