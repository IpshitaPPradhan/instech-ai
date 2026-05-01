from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from app.database import Base


class Claim(Base):
    """
    Claims table.
    fraud_probability (Phase 3) — written by /fraud-check endpoint.
    risk_flags        (Phase 3) — JSON list of flag strings, e.g.
                                  ["late_night_submission", "high_amount_relative_to_premium"]
    status            (Phase 4) — can be set to "auto_triggered" by parametric endpoint.
    """
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("policies.id", ondelete="CASCADE"), nullable=False, index=True)

    claim_type = Column(String(50), nullable=False)    # flood | fire | theft | accident | other
    description = Column(String(2000), nullable=True)
    amount_requested = Column(Float, nullable=False)

    # Phase 3 — populated by POST /claims/{id}/fraud-check
    fraud_probability = Column(Float, nullable=True)
    risk_flags = Column(JSON, nullable=True)            # list[str]

    # pending | approved | denied | auto_triggered
    status = Column(String(30), nullable=False, default="pending")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    policy = relationship("Policy", back_populates="claims")
