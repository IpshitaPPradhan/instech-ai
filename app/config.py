from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://instech:instech@db:5432/instech"
    SECRET_KEY: str = "change-this-in-production-use-openssl-rand-hex-32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    OPEN_METEO_URL: str = "https://api.open-meteo.com/v1/forecast"

    # Flood trigger threshold (Phase 4) — fraction 0-1
    FLOOD_TRIGGER_THRESHOLD: float = 0.75

    class Config:
        env_file = ".env"


settings = Settings()
