# instech-ai

### Climate-linked Premium Calculator · Claim Fraud Detection · Property Exposure Map

**Live demo:** [instech-ai-dashboard.onrender.com](https://instech-ai-dashboard.onrender.com)
&nbsp;|&nbsp;
**API docs:** [instech-ai-api.onrender.com/docs](https://instech-ai-api.onrender.com/docs)

---

## What is this?

Most insurance software is a database with a form in front of it. A customer fills in their address, picks a coverage amount, and a human underwriter somewhere decides on the premium often using a spreadsheet built in 2003.

**instech-ai** is an attempt to show what that pipeline looks like when you replace the spreadsheet with real geospatial intelligence.

It is a full-stack insurance policy and claims platform where every policy creation silently triggers a chain of ML inference: real weather is fetched from Open-Meteo, real elevation is pulled from SRTM 90m satellite data, a trained XGBoost model combines them into a risk score, and that score is written back to the database before the API even responds. The frontend just shows a number. Nobody needs to know how it got there.

---

## Why does this matter?

Climate risk is the defining problem of the next 30 years of insurance. The industry's exposure to floods, wildfires, and extreme precipitation events is accelerating faster than traditional actuarial tables can adapt. Companies like Munich Re, Swiss Re, and every serious InsurTech are racing to build exactly this: systems that price risk dynamically using real-world environmental signals rather than static postal-code lookup tables.

This project is a working demonstration of that architecture — built in Python, deployable in a single `docker compose up`, and transparent enough to understand line by line.

There are four layers:

---

## Phase 1 — The Foundation

A clean REST API built on **FastAPI** with a real **PostgreSQL** database. Three tables: `customers`, `policies`, `claims`. Proper foreign keys, cascade deletes, async SQLAlchemy sessions, and Pydantic validation on every endpoint.

This is table stakes. But everything else is built on top of it — `risk_score`, `fraud_probability`, `risk_flags`, and `trigger_status` are all just columns that get written as the ML layers run.

---

## Phase 2 — Climate-linked Premium Calculator

The moment a policy is created with a latitude and longitude, the backend:

1. Calls **Open-Meteo** (free, no API key) for real current temperature, precipitation, and wind at that coordinate
2. Samples a flood hazard raster for the location — ready to swap for actual **GSI** or **JAXA** flood zone data
3. Feeds both into a trained **XGBoost regressor** with geophysically-motivated feature weights
4. Writes the `risk_score` back to the `Policy` row before the API responds

A property in coastal Chennai at 6m elevation during monsoon season gets a very different score than a property on the Deccan Plateau at 600m. The premium follows the risk — not a spreadsheet from 2003.

---

## Phase 3 — Claim Fraud Detection

Insurance fraud costs the Indian industry an estimated ₹45,000 crore annually. When a claim is filed, a single endpoint runs two layers of detection:

**Business-logic flags** — five deterministic rules from insurance domain knowledge:
- `late_night_submission` — claims filed between 23:00–04:00 are statistically anomalous
- `high_amount_relative_to_premium` — claim > 3× annual premium
- `new_policy` — policy less than 30 days old (a classic fraud pattern)
- `rapid_repeat_claim` — another claim on the same policy within 60 days
- `amount_near_sum_insured_limit` — claim ≥ 90% of sum insured

**Statistical anomaly detection** — an **IsolationForest** trained on claim feature distributions catches outliers that rule-based systems miss.

Both signals are blended into a single `fraud_probability` (0–1) with a `clear / review / flag` decision. Results are written back to the Claim row and shown as colour-coded badges in the dashboard.

---

## Phase 4 — Parametric CAT Trigger

This is the PhD angle — and the thing that makes this genuinely different from anything else in this space.

**Parametric insurance** pays out when a physical event crosses a measurable threshold, rather than after a loss assessment. It's how catastrophe bonds work. It's what Munich Re and Swiss Re are building for climate-exposed assets globally.

The `/claims/auto-trigger` endpoint:

1. Fetches **real 7-day precipitation** from Open-Meteo's forecast API
2. Fetches **real 30-day precipitation baseline** from Open-Meteo's historical archive — a proxy for soil saturation
3. Fetches **real elevation** from **OpenTopoData SRTM 90m** — the same satellite dataset used in academic flood modelling
4. Combines them: `score = 0.45 × precip_7d + 0.30 × elevation_risk + 0.25 × precip_30d`
5. Returns `triggered: true` if the score crosses the configurable threshold (default 0.75)

No synthetic data. No random seeds. Real API calls, real geophysical reasoning.

Try it with Patna (`25.61°N, 85.12°E`) during monsoon season.

---

## Stack

```
Backend     FastAPI · SQLAlchemy (async) · PostgreSQL · Gunicorn + Uvicorn
ML          XGBoost · scikit-learn IsolationForest · NumPy · Pandas
Geospatial  Rasterio · GeoPandas · Shapely
Data        Open-Meteo API · OpenTopoData SRTM 90m
Frontend    Streamlit · Folium · CartoDB dark_matter tiles
Theme       Navy #0a1628 · Gold #c9a84c · JetBrains Mono
Infra       Docker · docker-compose · Neon PostgreSQL · Render
```

---

## Run locally

```bash
git clone https://github.com/YOUR_USERNAME/instech-ai
cd instech-ai
copy .env.example .env           # Windows
# cp .env.example .env           # Mac/Linux
docker compose up --build -d
# wait ~60 seconds for startup
python seed.py                   # populate with Indian data
```

- Dashboard → `http://localhost:8501`
- API / Swagger → `http://localhost:8000/docs`

---

## Project structure

```
instech-ai/
├── app/
│   ├── main.py              # FastAPI app + lifespan
│   ├── config.py            # pydantic-settings
│   ├── database.py          # async SQLAlchemy engine
│   ├── models/              # ORM: Customer, Policy, Claim
│   ├── schemas/             # Pydantic I/O schemas
│   ├── routers/             # CRUD + ML endpoints
│   └── services/
│       ├── risk.py          # Phase 2 — XGBoost risk scorer
│       ├── fraud.py         # Phase 3 — fraud detection
│       └── parametric.py    # Phase 4 — parametric CAT trigger
├── dashboard/
│   └── app.py               # Streamlit UI (navy + gold)
├── seed.py                  # Realistic Indian insurance seed data
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Key endpoints

| Method | Endpoint | What it does |
|--------|----------|--------------|
| `POST` | `/policies/` | Create policy → **auto-scores risk (Phase 2)** |
| `POST` | `/policies/{id}/risk-update` | Re-score on demand |
| `POST` | `/claims/{id}/fraud-check` | **Phase 3** fraud detection → writes result to DB |
| `GET`  | `/claims/auto-trigger?lat=&lon=&event_type=` | **Phase 4** parametric trigger with real satellite + weather data |
| `GET`  | `/health` | API health check |

---

## Background

This project was built as part of a geospatial AI portfolio targeting Earth observation and InsurTech roles. The author holds a PhD in Remote Sensing and GIS from IIT Mandi, with research focused on cryospheric hazard mapping in the Northwestern Himalayas using SAR/InSAR, DGPS, and drone photogrammetry.

---

*Python · FastAPI · PostgreSQL · XGBoost · Open-Meteo · OpenTopoData SRTM*
*Deployed on Render + Neon · Built for the climate risk era*