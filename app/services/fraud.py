"""
Phase 3 — Fraud Detection Service
───────────────────────────────────
Two-layer detection:
  1. Business-logic flags — deterministic rules from insurance domain knowledge.
  2. IsolationForest anomaly score — statistical outlier among claims.

Both are combined into a final fraud_probability (0-1).
The decision label: clear / review / flag maps to UI badge colour.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

# ── Train IsolationForest on startup ─────────────────────────────────────────
# Features: [amount_normalised, claim_age_days, policy_age_days, hour_of_day]
_rng = np.random.default_rng(0)
_iso_train = _rng.random((400, 4))
_iso_train[:20] = _rng.random((20, 4)) * [5, 0.1, 0.05, 1]  # inject outliers
_iso = IsolationForest(n_estimators=100, contamination=0.05, random_state=0)
_iso.fit(_iso_train)


# ── Business-logic flags ──────────────────────────────────────────────────────
def _compute_flags(
    claim_amount: float,
    annual_premium: float,
    sum_insured: float,
    policy_created_at: datetime,
    claim_created_at: datetime,
    previous_claim_dates: list[datetime],
) -> list[str]:
    flags = []
    now = claim_created_at

    # 1. Late night submission (23:00–04:00 local)
    if now.hour >= 23 or now.hour <= 4:
        flags.append("late_night_submission")

    # 2. Claim amount > 3× annual premium (major red flag in non-life insurance)
    if annual_premium > 0 and claim_amount > annual_premium * 3:
        flags.append("high_amount_relative_to_premium")

    # 3. Policy less than 30 days old ("new policy" fraud)
    policy_age = (now - policy_created_at.replace(tzinfo=timezone.utc)).days
    if policy_age < 30:
        flags.append("new_policy")

    # 4. Rapid repeat claim — another claim within 60 days
    for prev in previous_claim_dates:
        if abs((now - prev.replace(tzinfo=timezone.utc)).days) < 60:
            flags.append("rapid_repeat_claim")
            break

    # 5. Claim amount is ≥ 90% of sum insured (suspiciously precise)
    if sum_insured > 0 and claim_amount >= sum_insured * 0.9:
        flags.append("amount_near_sum_insured_limit")

    return flags


# ── Anomaly score ─────────────────────────────────────────────────────────────
def _anomaly_probability(
    claim_amount: float,
    sum_insured: float,
    policy_age_days: int,
    claim_hour: int,
) -> float:
    amount_norm = claim_amount / max(sum_insured, 1)
    features = np.array([[
        amount_norm,
        min(policy_age_days, 365) / 365,
        min(policy_age_days, 365) / 365,
        claim_hour / 24,
    ]])
    raw = _iso.decision_function(features)[0]
    # decision_function: negative = more anomalous. Map to [0,1].
    prob = 1 / (1 + np.exp(raw * 4))
    return float(np.clip(prob, 0, 1))


# ── Decision label ────────────────────────────────────────────────────────────
def _decision(fraud_prob: float, n_flags: int) -> str:
    if fraud_prob > 0.70 or n_flags >= 3:
        return "flag"
    if fraud_prob > 0.40 or n_flags >= 1:
        return "review"
    return "clear"


# ── Public interface ──────────────────────────────────────────────────────────
def run_fraud_check(
    claim_amount: float,
    claim_created_at: datetime,
    annual_premium: float,
    sum_insured: float,
    policy_created_at: datetime,
    previous_claim_dates: list[datetime],
) -> dict:
    """
    Returns fraud_probability, risk_flags, decision.
    All values are written back to the Claim row.
    """
    flags = _compute_flags(
        claim_amount=claim_amount,
        annual_premium=annual_premium,
        sum_insured=sum_insured,
        policy_created_at=policy_created_at,
        claim_created_at=claim_created_at,
        previous_claim_dates=previous_claim_dates,
    )

    policy_age_days = max(0, (claim_created_at - policy_created_at.replace(tzinfo=timezone.utc)).days)
    anomaly_prob = _anomaly_probability(
        claim_amount=claim_amount,
        sum_insured=sum_insured,
        policy_age_days=policy_age_days,
        claim_hour=claim_created_at.hour,
    )

    # Blend: 60% anomaly model, 40% flag count signal
    flag_signal = min(len(flags) / 4, 1.0)
    fraud_prob = round(0.60 * anomaly_prob + 0.40 * flag_signal, 4)

    return {
        "fraud_probability": fraud_prob,
        "risk_flags": flags,
        "decision": _decision(fraud_prob, len(flags)),
    }
