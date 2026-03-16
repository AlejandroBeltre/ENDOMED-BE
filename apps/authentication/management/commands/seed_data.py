"""
Management command: seed_data
Creates test fixtures for development/staging.

Usage:
    python manage.py seed_data
    python manage.py seed_data --reset   # deletes existing seed data first
"""
import uuid

from django.core.management.base import BaseCommand
from django.db import transaction

# Fixed UUIDs so the JSON test cases below are stable
SEDE_SD_ID   = uuid.UUID("11111111-0000-0000-0000-000000000001")
SEDE_STG_ID  = uuid.UUID("11111111-0000-0000-0000-000000000002")
SEDE_PP_ID   = uuid.UUID("11111111-0000-0000-0000-000000000003")

USER_DOC_ID  = uuid.UUID("22222222-0000-0000-0000-000000000001")
USER_SEC_ID  = uuid.UUID("22222222-0000-0000-0000-000000000002")

TC_CTRL_ID   = uuid.UUID("33333333-0000-0000-0000-000000000001")
TC_NUEVO_ID  = uuid.UUID("33333333-0000-0000-0000-000000000002")
TC_NUTRI_ID  = uuid.UUID("33333333-0000-0000-0000-000000000003")

PAC_1_ID     = uuid.UUID("44444444-0000-0000-0000-000000000001")
PAC_2_ID     = uuid.UUID("44444444-0000-0000-0000-000000000002")
PAC_3_ID     = uuid.UUID("44444444-0000-0000-0000-000000000003")


class Command(BaseCommand):
    help = "Seed the database with test data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing seed records before inserting",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        from apps.agenda.models import TipoConsulta
        from apps.authentication.models import Sede, User, UserSede
        from apps.pacientes.models import Paciente

        if options["reset"]:
            self.stdout.write("Deleting existing seed data...")
            Paciente.objects.filter(id__in=[PAC_1_ID, PAC_2_ID, PAC_3_ID]).delete()
            TipoConsulta.objects.filter(id__in=[TC_CTRL_ID, TC_NUEVO_ID, TC_NUTRI_ID]).delete()
            UserSede.objects.filter(user_id__in=[USER_DOC_ID, USER_SEC_ID]).delete()
            User.objects.filter(id__in=[USER_DOC_ID, USER_SEC_ID]).delete()
            Sede.objects.filter(id__in=[SEDE_SD_ID, SEDE_STG_ID, SEDE_PP_ID]).delete()

        # ── Sedes ────────────────────────────────────────────────────────────
        sede_sd, _ = Sede.objects.get_or_create(
            id=SEDE_SD_ID,
            defaults={"nombre": "Clínica Santo Domingo", "ciudad": "Santo Domingo"},
        )
        sede_stg, _ = Sede.objects.get_or_create(
            id=SEDE_STG_ID,
            defaults={"nombre": "Clínica Santiago", "ciudad": "Santiago"},
        )
        sede_pp, _ = Sede.objects.get_or_create(
            id=SEDE_PP_ID,
            defaults={"nombre": "Clínica Punta Cana", "ciudad": "Punta Cana"},
        )
        self.stdout.write(self.style.SUCCESS("OK Sedes created"))

        # ── Users ─────────────────────────────────────────────────────────────
        if not User.objects.filter(id=USER_DOC_ID).exists():
            doctora = User.objects.create_user(
                id=USER_DOC_ID,
                email="doctora@endomed.com",
                password="Endomed2026!",
                nombre="Elizabeth",
                apellido="Acosta",
                role="doctora",
                is_staff=True,
                is_superuser=True,
            )
        else:
            doctora = User.objects.get(id=USER_DOC_ID)

        if not User.objects.filter(id=USER_SEC_ID).exists():
            secretaria = User.objects.create_user(
                id=USER_SEC_ID,
                email="secretaria@endomed.com",
                password="Endomed2026!",
                nombre="Laura",
                apellido="Méndez",
                role="secretaria",
            )
        else:
            secretaria = User.objects.get(id=USER_SEC_ID)

        UserSede.objects.get_or_create(user=doctora,     sede=sede_sd,  defaults={"is_primary": True})
        UserSede.objects.get_or_create(user=doctora,     sede=sede_stg, defaults={"is_primary": False})
        UserSede.objects.get_or_create(user=doctora,     sede=sede_pp,  defaults={"is_primary": False})
        UserSede.objects.get_or_create(user=secretaria,  sede=sede_sd,  defaults={"is_primary": True})
        self.stdout.write(self.style.SUCCESS("OK Users created"))

        # ── Tipos de Consulta ─────────────────────────────────────────────────
        TipoConsulta.objects.get_or_create(
            id=TC_CTRL_ID,
            defaults={"nombre": "Control Metabólico", "duracion_min": 30, "tarifa_rd": "2500.00", "color_hex": "#00B0B9"},
        )
        TipoConsulta.objects.get_or_create(
            id=TC_NUEVO_ID,
            defaults={"nombre": "Consulta Nueva", "duracion_min": 60, "tarifa_rd": "4000.00", "color_hex": "#7C3AED"},
        )
        TipoConsulta.objects.get_or_create(
            id=TC_NUTRI_ID,
            defaults={"nombre": "Nutrición", "duracion_min": 45, "tarifa_rd": "3000.00", "color_hex": "#059669"},
        )
        self.stdout.write(self.style.SUCCESS("OK Tipos de Consulta created"))

        # ── Pacientes ─────────────────────────────────────────────────────────
        Paciente.objects.get_or_create(
            id=PAC_1_ID,
            defaults={
                "cedula": "001-1234567-8",
                "nombre": "María",
                "apellido": "García",
                "fecha_nacimiento": "1985-06-15",
                "sexo": "F",
                "telefono_whatsapp": "+18095551234",
                "email": "maria.garcia@email.com",
                "sede": sede_sd,
            },
        )
        Paciente.objects.get_or_create(
            id=PAC_2_ID,
            defaults={
                "cedula": "001-9876543-2",
                "nombre": "Carlos",
                "apellido": "Martínez",
                "fecha_nacimiento": "1972-11-30",
                "sexo": "M",
                "telefono_whatsapp": "+18095559876",
                "email": "carlos.martinez@email.com",
                "sede": sede_sd,
            },
        )
        Paciente.objects.get_or_create(
            id=PAC_3_ID,
            defaults={
                "cedula": "001-5554443-1",
                "nombre": "Ana",
                "apellido": "Rodríguez",
                "fecha_nacimiento": "1990-03-22",
                "sexo": "F",
                "telefono_whatsapp": "+18095553333",
                "email": "",
                "sede": sede_stg,
            },
        )
        self.stdout.write(self.style.SUCCESS("OK Pacientes created"))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 55))
        self.stdout.write(self.style.SUCCESS("Seed complete. Credentials:"))
        self.stdout.write("  doctora@endomed.com   / Endomed2026!")
        self.stdout.write("  secretaria@endomed.com / Endomed2026!")
        self.stdout.write(self.style.SUCCESS("=" * 55))
