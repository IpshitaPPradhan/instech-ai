from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.claim import Claim
from app.models.policy import Policy
from app.schemas.claim import ClaimCreate, ClaimUpdate, ClaimOut, FraudCheckOut, AutoTriggerOut
from app.services.fraud import run_fraud_check
from app.services.parametric import evaluate_parametric_trigger
from datetime import datetime, timezone
from typing import List

router = APIRouter(prefix="/claims", tags=["claims"])


@router.post("/", response_model=ClaimOut, status_code=status.HTTP_201_CREATED)
async def create_claim(body: ClaimCreate, db: AsyncSession = Depends(get_db)):
    pol = await db.execute(select(Policy).where(Policy.id == body.policy_id))
    if not pol.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Policy not found.")
    claim = Claim(**body.model_dump())
    db.add(claim)
    await db.flush()
    await db.refresh(claim)
    return claim


@router.get("/", response_model=List[ClaimOut])
async def list_claims(
    skip: int = 0, limit: int = 50,
    policy_id: int = None,
    db: AsyncSession = Depends(get_db)
):
    q = select(Claim)
    if policy_id:
        q = q.where(Claim.policy_id == policy_id)
    result = await db.execute(q.offset(skip).limit(limit))
    return result.scalars().all()


@router.get("/auto-trigger", response_model=AutoTriggerOut, tags=["ml"])
async def auto_trigger(lat: float, lon: float, event_type: str = "flood"):
    """
    Phase 4 — Parametric trigger check.
    Does NOT require an existing claim. Pass coordinates and event type;
    returns whether a qualifying event has occurred (automatic payout eligible).
    """
    result = await evaluate_parametric_trigger(lat, lon, event_type)
    return AutoTriggerOut(**result)


@router.get("/{claim_id}", response_model=ClaimOut)
async def get_claim(claim_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Claim).where(Claim.id == claim_id))
    claim = result.scalar_one_or_none()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found.")
    return claim


@router.patch("/{claim_id}", response_model=ClaimOut)
async def update_claim(claim_id: int, body: ClaimUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Claim).where(Claim.id == claim_id))
    claim = result.scalar_one_or_none()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found.")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(claim, field, value)
    await db.flush()
    await db.refresh(claim)
    return claim


@router.delete("/{claim_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_claim(claim_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Claim).where(Claim.id == claim_id))
    claim = result.scalar_one_or_none()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found.")
    await db.delete(claim)


@router.post("/{claim_id}/fraud-check", response_model=FraudCheckOut, tags=["ml"])
async def fraud_check(claim_id: int, db: AsyncSession = Depends(get_db)):
    """
    Phase 3 — Run fraud detection on a claim.
    Writes fraud_probability and risk_flags back to the Claim row.
    Returns decision: clear | review | flag.
    """
    result = await db.execute(select(Claim).where(Claim.id == claim_id))
    claim = result.scalar_one_or_none()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found.")

    pol_result = await db.execute(select(Policy).where(Policy.id == claim.policy_id))
    policy = pol_result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Associated policy not found.")

    # Get other claims on the same policy (for repeat-claim flag)
    other_claims_result = await db.execute(
        select(Claim).where(Claim.policy_id == claim.policy_id, Claim.id != claim_id)
    )
    other_claims = other_claims_result.scalars().all()
    prev_dates = [c.created_at for c in other_claims if c.created_at]

    fraud_data = run_fraud_check(
        claim_amount=claim.amount_requested,
        claim_created_at=claim.created_at or datetime.now(timezone.utc),
        annual_premium=policy.premium,
        sum_insured=policy.sum_insured,
        policy_created_at=policy.created_at,
        previous_claim_dates=prev_dates,
    )

    # Write results back to the claim row
    claim.fraud_probability = fraud_data["fraud_probability"]
    claim.risk_flags = fraud_data["risk_flags"]
    await db.flush()

    return FraudCheckOut(
        claim_id=claim_id,
        fraud_probability=fraud_data["fraud_probability"],
        risk_flags=fraud_data["risk_flags"],
        decision=fraud_data["decision"],
    )
