"""Seed demo data for client onboarding sessions.

Creates:
  - 3 sedes (Cotuí, San Francisco de Macorís, Unidad Endometabólica)
  - 2 users  (doctora + secretaria) with onboarding credentials
  - 7 tipos de consulta (matching the production palette)
  - 10 pacientes (realistic Dominican names & data)
  - 8 citas  (2 for today, 3 upcoming, 3 completed in the last 30 days)
  - 3 consultas with signos vitales + diagnósticos for completed citas
  - 5 facturas (3 pagadas, 1 emitida, 1 borrador)
  - 5 inventario items (2 below minimum stock)

Usage:
    python manage.py seed_demo            # idempotent
    python manage.py seed_demo --reset    # wipe first, then re-create
"""

import uuid
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone as tz

# ── Stable IDs ────────────────────────────────────────────────────────────────

_S1 = uuid.UUID("aaaaaaaa-0001-0000-0000-000000000001")  # Cotuí
_S2 = uuid.UUID("aaaaaaaa-0001-0000-0000-000000000002")  # San Francisco
_S3 = uuid.UUID("aaaaaaaa-0001-0000-0000-000000000003")  # Unidad Endometabólica

_U1 = uuid.UUID("aaaaaaaa-0002-0000-0000-000000000001")  # doctora
_U2 = uuid.UUID("aaaaaaaa-0002-0000-0000-000000000002")  # secretaria

_TC = {
    "endo": uuid.UUID("aaaaaaaa-0003-0000-0000-000000000001"),
    "nutri": uuid.UUID("aaaaaaaa-0003-0000-0000-000000000002"),
    "supl": uuid.UUID("aaaaaaaa-0003-0000-0000-000000000003"),
    "suero": uuid.UUID("aaaaaaaa-0003-0000-0000-000000000004"),
    "preq_gen": uuid.UUID("aaaaaaaa-0003-0000-0000-000000000005"),
    "preq_bar": uuid.UUID("aaaaaaaa-0003-0000-0000-000000000006"),
    "preq_plas": uuid.UUID("aaaaaaaa-0003-0000-0000-000000000007"),
}

_PAC = [uuid.UUID(f"aaaaaaaa-0004-0000-0000-{i:012d}") for i in range(1, 11)]

SEDES = [
    {"id": _S1, "nombre": "Cotuí", "ciudad": "Cotuí"},
    {
        "id": _S2,
        "nombre": "San Francisco de Macorís",
        "ciudad": "San Francisco de Macorís",
    },
    {"id": _S3, "nombre": "Unidad Endometabólica", "ciudad": "Santo Domingo"},
]

TIPOS_CONSULTA = [
    {
        "id": _TC["endo"],
        "nombre": "Endocrinología",
        "duracion_min": 30,
        "tarifa_rd": "2500.00",
        "color_hex": "#00B0B9",
    },
    {
        "id": _TC["nutri"],
        "nombre": "Nutrición",
        "duracion_min": 45,
        "tarifa_rd": "2000.00",
        "color_hex": "#10B981",
    },
    {
        "id": _TC["supl"],
        "nombre": "Suplementos",
        "duracion_min": 20,
        "tarifa_rd": "1500.00",
        "color_hex": "#F59E0B",
    },
    {
        "id": _TC["suero"],
        "nombre": "Sueroterapia",
        "duracion_min": 60,
        "tarifa_rd": "3500.00",
        "color_hex": "#6366F1",
    },
    {
        "id": _TC["preq_gen"],
        "nombre": "Prequirúrgica General",
        "duracion_min": 45,
        "tarifa_rd": "3000.00",
        "color_hex": "#8B5CF6",
    },
    {
        "id": _TC["preq_bar"],
        "nombre": "Prequirúrgica Bariátrica",
        "duracion_min": 60,
        "tarifa_rd": "4000.00",
        "color_hex": "#EC4899",
    },
    {
        "id": _TC["preq_plas"],
        "nombre": "Prequirúrgica Plástica",
        "duracion_min": 45,
        "tarifa_rd": "3500.00",
        "color_hex": "#F97316",
    },
]

