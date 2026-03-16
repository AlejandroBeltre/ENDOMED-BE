import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from .managers import CustomUserManager


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        DOCTORA = "doctora", "Doctora"
        SECRETARIA = "secretaria", "Secretaria"
        ASISTENTE = "asistente", "Asistente"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=Role.choices)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nombre", "apellido", "role"]

    objects = CustomUserManager()

    class Meta:
        db_table = "users"
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self) -> str:
        return f"{self.nombre} {self.apellido} ({self.role})"


class Sede(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100)
    ciudad = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sedes"
        verbose_name = "Sede"
        verbose_name_plural = "Sedes"

    def __str__(self) -> str:
        return f"{self.nombre} — {self.ciudad}"


class UserSede(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_sedes")
    sede = models.ForeignKey(Sede, on_delete=models.CASCADE, related_name="user_sedes")
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_sedes"
        unique_together = [("user", "sede")]
        verbose_name = "Usuario-Sede"
        verbose_name_plural = "Usuarios-Sedes"

    def __str__(self) -> str:
        return f"{self.user} @ {self.sede}"


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=20)  # CREATE | UPDATE | DELETE
    table_name = models.CharField(max_length=100)
    record_id = models.CharField(max_length=36)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_log"
        verbose_name = "Registro de Auditoría"
        verbose_name_plural = "Registros de Auditoría"
        ordering = ["-timestamp"]

    def __str__(self) -> str:
        return f"{self.action} on {self.table_name}:{self.record_id} by {self.user}"
