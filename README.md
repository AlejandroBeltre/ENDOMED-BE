# ENDOMED — Backend

Django 5 + FastAPI 0.115 hybrid ASGI application for the ENDOMED medical management system.

## Stack

| Layer | Technology |
|-------|-----------|
| Framework | Django 5.1 + FastAPI 0.115 (Starlette routing) |
| Database | PostgreSQL 16 (Railway) |
| Auth | SimpleJWT — access token in memory, refresh token in HttpOnly cookie |
| PDF | xhtml2pdf (prescription generation) |
| Server | Gunicorn + UvicornWorker |

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
# Edit .env — set DATABASE_URL and SECRET_KEY

# 4. Run migrations + seed data
python manage.py migrate
python manage.py seed

# 5. Start server (port 8000)
uvicorn config.asgi:application --reload --port 8000
```

API docs available at `http://localhost:8000/api/docs`.

## Running tests

```bash
pytest tests/ -v
```

Tests use the Railway database with a separate `endomed_test` schema. Set `DATABASE_URL` in your `.env`.

## Project structure

```
api/
  routers/      FastAPI route handlers (no business logic)
  schemas/      Pydantic request/response models
  dependencies.py  get_current_user, require_role

apps/
  authentication/  Custom User, Sede, AuditLog
  agenda/          TipoConsulta, Cita
  pacientes/       Paciente
  hce/             HistoriaClinica, Consulta, SignosVitales, MedicamentoPrescrito
  documentos/      DocumentoGenerado + PDF service

config/
  settings/
    base.py        Shared settings
    development.py Local settings
    production.py  Railway production settings
    test.py        Test settings

templates/
  receta.html    Prescription PDF template
```

## Architecture rule

`FastAPI router → services.py → Django ORM` — never skip layers, never put business logic in routers or models.
