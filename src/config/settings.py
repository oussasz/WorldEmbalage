# Application settings and configuration loading
from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / '.env'
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)


@dataclass(slots=True)
class Settings:
    app_name: str = 'World Embalage'
    env: str = os.getenv('APP_ENV', 'development')
    debug: bool = os.getenv('APP_DEBUG', '0') == '1'
    db_user: str = os.getenv('DB_USER', 'world_user')
    db_password: str = os.getenv('DB_PASSWORD', 'StrongPassword123')
    db_host: str = os.getenv('DB_HOST', '127.0.0.1')
    db_port: int = int(os.getenv('DB_PORT', '3306'))
    db_name: str = os.getenv('DB_NAME', 'world_embalage')
    db_echo: bool = os.getenv('DB_ECHO', '0') == '1'
    locale: str = os.getenv('APP_LOCALE', 'fr_FR')
    reports_dir: Path = PROJECT_ROOT / 'generated_reports'
    db_url: str = os.getenv('DB_URL', '')  # Full SQLAlchemy URL overrides individual parts when set

    def dsn(self) -> str:
        if self.db_url:
            return self.db_url
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"\
            f"@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
        )

    def ensure_dirs(self):
        self.reports_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_dirs()
