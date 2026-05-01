from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.database import engine, Base
from app.models import Customer, Policy, Claim
from app.routers.customers import router as customers_router
from app.routers.policies import router as policies_router
from app.routers.claims import router as claims_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        # Advisory lock prevents two workers running create_all simultaneously
        await conn.execute(text("SELECT pg_advisory_lock(12345)"))
        try:
            await conn.run_sync(lambda c: Base.metadata.create_all(c, checkfirst=True))
        finally:
            await conn.execute(text("SELECT pg_advisory_unlock(12345)"))
    yield
    await engine.dispose()


app = FastAPI(
    title="Instech-AI",
    description=(
        "Insurance policy & claims management with ML-powered risk scoring, "
        "fraud detection, and parametric CAT trigger."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(customers_router)
app.include_router(policies_router)
app.include_router(claims_router)


@app.get("/health", tags=["infra"])
async def health():
    return {"status": "ok"}