from django.contrib import admin

from .models import Consulta, HistoriaClinica, MedicamentoPrescrito, SignosVitales


@admin.register(HistoriaClinica)
class HistoriaClinicaAdmin(admin.ModelAdmin):
    list_display = ["paciente", "created_at"]
    search_fields = ["paciente__nombre", "paciente__apellido", "paciente__cedula"]


@admin.register(Consulta)
class ConsultaAdmin(admin.ModelAdmin):
    list_display = ["hce", "tipo_consulta", "fecha_hora", "modalidad", "created_by"]
    list_filter = ["tipo_consulta", "modalidad"]
    ordering = ["-fecha_hora"]
    search_fields = ["hce__paciente__nombre", "hce__paciente__cedula"]


@admin.register(SignosVitales)
class SignosVitalesAdmin(admin.ModelAdmin):
    list_display = ["consulta", "peso_kg", "talla_cm", "imc", "pa_sistolica", "fc"]


@admin.register(MedicamentoPrescrito)
class MedicamentoPrescritoAdmin(admin.ModelAdmin):
    list_display = ["nombre", "presentacion", "dosis", "frecuencia", "consulta"]
    search_fields = ["nombre", "consulta__hce__paciente__nombre"]
