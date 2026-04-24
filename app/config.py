# app/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama3-groq-70b-8192-tool-use-preview"
    TOKEN_API_HEROES: str

    class Config:
        env_file = ".env"


# instância única usada em todo o projeto
settings = Settings()