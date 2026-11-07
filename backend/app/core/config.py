from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg://nexus_user:nexus_pass@localhost:5432/nexus_db"
    SECRET_KEY: str = "change-this-to-a-64-char-random-string-before-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14
    FRONTEND_URL: str = "http://localhost:5173"
    EMAIL_PROVIDER: str = ""
    EMAIL_API_KEY: str = ""
    EMAIL_FROM: str = ""
    LLM_PROVIDER: str = ""
    LLM_API_KEY: str = ""
    GOOGLE_MAPS_SERVER_KEY: str = ""
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ENVIRONMENT: str = "development"
    BACKEND_CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 20
    YOLO_MODEL_PATH: str = "./models/yolov8n_infrastructure.pt"
    SEVERITY_MODEL_PATH: str = "./models/severity_xgb.pkl"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.BACKEND_CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
