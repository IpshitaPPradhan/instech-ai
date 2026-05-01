from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.policy import Policy
from app.models.customer import Customer
from app.schemas.policy import PolicyCreate, PolicyUpdate, PolicyOut, RiskUpdateOut
from app.services.risk import compute_policy_risk
from typing import List

router = APIRouter(prefix="/policies", tags=["policies"])


@router.post("/", response_model=PolicyOut, status_code=status.HTTP_201_CREATED)
async def create_policy(body: PolicyCreate, db: AsyncSession = Depends(get_db)):
    # Validate customer exists
    cust = await db.execute(select(Customer).where(Customer.id == body.customer_id))
    if not cust.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Customer not found.")

    policy = Policy(**body.model_dump())
    db.add(policy)
    await db.flush()  # get the ID

    # ── Phase 2: compute risk score immediately on creation ──────────────────
    risk_data = await compute_policy_risk(body.lat, body.lon)
    policy.risk_score = risk_data["risk_score"]
    # ────────────────────────────────────────────────────────────────────────

    await db.flush()
    await db.refresh(policy)
    return policy


@router.get("/", response_model=List[PolicyOut])
async def list_policies(
    skip: int = 0, limit: int = 50,
    customer_id: int = None,
    db: AsyncSession = Depends(get_db)
):
    q = select(Policy)
    if customer_id:
        q = q.where(Policy.customer_id == customer_id)
    result = await db.execute(q.offset(skip).limit(limit))
    return result.scalars().all()


@router.get("/{policy_id}", response_model=PolicyOut)
async def get_policy(policy_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Policy).where(Policy.id == policy_id))
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found.")
    return policy


@router.patch("/{policy_id}", response_model=PolicyOut)
async def update_policy(policy_id: int, body: PolicyUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Policy).where(Policy.id == policy_id))
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found.")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(policy, field, value)
    await db.flush()
    await db.refresh(policy)
    return policy


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(policy_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Policy).where(Policy.id == policy_id))
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found.")
    await db.delete(policy)


@router.post("/{policy_id}/risk-update", response_model=RiskUpdateOut, tags=["ml"])
async def refresh_risk_score(policy_id: int, db: AsyncSession = Depends(get_db)):
    """
    Phase 2 — manually re-trigger risk scoring for an existing policy.
    Useful when weather conditions change or as a cron job.
    """
    result = await db.execute(select(Policy).where(Policy.id == policy_id))
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found.")

    risk_data = await compute_policy_risk(policy.lat, policy.lon)
    policy.risk_score = risk_data["risk_score"]
    await db.flush()

    return RiskUpdateOut(
        policy_id=policy_id,
        risk_score=risk_data["risk_score"],
        weather=risk_data["weather"],
        ndvi=risk_data["ndvi"],
        flood_hazard=risk_data["flood_hazard"],
    )
