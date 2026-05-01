from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal, List


ClaimType = Literal["flood", "fire", "theft", "accident", "other"]
ClaimStatus = Literal["pending", "approved", "denied", "auto_triggered"]


class ClaimCreate(BaseModel):
    policy_id: int
    claim_type: ClaimType
    description: Optional[str] = None
    amount_requested: float = Field(..., gt=0)


class ClaimUpdate(BaseModel):
    status: Optional[ClaimStatus] = None
    description: Optional[str] = None


class ClaimOut(BaseModel):
    id: int
    policy_id: int
    claim_type: str
    description: Optional[str]
    amount_requested: float
    fraud_probability: Optional[float]   # Phase 3
    risk_flags: Optional[List[str]]      # Phase 3
    status: str
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class FraudCheckOut(BaseModel):
    claim_id: int
    fraud_probability: float
    risk_flags: List[str]
    decision: Literal["clear", "review", "flag"]


class AutoTriggerOut(BaseModel):
    lat: float
    lon: float
    event_type: str
    flood_score: float
    triggered: bool
    message: str
