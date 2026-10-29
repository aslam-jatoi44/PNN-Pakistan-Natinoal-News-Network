import os
import warnings
from dotenv import load_dotenv

load_dotenv()

_WEAK_SUBSTRINGS = (
    "pnn-super-secret",
    "change-in-production",
    "changeme",
    "your-secret",
)
_ALLOWED_ALGORITHMS = {"HS256"}


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def validate_secret_key(secret_key: str, is_production: bool = False) -> str:
    """Validate SECRET_KEY strength without ever logging or exposing its value."""
    key = (secret_key or "").strip()
    if not key or len(key) < 32:
        raise RuntimeError(
            "SECRET_KEY must be set in the environment and be at least 32 characters long. "
            "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(48))\""
        )
    lowered = key.lower()
    if lowered == "pnn-super-secret-key-change-in-production-2024":
        raise RuntimeError(
            "SECRET_KEY is set to the default placeholder value. "
            "Set a strong random SECRET_KEY in your environment before starting."
        )
    if any(marker in lowered for marker in _WEAK_SUBSTRINGS):
        if is_production:
            raise RuntimeError(
                "SECRET_KEY contains an insecure placeholder pattern and cannot be used in production. "
                "Generate a random key with: python -c \"import secrets; print(secrets.token_urlsafe(48))\""
            )
        warnings.warn(
            "SECRET_KEY appears to contain a placeholder phrase. Rotate SECRET_KEY in .env before production.",
            UserWarning,
            stacklevel=2,
        )
    return key


class Settings:
    APP_ENV: str = os.getenv("APP_ENV", "production" if os.getenv("RAILWAY_ENVIRONMENT") else "development").strip().lower()
    SECRET_KEY: str = validate_secret_key(
        os.getenv("SECRET_KEY", ""),
        is_production=(APP_ENV == "production"),
    )
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./pnn_news.db")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256").strip()
    if ALGORITHM not in _ALLOWED_ALGORITHMS:
        raise RuntimeError(f"Unsupported JWT ALGORITHM '{ALGORITHM}'. Allowed: {sorted(_ALLOWED_ALGORITHMS)}")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    AUTO_INIT_DB: bool = _env_bool("AUTO_INIT_DB", default=False)
    COOKIE_SECURE: bool = _env_bool("COOKIE_SECURE", default=(APP_ENV == "production"))

    # Social Media
    FACEBOOK_APP_ID: str = os.getenv("FACEBOOK_APP_ID", "")
    FACEBOOK_APP_SECRET: str = os.getenv("FACEBOOK_APP_SECRET", "")
    FACEBOOK_ACCESS_TOKEN: str = os.getenv("FACEBOOK_ACCESS_TOKEN", "")

    INSTAGRAM_APP_ID: str = os.getenv("INSTAGRAM_APP_ID", "")
    INSTAGRAM_APP_SECRET: str = os.getenv("INSTAGRAM_APP_SECRET", "")

    TWITTER_API_KEY: str = os.getenv("TWITTER_API_KEY", "")
    TWITTER_API_SECRET: str = os.getenv("TWITTER_API_SECRET", "")
    TWITTER_ACCESS_TOKEN: str = os.getenv("TWITTER_ACCESS_TOKEN", "")
    TWITTER_ACCESS_TOKEN_SECRET: str = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")
    TWITTER_BEARER_TOKEN: str = os.getenv("TWITTER_BEARER_TOKEN", "")

    WHATSAPP_PHONE_NUMBER_ID: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    WHATSAPP_ACCESS_TOKEN: str = os.getenv("WHATSAPP_ACCESS_TOKEN", "")

    YOUTUBE_CLIENT_ID: str = os.getenv("YOUTUBE_CLIENT_ID", "")
    YOUTUBE_CLIENT_SECRET: str = os.getenv("YOUTUBE_CLIENT_SECRET", "")
    YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "")

settings = Settings()
