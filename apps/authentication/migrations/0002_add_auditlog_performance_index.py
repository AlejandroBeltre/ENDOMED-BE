"""Add composite index (table_name, timestamp) on audit_log."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0001_initial"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(
                fields=["table_name", "timestamp"],
                name="auditlog_table_ts_idx",
            ),
        ),
    ]
