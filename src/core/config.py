"""Configuration management using pydantic-settings."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .exceptions import ConfigError


class Config(BaseSettings):
    """Application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = Field(
        default="sqlite:///data/database.db",
        description="Database connection URL"
    )

    # Feishu API (optional)
    feishu_app_id: Optional[str] = None
    feishu_app_secret: Optional[str] = None
    feishu_hot_topics_app_token: Optional[str] = None
    feishu_hot_topics_table_id: Optional[str] = None
    feishu_creators_app_token: Optional[str] = None
    feishu_creators_table_id: Optional[str] = None

    # Ima API (optional)
    ima_api_key: Optional[str] = None

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: str = Field(default="logs/mcn_ai.log", description="Log file path")

    # WebSearch settings
    max_concurrent_searches: int = Field(
        default=5,
        description="Maximum concurrent web searches"
    )
    search_timeout: int = Field(default=30, description="Search timeout in seconds")

    # Paths
    _base_path: Path = Path(__file__).parent.parent.parent
    _config_path: Path = _base_path / "config"
    _data_path: Path = _base_path / "data"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._keywords: Optional[Dict[str, List[str]]] = None
        self._platforms: Optional[Dict[str, Any]] = None
        self._personal_profile: Optional[Dict[str, Any]] = None

    @property
    def base_path(self) -> Path:
        """Get base project path."""
        return self._base_path

    @property
    def config_path(self) -> Path:
        """Get config directory path."""
        return self._config_path

    @property
    def data_path(self) -> Path:
        """Get data directory path."""
        return self._data_path

    @property
    def keywords(self) -> Dict[str, List[str]]:
        """Load keywords configuration."""
        if self._keywords is None:
            keywords_file = self._config_path / "keywords.yaml"
            if not keywords_file.exists():
                raise ConfigError(f"Keywords file not found: {keywords_file}")

            with open(keywords_file, "r", encoding="utf-8") as f:
                self._keywords = yaml.safe_load(f)

        return self._keywords

    @property
    def platforms(self) -> Dict[str, Any]:
        """Load platforms configuration."""
        if self._platforms is None:
            platforms_file = self._config_path / "platforms.yaml"
            if not platforms_file.exists():
                raise ConfigError(f"Platforms file not found: {platforms_file}")

            with open(platforms_file, "r", encoding="utf-8") as f:
                self._platforms = yaml.safe_load(f)

        return self._platforms

    @property
    def personal_profile(self) -> Dict[str, Any]:
        """Load personal profile configuration."""
        if self._personal_profile is None:
            profile_file = self._config_path / "personal_profile.json"
            if not profile_file.exists():
                raise ConfigError(f"Personal profile not found: {profile_file}")

            with open(profile_file, "r", encoding="utf-8") as f:
                self._personal_profile = json.load(f)

        return self._personal_profile

    def get_platform_config(self, platform: str) -> Dict[str, Any]:
        """Get configuration for a specific platform.

        Args:
            platform: Platform name (douyin, xiaohongshu, bilibili, etc.)

        Returns:
            Platform configuration dictionary

        Raises:
            ConfigError: If platform not found
        """
        platforms = self.platforms.get("platforms", {})
        if platform not in platforms:
            raise ConfigError(f"Platform '{platform}' not found in configuration")

        return platforms[platform]

    def get_keywords_by_category(self, category: str) -> List[str]:
        """Get keywords for a specific category.

        Args:
            category: Keyword category (ai_keywords, personal_brand_keywords, etc.)

        Returns:
            List of keywords

        Raises:
            ConfigError: If category not found
        """
        if category not in self.keywords:
            raise ConfigError(f"Keyword category '{category}' not found")

        return self.keywords[category]

    def has_feishu_config(self) -> bool:
        """Check if Feishu API is configured."""
        return bool(
            self.feishu_app_id
            and self.feishu_app_secret
            and self.feishu_hot_topics_app_token
        )


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get global configuration instance.

    Returns:
        Config instance
    """
    global _config
    if _config is None:
        _config = Config()
    return _config
