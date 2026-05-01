from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, func, Date
)
from sqlalchemy.orm import relationship
from app.database import Base


class Policy(Base):
    """
    Core policy table.
    risk_score (Phase 2)    — written automatically when policy is created.
    trigger_status (Phase 4)— updated by the parametric auto-trigger endpoint.
    """
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)

    address = Column(String(500), nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)

    policy_type = Column(String(50), nullable=False)   # home | flood | fire | auto
    sum_insured = Column(Float, nullable=False)
    premium = Column(Float, nullable=False)             # annual premium

    # Phase 2 — populated on creation by the risk service
    risk_score = Column(Float, nullable=True)

    # Phase 4 — none | pending | triggered | denied
    trigger_status = Column(String(20), nullable=False, default="none")

    status = Column(String(20), nullable=False, default="active")   # active | expired | cancelled
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    customer = relationship("Customer", back_populates="policies")
    claims = relationship("Claim", back_populates="policy", lazy="selectin")
