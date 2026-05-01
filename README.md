# instech-ai

ML-powered insurance policy & claims platform.

## Stack
- **FastAPI** + **SQLAlchemy async** + **PostgreSQL** — real database, real persistence
- **Phase 2** — XGBoost risk scorer (Open-Meteo weather + flood raster) fires on policy creation
- **Phase 3** — IsolationForest + business-logic fraud detection with named flags
- **Phase 4** — Parametric CAT trigger (real precipitation from Open-Meteo + hazard zone)
- **Streamlit** dashboard — navy + gold, monospace, dark-first

## Run

```bash
cp .env.example .env
docker compose up --build
```

- API + Swagger: http://localhost:8000/docs
- Dashboard:     http://localhost:8501

## Project structure

```
app/
├── main.py              # FastAPI app factory
├── config.py            # pydantic-settings
├── database.py          # async SQLAlchemy engine
├── models/              # ORM: Customer, Policy, Claim
├── schemas/             # Pydantic I/O schemas
├── routers/             # CRUD + ML endpoints
└── services/
    ├── risk.py          # Phase 2 — risk scorer
    ├── fraud.py         # Phase 3 — fraud detection
    └── parametric.py    # Phase 4 — CAT trigger
dashboard/
└── app.py               # Streamlit UI
```

## Key endpoints

| Method | Path | What it does |
|--------|------|-------------|
| POST | /policies/ | Create policy → auto-runs risk scorer |
| POST | /policies/{id}/risk-update | Re-score existing policy |
| POST | /claims/{id}/fraud-check | Run fraud detection, write results to DB |
| GET  | /claims/auto-trigger | Parametric event evaluation |
