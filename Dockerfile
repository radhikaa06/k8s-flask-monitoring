# Small official Python base image ("slim" = Debian without extras).
FROM python:3.12-slim

# Version is passed in at build time (scripts/deploy.sh reads it from k8s/deployment.yaml).
ARG APP_VERSION=dev

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_VERSION=${APP_VERSION}

WORKDIR /app

# Copy requirements first: this layer is cached and only rebuilt when dependencies change.
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

# Never run as root inside a container.
RUN useradd --uid 10001 --no-create-home appuser
USER 10001

# Documentation only; the real port comes from config.py (PORT, default 5000).
EXPOSE 5000

CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]
