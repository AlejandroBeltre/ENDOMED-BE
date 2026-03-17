"""Add composite index (sede_id, fecha_hora, estado) on cita for analytics queries."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("agenda", "0003_add_recordatorio"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="cita",
            index=models.Index(
                fields=["sede_id", "fecha_hora", "estado"],
                name="cita_sede_fecha_estado_idx",
            ),
        ),
    ]
