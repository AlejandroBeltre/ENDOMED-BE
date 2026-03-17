import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pacientes", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ContactoEmergencia",
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
                ("nombre", models.CharField(max_length=200)),
                ("relacion", models.CharField(max_length=100)),
                ("telefono", models.CharField(max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "paciente",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="contactos_emergencia",
                        to="pacientes.paciente",
                    ),
                ),
            ],
            options={
                "verbose_name": "Contacto de Emergencia",
                "verbose_name_plural": "Contactos de Emergencia",
                "db_table": "contactos_emergencia",
            },
        ),
        migrations.CreateModel(
            name="SeguroMedico",
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
                ("aseguradora", models.CharField(max_length=200)),
                ("numero_poliza", models.CharField(max_length=100)),
                ("cobertura", models.JSONField(blank=True, default=dict)),
                ("vigencia_hasta", models.DateField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "paciente",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="seguros",
                        to="pacientes.paciente",
                    ),
                ),
            ],
            options={
                "verbose_name": "Seguro Médico",
                "verbose_name_plural": "Seguros Médicos",
                "db_table": "seguros_medicos",
            },
        ),
    ]
