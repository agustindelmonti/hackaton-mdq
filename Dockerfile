# PolPilot x Papasud — demo público para Render: UN solo servicio, UN solo puerto.
# SOLO data-papasud/ (dataset sintético, ver README) viaja a la imagen; el
# .env local, credenciales.json y node_modules quedan afuera por
# .dockerignore Y se verifican acá adentro (el build FALLA si algo se cuela).

# --- Etapa 1: el frontend compilado (Vite) -----------------------------------
FROM node:20-slim AS front
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- Etapa 2: el runtime (Python + WeasyPrint en Linux) ----------------------
FROM python:3.12-slim
# Las libs de sistema que WeasyPrint necesita en Linux (el PDF se genera en el server)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 libpangocairo-1.0-0 libpangoft2-1.0-0 libcairo2 \
    libgdk-pixbuf-2.0-0 libffi-dev libharfbuzz0b libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ backend/
COPY data-papasud/ data-papasud/
COPY deploy/ deploy/
COPY --from=front /build/dist frontend/dist

# GUARDIA DE PRIVACIDAD: el build FALLA si un .env o credenciales llegaron a
# la imagen (defensa en profundidad sobre el .dockerignore) — incluye el
# bundle servido (frontend/dist), no solo los directorios de datos.
RUN test ! -e /app/backend/.env && \
    test ! -e /app/backend/credenciales.json && \
    test ! -e /app/data-papasud/credenciales.json && \
    if find /app -name "*.env" -o -name "credenciales.json" | grep -q .; then \
      echo "GUARDIA: archivo sensible en la imagen" && exit 1; fi && \
    echo "guardia de privacidad: OK (sin .env ni credenciales en la imagen)"

# El demo entero por env (los defaults seguros; las keys van como secret en Render)
ENV POLPILOT_TENANT=papasud \
    POLPILOT_DATA_DIR=/app/data-papasud \
    POLPILOT_CANONICAL_DIR=/app/canonical \
    POLPILOT_STATIC_DIR=/app/frontend/dist \
    POLPILOT_DEFAULT_LANG=es \
    POLPILOT_DEMO_TODAY=2026-08-22 \
    POLPILOT_DEMO_ROLE_SWITCH=1 \
    POLPILOT_DEMO_AUTOLOGIN=1 \
    POLPILOT_DEMO_MSG_CAP=35 \
    POLPILOT_DEMO_IP_CAP=60 \
    PYTHONUNBUFFERED=1

EXPOSE 8000
CMD ["python", "deploy/boot.py"]
