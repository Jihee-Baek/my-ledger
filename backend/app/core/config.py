from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite:///../data/ledger.db"
    imports_dir: str = "./imports"
    backups_dir: str = "./backups"
    log_level: str = "INFO"

    @property
    def database_path(self) -> Path:
        """Resolve the sqlite file path relative to the repo root."""
        url = self.database_url
        prefix = "sqlite:///"
        if not url.startswith(prefix):
            raise ValueError(f"Only sqlite URLs are supported in MVP, got: {url}")
        raw_path = url[len(prefix):]
        path = Path(raw_path)
        if not path.is_absolute():
            path = (REPO_ROOT / "backend" / path).resolve()
        return path

    @property
    def imports_path(self) -> Path:
        return (REPO_ROOT / self.imports_dir).resolve()

    @property
    def backups_path(self) -> Path:
        return (REPO_ROOT / self.backups_dir).resolve()


settings = Settings()
