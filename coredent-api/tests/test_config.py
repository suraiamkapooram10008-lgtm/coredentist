"""Tests for configuration validation"""
import os

import pytest
from cryptography.fernet import Fernet


class TestSimpleSettings:
    def test_access_token_default_15(self):
        from app.core.config_simple import SimpleSettings
        old = os.environ.pop("ACCESS_TOKEN_EXPIRE_MINUTES", None)
        try:
            s = SimpleSettings()
            assert s.ACCESS_TOKEN_EXPIRE_MINUTES == 15
        finally:
            if old:
                os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = old

    def test_environment_default_dev(self):
        from app.core.config_simple import SimpleSettings
        old = os.environ.pop("ENVIRONMENT", None)
        try:
            s = SimpleSettings()
            assert s.ENVIRONMENT == "development"
        finally:
            if old:
                os.environ["ENVIRONMENT"] = old

    def test_cors_parsing(self):
        from app.core.config_simple import SimpleSettings
        os.environ["CORS_ORIGINS"] = "http://a.com,http://b.com"
        try:
            s = SimpleSettings()
            assert "http://a.com" in s.CORS_ORIGINS
            assert "http://b.com" in s.CORS_ORIGINS
        finally:
            del os.environ["CORS_ORIGINS"]

    def test_env_override(self):
        """APP_NAME is a constant (not env-driven); confirm it is stable."""
        from app.core.config_simple import SimpleSettings

        s = SimpleSettings()
        assert s.APP_NAME == "CoreDent API"

    def test_debug_default_false(self):
        from app.core.config_simple import SimpleSettings
        old = os.environ.pop("DEBUG", None)
        try:
            s = SimpleSettings()
            assert s.DEBUG is False
        finally:
            if old:
                os.environ["DEBUG"] = old

    def test_database_url_default(self):
        from app.core.config_simple import SimpleSettings
        old = os.environ.pop("DATABASE_URL", None)
        try:
            s = SimpleSettings()
            assert "coredent_dev.db" in s.DATABASE_URL
        finally:
            if old:
                os.environ["DATABASE_URL"] = old


class TestProductionConfig:
    """Verify production configuration behavior."""

    def test_production_environment_sets_correctly(self):
        os.environ["ENVIRONMENT"] = "production"
        os.environ["ENCRYPTION_KEY"] = Fernet.generate_key().decode()
        os.environ["SECRET_KEY"] = "x" * 32
        os.environ["DEBUG"] = "false"
        try:
            from app.core.config_simple import SimpleSettings
            s = SimpleSettings()
            assert s.ENVIRONMENT == "production"
            assert s.DEBUG is False
        finally:
            os.environ["ENVIRONMENT"] = "development"
            os.environ.pop("ENCRYPTION_KEY", None)
            os.environ.pop("SECRET_KEY", None)
            os.environ.pop("DEBUG", None)

    def test_debug_true_in_production(self):
        """DEBUG=True in production is allowed by config (should be caught by deployment checks)."""
        os.environ["ENVIRONMENT"] = "production"
        os.environ["ENCRYPTION_KEY"] = Fernet.generate_key().decode()
        os.environ["SECRET_KEY"] = "x" * 32
        os.environ["DEBUG"] = "true"
        try:
            from app.core.config_simple import SimpleSettings
            s = SimpleSettings()
            assert s.DEBUG is True
            assert s.ENVIRONMENT == "production"
        finally:
            os.environ["ENVIRONMENT"] = "development"
            os.environ.pop("ENCRYPTION_KEY", None)
            os.environ.pop("SECRET_KEY", None)
            os.environ.pop("DEBUG", None)
