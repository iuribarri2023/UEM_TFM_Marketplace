FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system avra && adduser --system --ingroup avra avra

COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir .

COPY alembic.ini gunicorn.conf.py wsgi.py ./
COPY docs/openapi.yaml ./docs/openapi.yaml
COPY migrations ./migrations
COPY scripts ./scripts
COPY schemas ./schemas

RUN mkdir -p /app/storage && chown -R avra:avra /app
USER avra

CMD ["gunicorn", "-c", "gunicorn.conf.py", "wsgi:app"]
