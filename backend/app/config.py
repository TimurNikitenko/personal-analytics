from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgrespassword@localhost:5432/personal_analytics"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
