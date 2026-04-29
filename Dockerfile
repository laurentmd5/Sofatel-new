# Stage 1: Builder
FROM python:3.13-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libssl3 \
    libffi8 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Créer utilisateur AVANT de copier les packages
RUN useradd -m -u 1000 appuser

# Copier les packages dans le home de appuser
COPY --from=builder /root/.local /home/appuser/.local

# Définir PATH pour appuser
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Copier le code
COPY . .

# Créer les répertoires et donner les droits
RUN mkdir -p uploads logs && \
    chown -R appuser:appuser /app && \
    chown -R appuser:appuser /home/appuser/.local

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

EXPOSE 5000

ENTRYPOINT ["gunicorn"]
CMD ["--workers=2", "--bind=0.0.0.0:5000", "--timeout=600", "--keep-alive=5", "app:app"]