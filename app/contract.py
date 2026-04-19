from app.config import VALID_DECISION_TYPES, VALID_RISK_LEVELS
from app.models import Decision


class ContractError(Exception):
    pass


def validate_decision(decision: Decision) -> bool:
    if not decision.problem.strip():
        raise ContractError("problem 不能为空")

    if not decision.decision.strip():
        raise ContractError("decision 不能为空")

    if not decision.actions or not all(a.strip() for a in decision.actions):
        raise ContractError("actions 不能为空且每条不能为空字符串")

    if not decision.expected_impact.strip():
        raise ContractError("expected_impact 不能为空")

    if not (0.0 <= decision.confidence <= 1.0):
        raise ContractError(
            f"confidence 须在 [0,1] 范围内，当前值: {decision.confidence}"
        )

    if decision.risk_level not in VALID_RISK_LEVELS:
        raise ContractError(
            f"risk_level 须为 {VALID_RISK_LEVELS}，当前值: {decision.risk_level}"
        )

    if decision.decision_type not in VALID_DECISION_TYPES:
        raise ContractError(
            f"decision_type 须为 {VALID_DECISION_TYPES}，当前值: {decision.decision_type}"
        )

    if not (decision.reasoning or "").strip():
        raise ContractError("reasoning 不能为空，必须说明决策依据")

    return True
