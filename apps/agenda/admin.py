from django.contrib import admin

from .models import Cita, TipoConsulta


@admin.register(TipoConsulta)
class TipoConsultaAdmin(admin.ModelAdmin):
    list_display = ["nombre", "duracion_min", "tarifa_rd", "color_hex"]


@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = [
        "paciente",
        "profesional",
        "sede",
        "tipo_consulta",
        "fecha_hora",
        "estado",
    ]
    list_filter = ["estado", "modalidad", "sede", "tipo_consulta"]
    search_fields = ["paciente__nombre", "paciente__apellido", "paciente__cedula"]
    ordering = ["-fecha_hora"]
