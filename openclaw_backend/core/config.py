from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv


load_dotenv()


@dataclass
class Settings:
    app_env: str = os.getenv('APP_ENV', 'development')
    ai_provider: str = os.getenv('AI_PROVIDER', 'gemini')
    gemini_api_key: str = os.getenv('GEMINI_API_KEY', '')
    openai_api_key: str = os.getenv('OPENAI_API_KEY', '')
    log_dir: str = os.getenv('LOG_DIR', str(Path(__file__).resolve().parents[1] / 'logs'))
    storage_dir: str = os.getenv('STORAGE_DIR', str(Path(__file__).resolve().parents[1] / 'storage'))
    state_db_path: str = os.getenv('STATE_DB_PATH', str(Path(__file__).resolve().parents[1] / 'storage' / 'phase1_state.db'))
    allowed_origins_raw: str = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000,http://localhost:8000,http://localhost:8001')
    use_docker_sandbox: bool = os.getenv('USE_DOCKER_SANDBOX', 'false').lower() in {'1', 'true', 'yes', 'on'}
    whatsapp_verify_token: str = os.getenv('WHATSAPP_VERIFY_TOKEN', '')
    whatsapp_token: str = os.getenv('WHATSAPP_TOKEN', '')
    whatsapp_phone_number_id: str = os.getenv('WHATSAPP_PHONE_NUMBER_ID', '')
    telegram_bot_token: str = os.getenv('TELEGRAM_BOT_TOKEN', '')
    telegram_operator_chat_ids_raw: str = os.getenv('TELEGRAM_OPERATOR_CHAT_IDS', '')
    telegram_operator_usernames_raw: str = os.getenv('TELEGRAM_OPERATOR_USERNAMES', '')

    @property
    def allowed_origins(self) -> list[str]:
        return [item.strip() for item in self.allowed_origins_raw.split(',') if item.strip()]

    @property
    def GEMINI_API_KEY(self) -> str:
        return self.gemini_api_key

    @property
    def OPENAI_API_KEY(self) -> str:
        return self.openai_api_key

    @property
    def USE_DOCKER_SANDBOX(self) -> bool:
        return self.use_docker_sandbox

    @property
    def WHATSAPP_VERIFY_TOKEN(self) -> str:
        return self.whatsapp_verify_token

    @property
    def WHATSAPP_TOKEN(self) -> str:
        return self.whatsapp_token

    @property
    def WHATSAPP_PHONE_NUMBER_ID(self) -> str:
        return self.whatsapp_phone_number_id

    @property
    def TELEGRAM_BOT_TOKEN(self) -> str:
        return self.telegram_bot_token

    @property
    def telegram_operator_chat_ids(self) -> set[str]:
        return {
            item.strip()
            for item in self.telegram_operator_chat_ids_raw.split(',')
            if item.strip()
        }

    @property
    def telegram_operator_usernames(self) -> set[str]:
        values: set[str] = set()
        for item in self.telegram_operator_usernames_raw.split(','):
            normalized = item.strip().lower()
            if normalized.startswith('@'):
                normalized = normalized[1:]
            if normalized:
                values.add(normalized)
        return values

    @property
    def TELEGRAM_OPERATOR_CHAT_IDS(self) -> set[str]:
        return self.telegram_operator_chat_ids

    @property
    def TELEGRAM_OPERATOR_USERNAMES(self) -> set[str]:
        return self.telegram_operator_usernames


settings = Settings()
Path(settings.log_dir).mkdir(parents=True, exist_ok=True)
Path(settings.storage_dir).mkdir(parents=True, exist_ok=True)
Path(settings.state_db_path).parent.mkdir(parents=True, exist_ok=True)


def sanitize_project_id(project_id: str | None) -> str:
    if not project_id:
        return 'default'
    sanitized = ''.join(ch if ch.isalnum() or ch in {'-', '_'} else '_' for ch in project_id.strip())
    return sanitized or 'default'
