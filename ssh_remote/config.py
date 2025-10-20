"""Configuration management for SSH Remote Assistant."""

from pathlib import Path
from typing import Optional
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


class Settings(BaseModel):
    """Application settings."""
    
    # Application
    app_name: str = "SSH Remote Assistant"
    log_level: str = "INFO"
    
    # AI Service
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    openai_base_url: Optional[str] = os.getenv("OPENAI_BASE_URL")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4")
    openai_temperature: float = 0.7
    openai_max_tokens: int = 4000
    
    # SSH
    ssh_connection_timeout: int = 30
    ssh_keepalive_interval: int = 60
    
    # Security
    encryption_key_salt: str = "ssh-remote-default-salt"
    dangerous_commands: list[str] = [
        "rm -rf",
        "dd if=",
        "mkfs",
        "> /dev/",
        "chmod -R 777",
    ]
    
    # Database
    database_path: Path = Path.home() / ".ssh_remote" / "data.db"
    
    @property
    def data_dir(self) -> Path:
        """Get the data directory path."""
        return self.database_path.parent


# Global settings instance
settings = Settings()

# Ensure data directory exists
settings.data_dir.mkdir(parents=True, exist_ok=True)
