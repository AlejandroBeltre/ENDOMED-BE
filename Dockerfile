# ── ENDOMED Backend ──────────────────────────────────────────────────────────
FROM python:3.12-slim

# System libraries required by xhtml2pdf (pycairo + reportlab)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libcairo2 \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer cache)
COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/production.txt

# Copy source
COPY . .

EXPOSE 8080

# migrate → collectstatic → gunicorn
# $PORT is injected by Railway at runtime
CMD ["sh", "-c", \
     "python manage.py migrate --noinput && \
      python manage.py collectstatic --noinput && \
      gunicorn config.asgi:application \
        --worker-class uvicorn.workers.UvicornWorker \
        --bind 0.0.0.0:${PORT:-8080} \
        --workers 2 \
        --timeout 120 \
        --access-logfile -"]
