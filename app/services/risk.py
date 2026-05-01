"""
Phase 2 — Climate Risk Scorer
─────────────────────────────
Called automatically when a policy is created.
Pulls real weather from Open-Meteo, samples synthetic raster proxies
for NDVI and flood hazard, then runs XGBoost to produce risk_score (0-1).

Swap the synthetic raster calls with actual GeoTIFF reads (rasterio)
when you have real hazard layers.
"""
import numpy as np
import httpx
import logging
from app.config import settings

logger = logging.getLogger(__name__)

# ── ML model ─────────────────────────────────────────────────────────────────
# Trained once at startup on synthetic data.
# Replace with joblib.load("models/risk_model.pkl") for a trained artifact.
import xgboost as xgb

_rng = np.random.default_rng(42)
_X_train = _rng.random((500, 5))    # [temp, precip, wind, ndvi, flood_haz]
_y_train = (
    _X_train[:, 1] * 0.4            # precip weight
    + _X_train[:, 4] * 0.35         # flood hazard weight
    + _X_train[:, 2] * 0.15         # wind weight
    + _rng.random(500) * 0.1
).clip(0, 1)

_risk_model = xgb.XGBRegressor(
    max_depth=3, learning_rate=0.05, n_estimators=50,
    objective="reg:squarederror", random_state=42
)
_risk_model.fit(_X_train, _y_train)


# ── Raster proxies ────────────────────────────────────────────────────────────
def _sample_ndvi(lat: float, lon: float) -> float:
    """
    Synthetic NDVI proxy (0=bare/urban, 1=dense vegetation).
    Replace with rasterio.open("data/ndvi.tif").read() + row/col lookup.
    """
    seed = int(abs(lat * 1000 + lon * 100)) % 9973
    rng = np.random.default_rng(seed)
    return float(np.clip(rng.random(), 0, 1))


def _sample_flood_hazard(lat: float, lon: float) -> float:
    """
    Synthetic flood hazard score (0=low, 1=high risk zone).
    Replace with actual GSI/JAXA flood raster lookup.
    """
    seed = (int(abs(lat * 1000 + lon * 100)) % 9973) + 4999  # different seed
    rng = np.random.default_rng(seed)
    return float(np.clip(rng.random(), 0, 1))


# ── Open-Meteo fetch ─────────────────────────────────────────────────────────
async def _fetch_weather(lat: float, lon: float) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,precipitation,windspeed_10m",
        "forecast_days": 1,
    }
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(settings.OPEN_METEO_URL, params=params)
            r.raise_for_status()
            hourly = r.json()["hourly"]
            return {
                "temp":   float(np.nanmean(hourly["temperature_2m"])),
                "precip": float(np.nansum(hourly["precipitation"])),
                "wind":   float(np.nanmean(hourly["windspeed_10m"])),
            }
    except Exception as e:
        logger.warning(f"Open-Meteo fetch failed ({e}), using fallback weather.")
        return {"temp": 15.0, "precip": 2.0, "wind": 10.0}


# ── Public interface ──────────────────────────────────────────────────────────
async def compute_policy_risk(lat: float, lon: float) -> dict:
    """
    Returns a dict with risk_score and all intermediate values.
    Stored on the Policy row so the frontend just shows a number.
    """
    weather = await _fetch_weather(lat, lon)
    ndvi = _sample_ndvi(lat, lon)
    flood_haz = _sample_flood_hazard(lat, lon)

    features = np.array([[
        weather["temp"],
        weather["precip"],
        weather["wind"],
        ndvi,
        flood_haz,
    ]])
    risk_score = float(np.clip(_risk_model.predict(features)[0], 0.0, 1.0))

    return {
        "risk_score": round(risk_score, 4),
        "weather": weather,
        "ndvi": round(ndvi, 4),
        "flood_hazard": round(flood_haz, 4),
    }
