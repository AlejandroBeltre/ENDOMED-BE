web:    sh -c "python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn config.asgi:application --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8080} --workers 2 --timeout 120 --access-logfile -"
worker: python -m celery -A config worker -l info
beat:   python -m celery -A config beat -l info
