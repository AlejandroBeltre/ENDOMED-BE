from django.contrib import admin

from .models import Paciente


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ["cedula", "nombre", "apellido", "telefono_whatsapp", "sexo", "sede"]
    search_fields = ["cedula", "nombre", "apellido"]
    list_filter = ["sexo", "sede"]
    ordering = ["apellido", "nombre"]
