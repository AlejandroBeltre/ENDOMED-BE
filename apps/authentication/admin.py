from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import AuditLog, Sede, User, UserSede


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["email"]
    list_display = ["email", "nombre", "apellido", "role", "is_active"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Información personal", {"fields": ("nombre", "apellido", "role")}),
        (
            "Permisos",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "nombre",
                    "apellido",
                    "role",
                    "password1",
                    "password2",
                ),
            },
        ),
    )
    search_fields = ["email", "nombre", "apellido"]
    filter_horizontal = ("groups", "user_permissions")


@admin.register(Sede)
class SedeAdmin(admin.ModelAdmin):
    list_display = ["nombre", "ciudad", "is_active"]


@admin.register(UserSede)
class UserSedeAdmin(admin.ModelAdmin):
    list_display = ["user", "sede", "is_primary"]
    list_filter = ["sede"]


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = [
        "timestamp",
        "action",
        "table_name",
        "record_id",
        "user",
        "ip_address",
    ]
    readonly_fields = [
        "timestamp",
        "action",
        "table_name",
        "record_id",
        "user",
        "ip_address",
        "old_values",
        "new_values",
    ]
    list_filter = ["action", "table_name"]
    ordering = ["-timestamp"]
