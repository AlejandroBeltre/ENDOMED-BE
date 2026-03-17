import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("hce", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="DiagnosticoConsulta",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("codigo_cie10", models.CharField(max_length=10)),
                ("descripcion", models.CharField(max_length=300)),
                (
                    "tipo",
                    models.CharField(
                        choices=[
                            ("principal", "Principal"),
                            ("secundario", "Secundario"),
                        ],
                        default="principal",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "consulta",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="diagnosticos",
                        to="hce.consulta",
                    ),
                ),
            ],
            options={
                "verbose_name": "Diagnóstico de Consulta",
                "verbose_name_plural": "Diagnósticos de Consulta",
                "db_table": "diagnosticos_consulta",
                "ordering": ["tipo", "codigo_cie10"],
                "indexes": [
                    models.Index(
                        fields=["codigo_cie10"],
                        name="diagnosticos_cie10_idx",
                    ),
                    models.Index(
                        fields=["consulta", "tipo"],
                        name="diagnosticos_consulta_tipo_idx",
                    ),
                ],
            },
        ),
    ]
