# ENDOMED — Backend

Django 5 + FastAPI 0.115 hybrid ASGI application for the ENDOMED medical management system.

## Stack

| Layer | Technology |
|-------|-----------|
| Framework | Django 5.1 + FastAPI 0.115 (Starlette routing) |
| Database | PostgreSQL 16 (Railway) |
| Cache | Redis (Django cache framework + Celery broker) |
| Auth | SimpleJWT — access token in memory, refresh token in HttpOnly cookie |
| PDF | WeasyPrint + Jinja2 |
| Tasks | Celery + Celery Beat |
| Server | Uvicorn (ASGI) |

## Local development

```bash
# 1. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/macOS

# 2. Install dependencies
pip install -r requirements/development.txt

# 3. Configure environment
cp .env.example .env
# Edit .env — set DATABASE_URL, REDIS_URL, and SECRET_KEY at minimum

# 4. Run migrations + seed data
python manage.py migrate
python manage.py seed          # dev credentials (doctora123 / secretaria123)

# 5. Start server (port 8000)
uvicorn config.asgi:application --reload --port 8000
```

API docs available at `http://localhost:8000/api/docs`.

## Seed commands

```bash
python manage.py seed          # dev data (idempotent, simple credentials)
python manage.py seed_demo     # onboarding demo data (realistic, Demo2026!)
python manage.py seed --reset  # wipe seed records and re-create
```

## Running tests

```bash
pytest tests/ -v
pytest --cov=apps --cov-report=term-missing
```

Requires a PostgreSQL database named `endomed_test`. Set `DATABASE_URL` in `.env`.

## Code quality

```bash
black .                  # format (88-char line length)
ruff check .             # lint + import sort
ruff check --fix .       # auto-fix
```

## Project structure

```
api/
  main.py           FastAPI app + router registration
  dependencies.py   get_current_user(), require_role() RBAC
  routers/          Route handlers per domain (no business logic)
  schemas/          Pydantic v2 request/response models

apps/
  authentication/   User, Sede, UserSede, AuditLog
  agenda/           TipoConsulta, Cita, Recordatorio
  pacientes/        Paciente, ContactoEmergencia, SeguroMedico
  hce/              HistoriaClinica, Consulta, SignosVitales,
                    DiagnosticoConsulta, MedicamentoPrescrito,
                    EvaluacionPrequirurgica, ResultadoLaboratorio
  documentos/       DocumentoGenerado, PlantillaDocumento
  finanzas/         Factura, Pago, Inventario, TarifaSeguro
  analitica/        Materialized views + reporting queries

config/
  settings/
    base.py         Shared settings (Redis cache, Celery, JWT)
    development.py  Local overrides (DEBUG=True)
    production.py   Railway production (CORS, HTTPS, DEBUG=False)
    test.py         Test database settings

tasks/
  recordatorios.py  Celery tasks: WhatsApp + email reminders
  reportes.py       Materialized view refresh tasks
```

## Architecture rule

`FastAPI router → apps/<domain>/services.py → Django ORM` — never skip layers, never put business logic in routers or models.

## Deployment (Railway)

```
endomed-backend   uvicorn config.asgi:application --host 0.0.0.0 --port $PORT
celery-worker     celery -A config worker -l info
celery-beat       celery -A config beat -l info
```

Release command: `python manage.py migrate --no-input`

Required environment variables: `DATABASE_URL` `SECRET_KEY` `REDIS_URL`
`CLOUDINARY_URL` `SENDGRID_API_KEY` `TWILIO_ACCOUNT_SID` `TWILIO_AUTH_TOKEN`
`TWILIO_WHATSAPP_FROM` `DJANGO_SETTINGS_MODULE=config.settings.production`
`SECURE_COOKIES=True` `CORS_ALLOWED_ORIGINS=https://app.endomed.app`
