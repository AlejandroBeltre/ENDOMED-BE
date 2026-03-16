"""Seed command: creates initial data for development and testing.

Usage:
    python manage.py seed            # idempotent — safe to run multiple times
    python manage.py seed --reset    # wipe seed records first, then re-create
"""

from django.core.management.base import BaseCommand
from django.db import transaction

TIPOS_CONSULTA = [
    {
        "nombre": "Endocrinología",
        "duracion_min": 30,
        "tarifa_rd": "2500.00",
        "color_hex": "#00B0B9",
    },
    {
        "nombre": "Nutrición",
        "duracion_min": 45,
        "tarifa_rd": "2000.00",
        "color_hex": "#10B981",
    },
    {
        "nombre": "Suplementos",
        "duracion_min": 20,
        "tarifa_rd": "1500.00",
        "color_hex": "#F59E0B",
    },
    {
        "nombre": "Sueroterapia",
        "duracion_min": 60,
        "tarifa_rd": "3500.00",
        "color_hex": "#6366F1",
    },
    {
        "nombre": "Prequirúrgica General",
        "duracion_min": 45,
        "tarifa_rd": "3000.00",
        "color_hex": "#8B5CF6",
    },
    {
        "nombre": "Prequirúrgica Bariátrica",
        "duracion_min": 60,
        "tarifa_rd": "4000.00",
        "color_hex": "#EC4899",
    },
    {
        "nombre": "Prequirúrgica Plástica",
        "duracion_min": 45,
        "tarifa_rd": "3500.00",
        "color_hex": "#F97316",
    },
]

SEDES = [
    {"nombre": "Cotuí", "ciudad": "Cotuí"},
    {"nombre": "San Francisco de Macorís", "ciudad": "San Francisco de Macorís"},
    {"nombre": "Unidad Endometabólica", "ciudad": "Santo Domingo"},
]


class Command(BaseCommand):
    help = "Seeds the database with initial development data."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing seed records before creating new ones.",
        )

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        from apps.agenda.models import TipoConsulta
        from apps.authentication.models import Sede, User, UserSede

        if options["reset"]:
            self.stdout.write("  Eliminando datos de seed...")
            User.objects.filter(
                email__in=["doctora@endomed.com", "secretaria@endomed.com"]
            ).delete()
            Sede.objects.filter(nombre__in=[s["nombre"] for s in SEDES]).delete()
            TipoConsulta.objects.filter(
                nombre__in=[t["nombre"] for t in TIPOS_CONSULTA]
            ).delete()

        # ── Sedes ──────────────────────────────────────────────────────────
        sedes: dict[str, Sede] = {}
        for data in SEDES:
            sede, created = Sede.objects.get_or_create(
                nombre=data["nombre"], defaults=data
            )
            sedes[sede.nombre] = sede
            self.stdout.write(f"  {'[+]' if created else '[ ]'} Sede: {sede.nombre}")

        # ── Tipos de consulta ──────────────────────────────────────────────
        for data in TIPOS_CONSULTA:
            tc, created = TipoConsulta.objects.get_or_create(
                nombre=data["nombre"], defaults=data
            )
            self.stdout.write(
                f"  {'[+]' if created else '[ ]'} TipoConsulta: {tc.nombre}"
            )

        # ── Doctora ────────────────────────────────────────────────────────
        doctora, created = User.objects.get_or_create(
            email="doctora@endomed.com",
            defaults={
                "nombre": "Elizabeth",
                "apellido": "Acosta",
                "role": User.Role.DOCTORA,
                "is_active": True,
                "is_staff": True,
            },
        )
        if created:
            doctora.set_password("doctora123")
            doctora.save()
        self.stdout.write(f"  {'[+]' if created else '[ ]'} User: {doctora.email}")

        for sede in sedes.values():
            UserSede.objects.get_or_create(
                user=doctora,
                sede=sede,
                defaults={"is_primary": sede.nombre == "Unidad Endometabólica"},
            )

        # ── Secretaria ─────────────────────────────────────────────────────
        secretaria, created = User.objects.get_or_create(
            email="secretaria@endomed.com",
            defaults={
                "nombre": "Ana",
                "apellido": "Martínez",
                "role": User.Role.SECRETARIA,
                "is_active": True,
            },
        )
        if created:
            secretaria.set_password("secretaria123")
            secretaria.save()
        self.stdout.write(f"  {'[+]' if created else '[ ]'} User: {secretaria.email}")

        UserSede.objects.get_or_create(
            user=secretaria,
            sede=sedes["Unidad Endometabólica"],
            defaults={"is_primary": True},
        )

        self.stdout.write(self.style.SUCCESS("\nSeed completado OK."))
        self.stdout.write("  doctora@endomed.com     / doctora123")
        self.stdout.write("  secretaria@endomed.com  / secretaria123")