PACIENTES = [
    {
        "id": _PAC[0],
        "cedula": "001-1234567-8",
        "nombre": "María",
        "apellido": "García Pérez",
        "sexo": "F",
        "fecha_nacimiento": "1985-06-15",
        "telefono_whatsapp": "+18095551234",
        "email": "maria.garcia@email.com",
    },
    {
        "id": _PAC[1],
        "cedula": "001-9876543-2",
        "nombre": "Carlos",
        "apellido": "Martínez Díaz",
        "sexo": "M",
        "fecha_nacimiento": "1972-11-30",
        "telefono_whatsapp": "+18095559876",
        "email": "carlos.martinez@email.com",
    },
    {
        "id": _PAC[2],
        "cedula": "001-5554443-1",
        "nombre": "Ana",
        "apellido": "Rodríguez Sánchez",
        "sexo": "F",
        "fecha_nacimiento": "1990-03-22",
        "telefono_whatsapp": "+18095553333",
        "email": "",
    },
    {
        "id": _PAC[3],
        "cedula": "001-1112223-4",
        "nombre": "Luis",
        "apellido": "Almonte Cepeda",
        "sexo": "M",
        "fecha_nacimiento": "1968-08-10",
        "telefono_whatsapp": "+18095554444",
        "email": "lalmonte@gmail.com",
    },
    {
        "id": _PAC[4],
        "cedula": "001-2223334-5",
        "nombre": "Carmen",
        "apellido": "De la Cruz Vásquez",
        "sexo": "F",
        "fecha_nacimiento": "1995-01-28",
        "telefono_whatsapp": "+18095555555",
        "email": "",
    },
    {
        "id": _PAC[5],
        "cedula": "001-3334445-6",
        "nombre": "Juan",
        "apellido": "Matos Tejeda",
        "sexo": "M",
        "fecha_nacimiento": "1980-07-04",
        "telefono_whatsapp": "+18095556666",
        "email": "jmatos@hotmail.com",
    },
    {
        "id": _PAC[6],
        "cedula": "001-4445556-7",
        "nombre": "Rosa",
        "apellido": "Polanco Herrera",
        "sexo": "F",
        "fecha_nacimiento": "1975-12-19",
        "telefono_whatsapp": "+18095557777",
        "email": "",
    },
    {
        "id": _PAC[7],
        "cedula": "001-5556667-8",
        "nombre": "Pedro",
        "apellido": "Santana Féliz",
        "sexo": "M",
        "fecha_nacimiento": "1963-04-05",
        "telefono_whatsapp": "+18095558888",
        "email": "psantana@gmail.com",
    },
    {
        "id": _PAC[8],
        "cedula": "001-6667778-9",
        "nombre": "Lucia",
        "apellido": "Estrella Morel",
        "sexo": "F",
        "fecha_nacimiento": "2001-09-14",
        "telefono_whatsapp": "+18095559999",
        "email": "luciae@email.com",
    },
    {
        "id": _PAC[9],
        "cedula": "001-7778889-0",
        "nombre": "Ramón",
        "apellido": "Castillo Núñez",
        "sexo": "M",
        "fecha_nacimiento": "1958-02-27",
        "telefono_whatsapp": "+18095550000",
        "email": "",
    },
]

INVENTARIO = [
    {
        "nombre_producto": "Suero Fisiológico 500ml",
        "categoria": "suero",
        "stock_actual": 45,
        "stock_minimo": 20,
        "precio_unitario_rd": "180.00",
        "proveedor": "Farmacorp",
    },
    {
        "nombre_producto": "Suero Glucosado 5% 500ml",
        "categoria": "suero",
        "stock_actual": 8,
        "stock_minimo": 15,
        "precio_unitario_rd": "210.00",
        "proveedor": "Farmacorp",
    },
    {
        "nombre_producto": "Vitamina C 1000mg",
        "categoria": "suplemento",
        "stock_actual": 3,
        "stock_minimo": 10,
        "precio_unitario_rd": "320.00",
        "proveedor": "Nutrisalud",
    },
    {
        "nombre_producto": "Jeringuillas 5ml (caja x50)",
        "categoria": "insumo",
        "stock_actual": 6,
        "stock_minimo": 5,
        "precio_unitario_rd": "450.00",
        "proveedor": "MediSupply",
    },
    {
        "nombre_producto": "Guantes Latex M (caja x100)",
        "categoria": "insumo",
        "stock_actual": 12,
        "stock_minimo": 8,
        "precio_unitario_rd": "380.00",
        "proveedor": "MediSupply",
    },
]


