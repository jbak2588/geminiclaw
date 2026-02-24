from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

# Ensure we override existing environment variables if .env changes
load_dotenv(override=True)

class Settings(BaseSettings):
    PROJECT_NAME: str = "Agentic Team Orchestrator"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

settings = Settings()
