# ── ENDOMED Backend ──────────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Install Python dependencies first (layer cache).
# pycairo (pulled in by xhtml2pdf → rlpycairo) has no pre-built wheel and
# must compile from source, so we need build tools + dev headers.
# We purge the build-only packages afterwards to keep the image lean while
# leaving the runtime libraries (libcairo2, libpango*) in place.
COPY requirements/ requirements/
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        # runtime deps for xhtml2pdf
        libcairo2 \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        # build-only deps for pycairo (removed below after pip install)
        gcc \
        pkg-config \
        libcairo2-dev \
        python3-dev \
    && pip install --no-cache-dir -r requirements/production.txt \
    && apt-get purge -y --auto-remove gcc pkg-config python3-dev \
    && apt-get remove -y libcairo2-dev \
    && rm -rf /var/lib/apt/lists/*

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
