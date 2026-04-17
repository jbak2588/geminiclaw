from pydantic_settings import BaseSettings
import os
import re
from dotenv import load_dotenv

# Ensure we override existing environment variables if .env changes
load_dotenv(override=True)

class Settings(BaseSettings):
    PROJECT_NAME: str = "Agentic Team Orchestrator"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Sandbox settings
    USE_DOCKER_SANDBOX: bool = True
    SANDBOX_IMAGE: str = "openclaw_worker_sandbox:latest"
    
    # CORS settings (comma-separated origins, "*" for dev only)
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "http://127.0.0.1:8080,http://localhost:8080,http://localhost:5173,http://127.0.0.1:5173")

    # ── Channel settings ──
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    WHATSAPP_TOKEN: str = os.getenv("WHATSAPP_TOKEN", "")
    WHATSAPP_PHONE_NUMBER_ID: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    WHATSAPP_VERIFY_TOKEN: str = os.getenv("WHATSAPP_VERIFY_TOKEN", "geminiclaw_verify")

settings = Settings()

# ──────────────────────────────────────────────
# Security utilities
# ──────────────────────────────────────────────
_SAFE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-]{1,128}$")

def sanitize_project_id(project_id: str) -> str:
    """Validate and sanitize project_id to prevent path traversal.
    Only allows alphanumeric characters, hyphens, and underscores.
    Returns 'default' if invalid.
    """
    if not project_id or not _SAFE_ID_PATTERN.match(project_id):
        return "default"
    return project_id

