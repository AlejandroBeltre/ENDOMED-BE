"""Add composite index (sede_id, fecha, estado) on factura for financial queries."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("finanzas", "0001_initial_finanzas"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="factura",
            index=models.Index(
                fields=["sede_id", "fecha", "estado"],
                name="factura_sede_fecha_estado_idx",
            ),
        ),
    ]
