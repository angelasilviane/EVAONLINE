"""
Integration tests for database operations and models.
Tests SQLAlchemy models, connections, and CRUD operations.
"""

from sqlalchemy.orm import Session


class TestDatabaseConnection:
    """Test database connectivity and operations."""

    def test_db_session_available(self, db_session: Session):
        """Test that database session is available."""
        assert db_session is not None

    def test_db_can_execute_query(self, db_session: Session):
        """Test that we can execute a simple query."""
        from sqlalchemy import text

        result = db_session.execute(text("SELECT 1"))
        assert result.fetchone()[0] == 1

    def test_db_tables_exist(self, db_session: Session):
        """Test that expected tables exist in database."""
        from sqlalchemy import text, inspect
        from backend.database.connection import engine

        inspector = inspect(engine)
        tables = inspector.get_table_names()

        # Check for key tables
        expected_tables = [
            "admin_users",
            "user_session_cache",
            "cache_metadata",
            "user_favorites",
            "favorite_location",
        ]

        for table in expected_tables:
            assert table in tables, f"Table {table} not found in database"


class TestModels:
    """Test SQLAlchemy model definitions."""

    def test_admin_user_model_importable(self):
        """Test AdminUser model can be imported."""
        from backend.database.models import AdminUser

        assert AdminUser is not None
        assert hasattr(AdminUser, "__table__")

    def test_user_session_cache_model_importable(self):
        """Test UserSessionCache model can be imported."""
        from backend.database.models import UserSessionCache

        assert UserSessionCache is not None

    def test_cache_metadata_model_importable(self):
        """Test CacheMetadata model can be imported."""
        from backend.database.models import CacheMetadata

        assert CacheMetadata is not None

    def test_user_favorites_model_importable(self):
        """Test UserFavorites model can be imported."""
        from backend.database.models import UserFavorites

        assert UserFavorites is not None

    def test_favorite_location_model_importable(self):
        """Test FavoriteLocation model can be imported."""
        from backend.database.models import FavoriteLocation

        assert FavoriteLocation is not None

    def test_models_have_tables(self):
        """Test that all models are properly mapped to tables."""
        from backend.database.models import (
            AdminUser,
            UserSessionCache,
            CacheMetadata,
            UserFavorites,
            FavoriteLocation,
        )

        models = [
            AdminUser,
            UserSessionCache,
            CacheMetadata,
            UserFavorites,
            FavoriteLocation,
        ]

        for model in models:
            assert hasattr(
                model, "__table__"
            ), f"{model.__name__} not mapped to table"
            assert hasattr(
                model, "__tablename__"
            ), f"{model.__name__} missing __tablename__"
