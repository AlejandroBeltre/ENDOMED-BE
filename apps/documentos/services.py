from datetime import date
from io import BytesIO

from django.template.loader import render_to_string
from xhtml2pdf import pisa

from apps.hce.models import Consulta


def generar_receta_pdf(consulta_id: str, current_user) -> bytes:
    """
    Renders the receta.html template for the given consulta and
    converts it to PDF bytes using xhtml2pdf.
    """
    consulta = (
        Consulta.objects.select_related(
            "hce__paciente__sede",
            "tipo_consulta",
            "created_by",
        )
        .prefetch_related("medicamentos")
        .get(id=consulta_id, deleted_at__isnull=True)
    )

    paciente = consulta.hce.paciente
    today = date.today()
    edad = (
        today.year
        - paciente.fecha_nacimiento.year
        - (
            (today.month, today.day)
            < (paciente.fecha_nacimiento.month, paciente.fecha_nacimiento.day)
        )
    )

    context = {
        "consulta": consulta,
        "paciente": paciente,
        "sede": paciente.sede,
        "doctora": consulta.created_by,
        "edad": edad,
        "medicamentos": list(consulta.medicamentos.all()),
        "plan_terapeutico": consulta.plan_terapeutico,
        "fecha": today.strftime("%d/%m/%Y"),
    }

    html_string = render_to_string("receta.html", context)

    buffer = BytesIO()
    pisa_status = pisa.CreatePDF(html_string, dest=buffer, encoding="utf-8")

    if pisa_status.err:
        raise RuntimeError(f"Error generando PDF: {pisa_status.err}")

    return buffer.getvalue()
