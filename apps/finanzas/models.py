import uuid

from django.db import models


class Factura(models.Model):
    class Estado(models.TextChoices):
        BORRADOR = "borrador", "Borrador"
        EMITIDA = "emitida", "Emitida"
        PAGADA = "pagada", "Pagada"
        ANULADA = "anulada", "Anulada"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    paciente = models.ForeignKey(
        "pacientes.Paciente", on_delete=models.PROTECT, related_name="facturas"
    )
    cita = models.ForeignKey(
        "agenda.Cita",
        on_delete=models.PROTECT,
        related_name="facturas",
        null=True,
        blank=True,
    )
    sede = models.ForeignKey(
        "authentication.Sede", on_delete=models.PROTECT, related_name="facturas"
    )
    numero_factura = models.PositiveIntegerField(unique=True, editable=False)
    fecha = models.DateField()
    subtotal_rd = models.DecimalField(max_digits=10, decimal_places=2)
    descuento_rd = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    itbis_rd = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_rd = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.BORRADOR
    )
    seguro = models.ForeignKey(
        "pacientes.SeguroMedico",
        on_delete=models.PROTECT,
        related_name="facturas",
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        "authentication.User", on_delete=models.PROTECT, related_name="facturas_creadas"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "facturas"
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["sede", "fecha"]),
            models.Index(fields=["paciente"]),
            models.Index(fields=["estado"]),
            models.Index(fields=["deleted_at"]),
        ]

    def __str__(self) -> str:
        return f"F-{self.numero_factura:06d} — {self.paciente}"


class Pago(models.Model):
    class Metodo(models.TextChoices):
        EFECTIVO = "efectivo", "Efectivo"
        TARJETA = "tarjeta", "Tarjeta"
        TRANSFERENCIA = "transferencia", "Transferencia"
        SEGURO = "seguro", "Seguro"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    factura = models.ForeignKey(Factura, on_delete=models.PROTECT, related_name="pagos")
    monto_rd = models.DecimalField(max_digits=10, decimal_places=2)
    metodo = models.CharField(max_length=20, choices=Metodo.choices)
    referencia_transaccion = models.CharField(max_length=200, blank=True, default="")
    fecha_pago = models.DateField()
    registrado_por = models.ForeignKey(
        "authentication.User",
        on_delete=models.PROTECT,
        related_name="pagos_registrados",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "pagos"
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["factura"]),
            models.Index(fields=["fecha_pago"]),
        ]

    def __str__(self) -> str:
        return f"Pago RD${self.monto_rd} ({self.metodo}) → {self.factura}"


class Inventario(models.Model):
    class Categoria(models.TextChoices):
        SUERO = "suero", "Suero"
        SUPLEMENTO = "suplemento", "Suplemento"
        INSUMO = "insumo", "Insumo"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre_producto = models.CharField(max_length=200)
    categoria = models.CharField(max_length=20, choices=Categoria.choices)
    stock_actual = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(default=0)
    precio_unitario_rd = models.DecimalField(max_digits=10, decimal_places=2)
    proveedor = models.CharField(max_length=200, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inventario"
        verbose_name = "Ítem de Inventario"
        verbose_name_plural = "Ítems de Inventario"
        ordering = ["nombre_producto"]

    def __str__(self) -> str:
        return f"{self.nombre_producto} (stock: {self.stock_actual})"


class MovimientoInventario(models.Model):
    class Tipo(models.TextChoices):
        ENTRADA = "entrada", "Entrada"
        SALIDA = "salida", "Salida"
        AJUSTE = "ajuste", "Ajuste"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    inventario = models.ForeignKey(
        Inventario, on_delete=models.PROTECT, related_name="movimientos"
    )
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    cantidad = models.IntegerField()
    motivo = models.CharField(max_length=300)
    consulta = models.ForeignKey(
        "hce.Consulta",
        on_delete=models.PROTECT,
        related_name="movimientos_inventario",
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.PROTECT,
        related_name="movimientos_inventario",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "movimientos_inventario"
        verbose_name = "Movimiento de Inventario"
        verbose_name_plural = "Movimientos de Inventario"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["inventario", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.tipo} {self.cantidad}u → {self.inventario}"


class TarifaSeguro(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    aseguradora = models.CharField(max_length=200)
    tipo_consulta = models.ForeignKey(
        "agenda.TipoConsulta", on_delete=models.PROTECT, related_name="tarifas_seguro"
    )
    monto_cubierto_rd = models.DecimalField(max_digits=10, decimal_places=2)
    requiere_preautorizacion = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tarifas_seguro"
        verbose_name = "Tarifa de Seguro"
        verbose_name_plural = "Tarifas de Seguro"
        unique_together = [("aseguradora", "tipo_consulta")]
        ordering = ["aseguradora", "tipo_consulta"]

    def __str__(self) -> str:
        return f"{self.aseguradora} — {self.tipo_consulta}"
