"""ASGI entry point for ENDOMED backend.

Routing:
  /api/* → FastAPI (all REST endpoints)
  /*     → Django (admin, static files)
"""

import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from django.core.asgi import get_asgi_application  # noqa: E402
from starlette.applications import Starlette  # noqa: E402
from starlette.routing import Mount  # noqa: E402

from api.main import app as fastapi_app  # noqa: E402

django_app = get_asgi_application()

application = Starlette(
    routes=[
        Mount("/api", app=fastapi_app),
        Mount("/", app=django_app),
    ]
)
