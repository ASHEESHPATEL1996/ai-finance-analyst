from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

try:
    import streamlit as st
    for key, value in st.secrets.items():
        os.environ.setdefault(key.upper(), str(value))
except Exception:
    pass


class Settings(BaseSettings):
    llm_provider: str = "groq"
    groq_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    alpha_vantage_api_key: str = ""
    app_env: str = "development"
    app_host: str = "127.0.0.1"
    app_port: int = 8000

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()