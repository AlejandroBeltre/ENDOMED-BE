"""Sets audit context (current user + client IP) on a thread-local so that
audit_post_save signals can read them without needing access to the request.
"""

import threading
from typing import Callable

from django.http import HttpRequest, HttpResponse

_audit_context: threading.local = threading.local()


class AuditLogMiddleware:
    def __init__(self, get_response: Callable) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        _audit_context.user = getattr(request, "user", None)
        _audit_context.ip = self._get_client_ip(request)
        response = self.get_response(request)
        return response

    @staticmethod
    def _get_client_ip(request: HttpRequest) -> str | None:
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")
