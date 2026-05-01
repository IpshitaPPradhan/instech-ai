from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, Literal


PolicyType = Literal["home", "flood", "fire", "auto"]
PolicyStatus = Literal["active", "expired", "cancelled"]
TriggerStatus = Literal["none", "pending", "triggered", "denied"]


class PolicyCreate(BaseModel):
    customer_id: int
    address: str
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    policy_type: PolicyType
    sum_insured: float = Field(..., gt=0)
    premium: float = Field(..., gt=0)
    start_date: date
    end_date: date


class PolicyUpdate(BaseModel):
    address: Optional[str] = None
    sum_insured: Optional[float] = None
    premium: Optional[float] = None
    status: Optional[PolicyStatus] = None


class PolicyOut(BaseModel):
    id: int
    customer_id: int
    address: str
    lat: float
    lon: float
    policy_type: str
    sum_insured: float
    premium: float
    risk_score: Optional[float]          # Phase 2
    trigger_status: str                  # Phase 4
    status: str
    start_date: date
    end_date: date
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class RiskUpdateOut(BaseModel):
    policy_id: int
    risk_score: float
    weather: dict
    ndvi: float
    flood_hazard: float
