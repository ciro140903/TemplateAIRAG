# ====================
# PORTALE AZIENDALE - BACKEND DOCKERFILE
# ====================

FROM python:3.11-slim

# Metadata
LABEL maintainer="Portale Aziendale Team"
LABEL description="Backend API per Portale Aziendale con AI e RAG"
LABEL version="1.0.0"

# Variabili ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Crea utente non-root per sicurezza
RUN groupadd -r portal && useradd -r -g portal portal

# Installa dipendenze sistema e Poetry
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    curl \
    && pip install poetry \
    && rm -rf /var/lib/apt/lists/*

# Configura Poetry per non creare virtual environment
RUN poetry config virtualenvs.create false

# Crea directory di lavoro
WORKDIR /app

# Copia file Poetry
COPY pyproject.toml poetry.lock* ./

# Installa dipendenze con Poetry
RUN poetry install --only=main --no-root && rm -rf $POETRY_CACHE_DIR

# Copia codice applicazione
COPY . .

# Crea directory per upload e logs
RUN mkdir -p /app/uploads /app/logs

# Cambia ownership delle directory
RUN chown -R portal:portal /app

# Passa all'utente non-root
USER portal

# Esponi porta
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando di avvio
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 