from pydantic import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Subscription Payments"
    DATABASE_URL: str = "sqlite:///./test.db"
    JWT_SECRET_KEY: str  # シークレットキーを必須項目に変更

    class Config:
        env_file = ".env"

settings = Settings()