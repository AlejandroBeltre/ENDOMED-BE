import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("agenda", "0002_initial"),
        ("authentication", "0001_initial"),
        ("hce", "0001_initial"),
        ("pacientes", "0002_add_contacto_emergencia_seguro_medico"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Inventario",
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
                ("nombre_producto", models.CharField(max_length=200)),
                (
                    "categoria",
                    models.CharField(
                        choices=[
                            ("suero", "Suero"),
                            ("suplemento", "Suplemento"),
                            ("insumo", "Insumo"),
                        ],
                        max_length=20,
                    ),
                ),
                ("stock_actual", models.IntegerField(default=0)),
                ("stock_minimo", models.IntegerField(default=0)),
                (
                    "precio_unitario_rd",
                    models.DecimalField(decimal_places=2, max_digits=10),
                ),
                ("proveedor", models.CharField(blank=True, default="", max_length=200)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Ítem de Inventario",
                "verbose_name_plural": "Ítems de Inventario",
                "db_table": "inventario",
                "ordering": ["nombre_producto"],
            },
        ),
        migrations.CreateModel(
            name="Factura",
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
                (
                    "numero_factura",
                    models.PositiveIntegerField(editable=False, unique=True),
                ),
                ("fecha", models.DateField()),
                (
                    "subtotal_rd",
                    models.DecimalField(decimal_places=2, max_digits=10),
                ),
                (
                    "descuento_rd",
                    models.DecimalField(decimal_places=2, default=0, max_digits=10),
                ),
                (
                    "itbis_rd",
                    models.DecimalField(decimal_places=2, default=0, max_digits=10),
                ),
                ("total_rd", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "estado",
                    models.CharField(
                        choices=[
                            ("borrador", "Borrador"),
                            ("emitida", "Emitida"),
                            ("pagada", "Pagada"),
                            ("anulada", "Anulada"),
                        ],
                        default="borrador",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                (
                    "paciente",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="facturas",
                        to="pacientes.paciente",
                    ),
                ),
                (
                    "cita",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="facturas",
                        to="agenda.cita",
                    ),
                ),
                (
                    "sede",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="facturas",
                        to="authentication.sede",
                    ),
                ),
                (
                    "seguro",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="facturas",
                        to="pacientes.seguromedico",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="facturas_creadas",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Factura",
                "verbose_name_plural": "Facturas",
                "db_table": "facturas",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(
                        fields=["sede", "fecha"], name="facturas_sede_fecha_idx"
                    ),
                    models.Index(fields=["paciente"], name="facturas_paciente_idx"),
                    models.Index(fields=["estado"], name="facturas_estado_idx"),
                    models.Index(fields=["deleted_at"], name="facturas_deleted_at_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="Pago",
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
                ("monto_rd", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "metodo",
                    models.CharField(
                        choices=[
                            ("efectivo", "Efectivo"),
                            ("tarjeta", "Tarjeta"),
                            ("transferencia", "Transferencia"),
                            ("seguro", "Seguro"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "referencia_transaccion",
                    models.CharField(blank=True, default="", max_length=200),
                ),
                ("fecha_pago", models.DateField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "factura",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="pagos",
                        to="finanzas.factura",
                    ),
                ),
                (
                    "registrado_por",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="pagos_registrados",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Pago",
                "verbose_name_plural": "Pagos",
                "db_table": "pagos",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["factura"], name="pagos_factura_idx"),
                    models.Index(fields=["fecha_pago"], name="pagos_fecha_pago_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="MovimientoInventario",
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
                (
                    "tipo",
                    models.CharField(
                        choices=[
                            ("entrada", "Entrada"),
                            ("salida", "Salida"),
                            ("ajuste", "Ajuste"),
                        ],
                        max_length=20,
                    ),
                ),
                ("cantidad", models.IntegerField()),
                ("motivo", models.CharField(max_length=300)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "inventario",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="movimientos",
                        to="finanzas.inventario",
                    ),
                ),
                (
                    "consulta",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="movimientos_inventario",
                        to="hce.consulta",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="movimientos_inventario",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Movimiento de Inventario",
                "verbose_name_plural": "Movimientos de Inventario",
                "db_table": "movimientos_inventario",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(
                        fields=["inventario", "created_at"],
                        name="movimientos_inv_created_idx",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="TarifaSeguro",
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
                (
                    "monto_cubierto_rd",
                    models.DecimalField(decimal_places=2, max_digits=10),
                ),
                ("requiere_preautorizacion", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "tipo_consulta",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="tarifas_seguro",
                        to="agenda.tipoconsulta",
                    ),
                ),
            ],
            options={
                "verbose_name": "Tarifa de Seguro",
                "verbose_name_plural": "Tarifas de Seguro",
                "db_table": "tarifas_seguro",
                "ordering": ["aseguradora", "tipo_consulta"],
                "unique_together": {("aseguradora", "tipo_consulta")},
            },
        ),
        migrations.RunSQL(
            sql="CREATE SEQUENCE IF NOT EXISTS factura_numero_seq START 1;",
            reverse_sql="DROP SEQUENCE IF EXISTS factura_numero_seq;",
        ),
    ]
