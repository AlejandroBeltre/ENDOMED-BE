"""AuditLog signal handlers.

Connected to clinical models in AuthenticationConfig.ready().
Uses thread-local context set by AuditLogMiddleware to capture user + IP.
"""

from __future__ import annotations

from apps.authentication.middleware import _audit_context


def connect_audit_signals() -> None:
    """Connect post_save signals for all audited models. Called from ready()."""
    from django.db.models.signals import post_save

    from apps.agenda.models import Cita
    from apps.documentos.models import DocumentoGenerado
    from apps.finanzas.models import Factura, Pago
    from apps.hce.models import Consulta
    from apps.pacientes.models import Paciente

    for model in [Cita, Paciente, Consulta, DocumentoGenerado, Factura, Pago]:
        post_save.connect(_audit_post_save, sender=model)


def _audit_post_save(sender, instance, created: bool, **kwargs) -> None:
    """Write an AuditLog row after any save on an audited model."""
    from apps.authentication.models import AuditLog

    user = getattr(_audit_context, "user", None)
    # Anonymous / unauthenticated Django users are not stored
    if user is not None and not getattr(user, "is_authenticated", False):
        user = None

    AuditLog.objects.create(
        user=user,
        action="CREATE" if created else "UPDATE",
        table_name=sender._meta.db_table,
        record_id=str(instance.pk),
        ip_address=getattr(_audit_context, "ip", None),
        new_values=None,  # Serialized values added in Phase 2
    )
