from django.contrib import admin

from apps.finanzas.models import (
    Factura,
    Inventario,
    MovimientoInventario,
    Pago,
    TarifaSeguro,
)

admin.site.register(Factura)
admin.site.register(Pago)
admin.site.register(Inventario)
admin.site.register(MovimientoInventario)
admin.site.register(TarifaSeguro)
