# Stage 1: Builder - Compiler les dépendances
FROM python:3.13-slim as builder

WORKDIR /app

# Installer les dépendances de compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copier requirements et installer dépendances Python
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime - Image finale
FROM python:3.13-slim

WORKDIR /app

# Installer les dépendances runtime uniquement
RUN apt-get update && apt-get install -y --no-install-recommends \
    libssl3 \
    libffi8 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copier les dépendances Python du builder
COPY --from=builder /root/.local /root/.local

# Définir PATH pour utiliser les packages installés localement
ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Copier le code application
COPY . .

# Créer les répertoires nécessaires
RUN mkdir -p uploads logs && chmod 755 uploads logs

# Créer utilisateur non-root pour sécurité
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Exposer le port
EXPOSE 5000

# Entrypoint
ENTRYPOINT ["python"]
CMD ["app.py"]
