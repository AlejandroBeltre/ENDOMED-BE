import dj_database_url
from decouple import config

from .base import *  # noqa: F401, F403

# Use the same Railway connection but a separate test database
DATABASES = {
    "default": {
        **dj_database_url.config(
            default=config(
                "DATABASE_URL",
                default="postgresql://postgres:postgres@localhost:5432/endomed_dev",
            )
        ),
        "TEST": {"NAME": "endomed_test"},
    }
}

# Faster password hashing in tests
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Suppress whitenoise warning
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
