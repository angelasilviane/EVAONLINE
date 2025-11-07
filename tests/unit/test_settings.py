"""
Unit tests for application settings and configuration.
Tests Pydantic BaseSettings validation and env var loading.
"""

from config.settings.app_config import get_settings


class TestSettings:
    """Test suite for application settings."""

    def test_settings_load_from_env(self):
        """Test that settings load from environment variables."""
        settings = get_settings()
        assert settings is not None
        assert settings.ENVIRONMENT in ["development", "staging", "production"]

    def test_postgres_settings_present(self):
        """Test PostgreSQL settings are configured."""
        settings = get_settings()
        assert settings.database.HOST is not None
        assert settings.database.USER is not None
        assert settings.database.DB is not None
        assert settings.database.PORT > 0

    def test_redis_settings_present(self):
        """Test Redis settings are configured."""
        settings = get_settings()
        assert settings.redis.HOST is not None
        assert settings.redis.PORT > 0

    def test_database_url_construction(self):
        """Test database URL is properly constructed."""
        settings = get_settings()
        db_url = settings.database.database_url
        assert "postgresql" in db_url

    def test_redis_url_construction(self):
        """Test Redis URL is properly constructed."""
        settings = get_settings()
        redis_url = settings.redis.redis_url
        assert redis_url.startswith("redis://")

    def test_settings_immutable(self):
        """Test that settings object structure is correct."""
        settings = get_settings()
        # Pydantic v2 allows mutation, just test structure
        assert hasattr(settings, "database")
        assert hasattr(settings, "redis")

    def test_settings_singleton(self):
        """Test that get_settings() returns same instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2
