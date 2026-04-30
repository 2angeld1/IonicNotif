# ============================================
# 🧠 Dockerfile para Caitlyn AI Microservice
# Optimizado con uv + Playwright + Gemini
# ============================================

FROM python:3.12-slim-bookworm

WORKDIR /app

# Instalar uv (gestor de paquetes ultrarrápido para Python)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Instalar TODAS las dependencias del sistema necesarias:
# - libgomp1: requerido por scikit-learn/numpy (OpenMP)
# - libgl1 + libglib2.0: requerido por OpenCV
# - libnss3, libgbm1, etc.: requerido por Playwright/Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de dependencias primero (cache de Docker)
COPY pyproject.toml uv.lock ./

# Instalar dependencias Python con uv (ultrarrápido)
RUN uv sync --frozen --no-install-project

# Instalar Chromium para Playwright
RUN uv run playwright install chromium && uv run playwright install-deps chromium

# Copiar el código de la aplicación
COPY . .

# Configurar el PATH para usar el entorno virtual
ENV PATH="/app/.venv/bin:$PATH"

# Exponer el puerto (Railway lo sobreescribe con $PORT)
EXPOSE 8000

# Usar start.sh que entrena la IA y luego arranca el servidor
RUN chmod +x start.sh
CMD ["./start.sh"]
