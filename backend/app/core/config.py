"""
Application settings loaded from environment variables / .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/factory_db"
    DB_ECHO: bool = False

    # ── JWT / Security ────────────────────────────────────────────────────────
    SECRET_KEY: str = "change-me-in-production"
    REFRESH_SECRET_KEY: str = "change-me-refresh-secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Password Hashing ─────────────────────────────────────────────────────
    ARGON2_TIME_COST: int = 2
    ARGON2_MEMORY_COST: int = 65536
    ARGON2_PARALLELISM: int = 2

    # ── File Storage ──────────────────────────────────────────────────────────
    UPLOAD_DIR: str = "uploads/documents"
    MAX_UPLOAD_SIZE_MB: int = 20
    ALLOWED_EXTENSIONS: list[str] = ["pdf", "docx", "xlsx", "pptx", "txt"]
    STORAGE_BACKEND: str = "local"   # "local" | "s3"

    # ── S3 / Object Storage (only if STORAGE_BACKEND=s3) ─────────────────────
    AWS_BUCKET: str = ""
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY: str = ""
    AWS_SECRET_KEY: str = ""

    # ── App ───────────────────────────────────────────────────────────────────
    APP_NAME: str = "Factory Management System"
    DEBUG: bool = False
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]
    TRUSTED_HOSTS: list[str] = ["*"]

    def __init__(self, **values):
        super().__init__(**values)
        import os
        if "VERCEL" in os.environ:
            self.UPLOAD_DIR = "/tmp/uploads/documents"

        # Ensure database URL is asyncpg compatible
        if self.DATABASE_URL.startswith("postgresql://"):
            self.DATABASE_URL = self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif self.DATABASE_URL.startswith("postgres://"):
            self.DATABASE_URL = self.DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)


settings = Settings()
