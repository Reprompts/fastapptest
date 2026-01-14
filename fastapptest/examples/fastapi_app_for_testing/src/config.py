# config.py


from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "FastSecForge"
    SECRET_KEY: str = "change-me-in-.env"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    DATABASE_TYPE: str = "sql"
    DATABASE_URL: str = "sqlite:///:memory:"
    DATABASE_NAME: str = "fastsecforge"

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
