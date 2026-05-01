"""
Phase 4 — Parametric Auto-Trigger (CAT Bond Logic)
────────────────────────────────────────────────────
Real data sources (no API key required):
  1. Open-Meteo forecast API   — 7-day precipitation sum at coordinate
  2. Open-Meteo historical API — 30-day precipitation baseline (soil saturation proxy)
  3. OpenTopoData SRTM 90m     — elevation at coordinate
                                  low elevation → high flood exposure

Flood score formula:
  flood_score = 0.45 × precip_norm_7d
              + 0.30 × elevation_risk
              + 0.25 × precip_norm_30d_baseline
"""

import asyncio
import numpy as np
import httpx
import logging
from datetime import date, timedelta
from app.config import settings

logger = logging.getLogger(__name__)


# ── 1. Real elevation — OpenTopoData SRTM 90m ────────────────────────────────
async def _fetch_elevation(lat: float, lon: float) -> float:
    """
    Returns elevation in metres above sea level.
    OpenTopoData SRTM 90m: free, no API key, covers all of India.
    """
    url = f"https://api.opentopodata.org/v1/srtm90m?locations={lat},{lon}"
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(url)
            r.raise_for_status()
            elev = r.json()["results"][0]["elevation"]
            return float(elev) if elev is not None else 50.0
    except Exception as e:
        logger.warning(f"OpenTopoData failed ({e}), fallback 50m.")
        return 50.0


def _elevation_to_flood_risk(elevation_m: float) -> float:
    """
    Elevation → flood risk score (0=safe, 1=extreme risk).
      ≤ 5m   → 1.00  coastal / tidal flood plain
      ≤ 15m  → 0.85  low-lying riverine zone
      ≤ 30m  → 0.65  moderate flood exposure
      ≤ 50m  → 0.40  some exposure
      ≤ 100m → 0.20  low exposure
      > 100m → 0.05  hills / plateau
    Linear interpolation between breakpoints.
    """
    breakpoints = [
        (0,    1.00), (5,   1.00), (15,  0.85),
        (30,   0.65), (50,  0.40), (100, 0.20),
        (500,  0.05), (9000, 0.0),
    ]
    for i in range(len(breakpoints) - 1):
        e0, r0 = breakpoints[i]
        e1, r1 = breakpoints[i + 1]
        if e0 <= elevation_m <= e1:
            t = (elevation_m - e0) / (e1 - e0)
            return float(np.clip(r0 + t * (r1 - r0), 0, 1))
    return 0.0


# ── 2. Real 7-day precipitation — Open-Meteo forecast ────────────────────────
async def _fetch_precip_7d(lat: float, lon: float) -> float:
    """Total precipitation (mm) over the past 7 days."""
    params = {
        "latitude":      lat,
        "longitude":     lon,
        "daily":         "precipitation_sum",
        "past_days":     7,
        "forecast_days": 0,
    }
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(settings.OPEN_METEO_URL, params=params)
            r.raise_for_status()
            values = r.json().get("daily", {}).get("precipitation_sum", [])
            return float(np.nansum([v for v in values if v is not None]))
    except Exception as e:
        logger.warning(f"Open-Meteo 7d precip failed ({e}), using 0mm.")
        return 0.0


# ── 3. Real 30-day precipitation baseline — Open-Meteo historical ─────────────
async def _fetch_precip_30d(lat: float, lon: float) -> float:
    """
    Total precipitation (mm) over the past 30 days.
    High 30-day total = saturated soil = higher flood risk from any new rain.
    Uses Open-Meteo historical archive API (free, no key).
    """
    end   = date.today() - timedelta(days=1)
    start = end - timedelta(days=29)
    params = {
        "latitude":   lat,
        "longitude":  lon,
        "start_date": str(start),
        "end_date":   str(end),
        "daily":      "precipitation_sum",
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                "https://archive-api.open-meteo.com/v1/archive",
                params=params,
            )
            r.raise_for_status()
            values = r.json().get("daily", {}).get("precipitation_sum", [])
            return float(np.nansum([v for v in values if v is not None]))
    except Exception as e:
        logger.warning(f"Open-Meteo 30d archive failed ({e}), using 0mm.")
        return 0.0


# ── Public interface ──────────────────────────────────────────────────────────
async def evaluate_parametric_trigger(
    lat: float,
    lon: float,
    event_type: str = "flood",
) -> dict:
    """
    Evaluates whether a parametric flood trigger fires at a coordinate.
    All three API calls run in parallel; each has an independent fallback
    so one failure does not break the evaluation.
    """
    elevation_m, precip_7d, precip_30d = await asyncio.gather(
        _fetch_elevation(lat, lon),
        _fetch_precip_7d(lat, lon),
        _fetch_precip_30d(lat, lon),
    )

    elevation_risk  = _elevation_to_flood_risk(elevation_m)
    precip_norm_7d  = float(np.clip(precip_7d  / 150.0, 0, 1))  # 150mm = extreme 7-day event
    precip_norm_30d = float(np.clip(precip_30d / 600.0, 0, 1))  # 600mm/month = extreme monsoon

    flood_score = round(
        0.45 * precip_norm_7d
      + 0.30 * elevation_risk
      + 0.25 * precip_norm_30d,
        4,
    )

    triggered = flood_score >= settings.FLOOD_TRIGGER_THRESHOLD

    if triggered:
        message = (
            f"Flood trigger CONFIRMED at ({lat:.4f}°N, {lon:.4f}°E). "
            f"Elevation: {elevation_m:.0f}m asl · "
            f"7-day rain: {precip_7d:.1f}mm · "
            f"30-day baseline: {precip_30d:.0f}mm. "
            f"Automatic payout eligible."
        )
    else:
        message = (
            f"No qualifying event at ({lat:.4f}°N, {lon:.4f}°E). "
            f"Composite score {flood_score:.4f} below threshold "
            f"{settings.FLOOD_TRIGGER_THRESHOLD}. "
            f"Elevation: {elevation_m:.0f}m · "
            f"7-day rain: {precip_7d:.1f}mm · "
            f"30-day baseline: {precip_30d:.0f}mm."
        )

    return {
        "lat":               lat,
        "lon":               lon,
        "event_type":        event_type,
        "elevation_m":       round(elevation_m, 1),
        "elevation_risk":    round(elevation_risk, 4),
        "total_precip_mm":   round(precip_7d, 2),
        "precip_30d_mm":     round(precip_30d, 2),
        "hazard_zone_score": round(elevation_risk, 4),  # kept for schema compatibility
        "flood_score":       flood_score,
        "triggered":         triggered,
        "message":           message,
    }