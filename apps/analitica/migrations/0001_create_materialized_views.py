"""
Create three PostgreSQL materialized views for analytics.

Views are refreshed by Celery tasks (never in real-time clinical flows):
  mv_consultas_resumen    → daily 3 AM
  mv_ingresos_resumen     → hourly
  mv_prevalencia_diagnosticos → daily 3 AM

Each view derives sede from the cita when available, falling back to the
patient's sede (COALESCE).  grupo_etario is computed from fecha_nacimiento.
"""

from django.db import migrations

# ── shared CASE expression for age groups ────────────────────────────────────

_GRUPO_ETARIO_CASE = """
    CASE
        WHEN EXTRACT(YEAR FROM AGE(p.fecha_nacimiento)) < 18  THEN '0-17'
        WHEN EXTRACT(YEAR FROM AGE(p.fecha_nacimiento)) BETWEEN 18 AND 29 THEN '18-29'
        WHEN EXTRACT(YEAR FROM AGE(p.fecha_nacimiento)) BETWEEN 30 AND 44 THEN '30-44'
        WHEN EXTRACT(YEAR FROM AGE(p.fecha_nacimiento)) BETWEEN 45 AND 59 THEN '45-59'
        ELSE '60+'
    END
"""

# ── mv_consultas_resumen ──────────────────────────────────────────────────────

_MV_CONSULTAS_UP = f"""
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_consultas_resumen AS
SELECT
    COALESCE(cs.id,  ps.id)      AS sede_id,
    COALESCE(cs.nombre, ps.nombre) AS sede_nombre,
    tc.id                          AS tipo_consulta_id,
    tc.nombre                      AS tipo_consulta,
    DATE_TRUNC('month', c.fecha_hora) AS mes,
    p.sexo,
    {_GRUPO_ETARIO_CASE}             AS grupo_etario,
    COUNT(*)                         AS total_consultas
FROM consultas c
JOIN historias_clinicas hce ON c.hce_id = hce.id
JOIN pacientes p             ON hce.paciente_id = p.id
JOIN sedes ps                ON p.sede_id = ps.id
JOIN tipos_consulta tc       ON c.tipo_consulta_id = tc.id
LEFT JOIN citas ci            ON c.cita_id = ci.id
LEFT JOIN sedes cs            ON ci.sede_id = cs.id
WHERE c.deleted_at IS NULL
GROUP BY
    COALESCE(cs.id,  ps.id),
    COALESCE(cs.nombre, ps.nombre),
    tc.id,
    tc.nombre,
    DATE_TRUNC('month', c.fecha_hora),
    p.sexo,
    {_GRUPO_ETARIO_CASE}
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS mv_consultas_resumen_unique_idx
ON mv_consultas_resumen (
    sede_id, tipo_consulta_id, mes, sexo, grupo_etario
);
"""

_MV_CONSULTAS_DOWN = """
DROP MATERIALIZED VIEW IF EXISTS mv_consultas_resumen;
"""

# ── mv_ingresos_resumen ───────────────────────────────────────────────────────

_MV_INGRESOS_UP = """
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_ingresos_resumen AS
SELECT
    s.id                              AS sede_id,
    s.nombre                          AS sede_nombre,
    COALESCE(tc.nombre, 'Sin consulta') AS tipo_consulta,
    DATE_TRUNC('month', f.fecha)      AS periodo,
    f.estado,
    COUNT(*)                          AS total_facturas,
    SUM(f.total_rd)                   AS total_ingresos,
    SUM(f.total_rd) FILTER (WHERE f.estado = 'pagada') AS total_cobrado
FROM facturas f
JOIN sedes s                 ON f.sede_id = s.id
LEFT JOIN citas ci            ON f.cita_id = ci.id
LEFT JOIN tipos_consulta tc   ON ci.tipo_consulta_id = tc.id
WHERE f.deleted_at IS NULL
GROUP BY
    s.id,
    s.nombre,
    COALESCE(tc.nombre, 'Sin consulta'),
    DATE_TRUNC('month', f.fecha),
    f.estado
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS mv_ingresos_resumen_unique_idx
ON mv_ingresos_resumen (sede_id, tipo_consulta, periodo, estado);
"""

_MV_INGRESOS_DOWN = """
DROP MATERIALIZED VIEW IF EXISTS mv_ingresos_resumen;
"""

# ── mv_prevalencia_diagnosticos ───────────────────────────────────────────────

_MV_PREVALENCIA_UP = f"""
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_prevalencia_diagnosticos AS
SELECT
    dc.codigo_cie10,
    dc.descripcion,
    DATE_TRUNC('month', c.fecha_hora)  AS mes,
    p.sexo,
    {_GRUPO_ETARIO_CASE}               AS grupo_etario,
    COALESCE(cs.id,  ps.id)            AS sede_id,
    COALESCE(cs.nombre, ps.nombre)     AS sede_nombre,
    COUNT(*)                           AS frecuencia
FROM diagnosticos_consulta dc
JOIN consultas c             ON dc.consulta_id = c.id
JOIN historias_clinicas hce  ON c.hce_id = hce.id
JOIN pacientes p             ON hce.paciente_id = p.id
JOIN sedes ps                ON p.sede_id = ps.id
LEFT JOIN citas ci            ON c.cita_id = ci.id
LEFT JOIN sedes cs            ON ci.sede_id = cs.id
WHERE c.deleted_at IS NULL
  AND dc.tipo = 'principal'
GROUP BY
    dc.codigo_cie10,
    dc.descripcion,
    DATE_TRUNC('month', c.fecha_hora),
    p.sexo,
    {_GRUPO_ETARIO_CASE},
    COALESCE(cs.id,  ps.id),
    COALESCE(cs.nombre, ps.nombre)
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS mv_prevalencia_unique_idx
ON mv_prevalencia_diagnosticos (
    codigo_cie10, mes, sexo, grupo_etario, sede_id
);
"""

_MV_PREVALENCIA_DOWN = """
DROP MATERIALIZED VIEW IF EXISTS mv_prevalencia_diagnosticos;
"""


class Migration(migrations.Migration):

    dependencies = [
        ("hce", "0002_add_diagnostico_consulta"),
        ("finanzas", "0001_initial_finanzas"),
        ("agenda", "0002_initial"),
        ("pacientes", "0002_add_contacto_emergencia_seguro_medico"),
        ("authentication", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql=_MV_CONSULTAS_UP,
            reverse_sql=_MV_CONSULTAS_DOWN,
        ),
        migrations.RunSQL(
            sql=_MV_INGRESOS_UP,
            reverse_sql=_MV_INGRESOS_DOWN,
        ),
        migrations.RunSQL(
            sql=_MV_PREVALENCIA_UP,
            reverse_sql=_MV_PREVALENCIA_DOWN,
        ),
    ]
