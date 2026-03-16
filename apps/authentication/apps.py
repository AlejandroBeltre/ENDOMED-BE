from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.authentication"
    verbose_name = "Autenticación"

    def ready(self) -> None:
        from apps.authentication.signals import connect_audit_signals

        connect_audit_signals()