class Command(BaseCommand):
    help = "Seeds realistic demo data for the client onboarding session."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing demo records before re-creating them.",
        )

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        from apps.agenda.models import Cita, TipoConsulta
        from apps.authentication.models import Sede, User, UserSede
        from apps.finanzas.models import Factura, Inventario, Pago
        from apps.hce.models import (
            DiagnosticoConsulta,
            HistoriaClinica,
            SignosVitales,
        )
        from apps.pacientes.models import Paciente

        if options["reset"]:
            self.stdout.write("  Eliminando datos demo existentes...")
            cedulas = [p["cedula"] for p in PACIENTES]
            Paciente.objects.filter(cedula__in=cedulas).delete()
            TipoConsulta.objects.filter(
                nombre__in=[t["nombre"] for t in TIPOS_CONSULTA]
            ).delete()
            demo_emails = ["doctora@endomed.com", "secretaria@endomed.com"]
            UserSede.objects.filter(user__email__in=demo_emails).delete()
            User.objects.filter(email__in=demo_emails).delete()
            Sede.objects.filter(nombre__in=[s["nombre"] for s in SEDES]).delete()
            Inventario.objects.filter(
                nombre_producto__in=[i["nombre_producto"] for i in INVENTARIO]
            ).delete()

        # ── Sedes ──────────────────────────────────────────────────────────────
        # Look up by nombre (natural key) — prod DB may have different UUIDs
        sedes: dict[str, Sede] = {}
        for data in SEDES:
            sede, created = Sede.objects.get_or_create(
                nombre=data["nombre"],
                defaults={"ciudad": data["ciudad"]},
            )
            sedes[sede.nombre] = sede
            self.stdout.write(f"  {'[+]' if created else '[ ]'} Sede: {sede.nombre}")

        sede_demo = sedes["Unidad Endometabólica"]

        # ── Tipos de consulta ──────────────────────────────────────────────────
        # Look up by nombre — prod DB may already have these with different UUIDs
        tipos: dict[str, TipoConsulta] = {}
        for data in TIPOS_CONSULTA:
            data.pop("id")
            tc, created = TipoConsulta.objects.get_or_create(
                nombre=data["nombre"], defaults=data
            )
            tipos[tc.nombre] = tc
            self.stdout.write(
                f"  {'[+]' if created else '[ ]'} TipoConsulta: {tc.nombre}"
            )

        # ── Usuarios ───────────────────────────────────────────────────────────
        # Look up by email — prod DB may have different UUIDs
        if not User.objects.filter(email="doctora@endomed.com").exists():
            doctora = User.objects.create_user(
                email="doctora@endomed.com",
                password="Demo2026!",
                nombre="Elizabeth",
                apellido="Acosta",
                role=User.Role.DOCTORA,
                is_staff=True,
                is_superuser=True,
            )
            created = True
        else:
            doctora = User.objects.get(email="doctora@endomed.com")
            created = False
        self.stdout.write(f"  {'[+]' if created else '[ ]'} User: {doctora.email}")

        for sede in sedes.values():
            UserSede.objects.get_or_create(
                user=doctora,
                sede=sede,
                defaults={"is_primary": sede.nombre == "Unidad Endometabólica"},
            )

        if not User.objects.filter(email="secretaria@endomed.com").exists():
            secretaria = User.objects.create_user(
                email="secretaria@endomed.com",
                password="Demo2026!",
                nombre="Laura",
                apellido="Méndez",
                role=User.Role.SECRETARIA,
            )
            created = True
        else:
            secretaria = User.objects.get(email="secretaria@endomed.com")
            created = False
        self.stdout.write(f"  {'[+]' if created else '[ ]'} User: {secretaria.email}")

        UserSede.objects.get_or_create(
            user=secretaria,
            sede=sede_demo,
            defaults={"is_primary": True},
        )

        # ── Pacientes ──────────────────────────────────────────────────────────
        pacientes: list[Paciente] = []
        for i, data in enumerate(PACIENTES):
            data.pop("id")
            sede = sedes["San Francisco de Macorís"] if i >= 7 else sede_demo
            pac, _ = Paciente.objects.get_or_create(
                cedula=data["cedula"],
                defaults={**data, "sede": sede},
            )
            pacientes.append(pac)
        self.stdout.write(f"  [+] {len(pacientes)} pacientes")

        # ── Citas ──────────────────────────────────────────────────────────────
        today = tz.localdate()
        tc_endo = tipos["Endocrinología"]
        tc_nutri = tipos["Nutrición"]
        tc_suero = tipos["Sueroterapia"]
        tc_preq = tipos["Prequirúrgica General"]

        cita_schedule = [
            # (paciente_idx, tipo, days_offset, hora, estado)
            (0, tc_endo, 0, 9, 0, "confirmada"),  # hoy 09:00
            (1, tc_nutri, 0, 10, 30, "pendiente"),  # hoy 10:30
            (2, tc_suero, 1, 8, 0, "pendiente"),  # mañana
            (3, tc_endo, 2, 11, 0, "pendiente"),  # pasado mañana
            (4, tc_preq, 3, 14, 0, "pendiente"),  # en 3 días
            (5, tc_endo, -7, 9, 0, "completada"),  # hace 1 semana
            (6, tc_nutri, -14, 10, 0, "completada"),  # hace 2 semanas
            (7, tc_suero, -21, 11, 0, "completada"),  # hace 3 semanas
        ]

        citas: list[Cita] = []
        for pac_idx, tc, day_offset, hour, minute, estado in cita_schedule:
            fecha_hora = tz.make_aware(
                tz.datetime(today.year, today.month, today.day, hour, minute)
                + timedelta(days=day_offset)
            )
            cita, created = Cita.objects.get_or_create(
                paciente=pacientes[pac_idx],
                tipo_consulta=tc,
                fecha_hora=fecha_hora,
                defaults={
                    "sede": sede_demo,
                    "profesional": doctora,
                    "duracion_min": tc.duracion_min,
                    "modalidad": Cita.Modalidad.PRESENCIAL,
                    "estado": estado,
                },
            )
            if not created and cita.estado != estado:
                cita.estado = estado
                cita.save(update_fields=["estado", "updated_at"])
            citas.append(cita)
        self.stdout.write(f"  [+] {len(citas)} citas")

        # ── HCE — consultas para las citas completadas ─────────────────────────
        completed_citas = [c for c in citas if c.estado == "completada"]
        consulta_data = [
            # (pac_idx, peso, talla, presion_sistolica, presion_diastolica, codigo_cie10, descripcion)
            (5, 78.5, 165, 130, 85, "E11", "Diabetes mellitus tipo 2"),
            (6, 92.0, 170, 120, 80, "E66.0", "Obesidad por exceso de calorías"),
            (7, 68.0, 158, 118, 76, "E03.9", "Hipotiroidismo, no especificado"),
        ]
        for i, (pac_idx, peso, talla, ps, pd, cie10, desc) in enumerate(consulta_data):
            pac = pacientes[pac_idx]
            cita = completed_citas[i]

            hce, _ = HistoriaClinica.objects.get_or_create(paciente=pac)

            from apps.hce.models import Consulta

            consulta, created = Consulta.objects.get_or_create(
                hce=hce,
                fecha_hora=cita.fecha_hora,
                defaults={
                    "cita": cita,
                    "created_by": doctora,
                    "tipo_consulta": cita.tipo_consulta,
                    "motivo_consulta": "Control periódico.",
                    "examen_fisico": {"nota": "Paciente en buen estado general."},
                    "plan_terapeutico": "Continuar tratamiento actual. Próximo control en 4 semanas.",
                },
            )

            if created:
                SignosVitales.objects.get_or_create(
                    consulta=consulta,
                    defaults={
                        "peso_kg": Decimal(str(peso)),
                        "talla_cm": Decimal(str(talla)),
                        "pa_sistolica": ps,
                        "pa_diastolica": pd,
                        "fc": 72,
                        "temperatura": Decimal("36.6"),
                    },
                )
                DiagnosticoConsulta.objects.get_or_create(
                    consulta=consulta,
                    codigo_cie10=cie10,
                    defaults={
                        "descripcion": desc,
                        "tipo": "principal",
                    },
                )

        self.stdout.write(
            f"  [+] {len(completed_citas)} consultas con signos vitales y diagnósticos"
        )

        # ── Facturas y pagos ───────────────────────────────────────────────────
        from django.db import connection

        # Ensure sequence exists (created by initial migration)
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT EXISTS (SELECT 1 FROM pg_sequences WHERE schemaname='public' AND sequencename='factura_numero_seq')"
            )
            seq_exists = cursor.fetchone()[0]
            if not seq_exists:
                cursor.execute("CREATE SEQUENCE factura_numero_seq START 1001")

        factura_specs = [
            # (pac_idx, cita_idx, total, estado)
            (5, 5, "2500.00", "pagada"),
            (6, 6, "2000.00", "pagada"),
            (7, 7, "3500.00", "pagada"),
            (0, 0, "2500.00", "emitida"),
            (1, 1, "2000.00", "borrador"),
        ]

        facturas_creadas = 0
        for pac_idx, cita_idx, total_str, estado in factura_specs:
            pac = pacientes[pac_idx]
            cita = citas[cita_idx]
            total = Decimal(total_str)

            if Factura.objects.filter(paciente=pac, cita=cita).exists():
                continue

            with connection.cursor() as cursor:
                cursor.execute("SELECT nextval('factura_numero_seq')")
                numero = cursor.fetchone()[0]

            factura = Factura.objects.create(
                numero_factura=numero,
                paciente=pac,
                cita=cita,
                sede=sede_demo,
                fecha=(
                    cita.fecha_hora.date()
                    if hasattr(cita.fecha_hora, "date")
                    else today
                ),
                subtotal_rd=total,
                descuento_rd=Decimal("0"),
                itbis_rd=Decimal("0"),
                total_rd=total,
                estado=estado,
                created_by=secretaria,
            )

            if estado == "pagada":
                Pago.objects.create(
                    factura=factura,
                    monto_rd=total,
                    metodo="efectivo",
                    fecha_pago=factura.fecha,
                    registrado_por=secretaria,
                )
            facturas_creadas += 1

        self.stdout.write(f"  [+] {facturas_creadas} facturas")

        # ── Inventario ─────────────────────────────────────────────────────────
        inv_creados = 0
        for data in INVENTARIO:
            _, created = Inventario.objects.get_or_create(
                nombre_producto=data["nombre_producto"],
                defaults={
                    "categoria": data["categoria"],
                    "stock_actual": data["stock_actual"],
                    "stock_minimo": data["stock_minimo"],
                    "precio_unitario_rd": Decimal(data["precio_unitario_rd"]),
                    "proveedor": data["proveedor"],
                },
            )
            if created:
                inv_creados += 1
        self.stdout.write(f"  [+] {inv_creados} ítems de inventario (2 bajo mínimo)")

        # ── Summary ────────────────────────────────────────────────────────────
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 55))
        self.stdout.write(
            self.style.SUCCESS("seed_demo completado — datos listos para onboarding.")
        )
        self.stdout.write("")
        self.stdout.write("  Credenciales demo:")
        self.stdout.write("    doctora@endomed.com     / Demo2026!")
        self.stdout.write("    secretaria@endomed.com  / Demo2026!")
        self.stdout.write("")
        self.stdout.write("  Datos creados:")
        self.stdout.write(
            f"    {len(sedes)} sedes · {len(TIPOS_CONSULTA)} tipos de consulta"
        )
        self.stdout.write(f"    {len(pacientes)} pacientes")
        self.stdout.write(f"    {len(citas)} citas (2 hoy, 3 próximas, 3 completadas)")
        self.stdout.write(f"    {len(completed_citas)} consultas con HCE")
        self.stdout.write(
            f"    {facturas_creadas} facturas · {len(INVENTARIO)} ítems inventario"
        )
        self.stdout.write(self.style.SUCCESS("=" * 55))
