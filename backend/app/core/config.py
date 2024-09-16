from pydantic import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Subscription Payments"
    DATABASE_URL: str = "sqlite:///./test.db"

    class Config:
        env_file = ".env"

settings = Settings()