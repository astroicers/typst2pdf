"""Application configuration."""


class BaseConfig:
    """Base configuration."""

    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    TESTING = False


class DevelopmentConfig(BaseConfig):
    """Development configuration."""

    DEBUG = True


class TestingConfig(BaseConfig):
    """Testing configuration."""

    TESTING = True


class ProductionConfig(BaseConfig):
    """Production configuration."""

    DEBUG = False


_config_map = {
    "default": ProductionConfig,
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(name: str = "default"):
    """Get configuration class by name."""
    return _config_map.get(name, ProductionConfig)
