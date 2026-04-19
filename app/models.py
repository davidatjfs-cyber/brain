from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import uuid
import time


class StoreInput(BaseModel):
    store_id: str
    date: str
    metrics: Dict[str, float]
    menu: List[Dict]
    feedback: List[Dict]
    scenario: Optional[str] = ""


class Decision(BaseModel):
    decision_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    problem: str
    decision: str
    actions: List[str]
    expected_impact: str
    risk_level: str
    confidence: float
    decision_type: str
    decision_status: str = "pending"
    reasoning: Optional[str] = ""
    used_pattern_ids: List[str] = Field(default_factory=list)


class EvaluationResult(BaseModel):
    score: float
    metrics: Dict[str, float]
    final_judgement: str
    comment: Optional[str] = ""


class DecisionRecord(BaseModel):
    input: StoreInput
    decision: Decision
    evaluation: Optional[EvaluationResult] = None
    timestamp: float = Field(default_factory=lambda: time.time())
