from django.contrib import admin

from .models import DocumentoGenerado


@admin.register(DocumentoGenerado)
class DocumentoGeneradoAdmin(admin.ModelAdmin):
    list_display = ["tipo", "paciente", "consulta", "created_by", "created_at"]
    list_filter = ["tipo"]
    ordering = ["-created_at"]
    search_fields = ["paciente__nombre", "paciente__cedula"]
