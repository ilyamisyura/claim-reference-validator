FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_INSTALL_DIR=/usr/local/bin

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        build-essential \
        libgl1 \
        libglib2.0-0 \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates

ADD https://astral.sh/uv/install.sh /uv-installer.sh

RUN sh /uv-installer.sh && rm /uv-installer.sh

ENV PATH="/root/.local/bin/:$PATH"

WORKDIR /app

# includes dev deps for stage)
FROM base AS deps
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# Development image
FROM deps AS dev
ENV PATH="/app/.venv/bin:${PATH}"
COPY . .
EXPOSE 8000
CMD ["fastapi", "dev", "--host", "0.0.0.0", "app/main.py"]

# Build production dependencies (no dev deps)
FROM base AS build
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev \
    && find .venv -name "__pycache__" -type d -exec rm -rf {} +

# Production runtime
FROM python:3.13-slim AS prod
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:${PATH}"

# Install runtime dependencies for OpenCV and Docling
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=build /app/.venv /app/.venv
COPY . .

EXPOSE 8000
CMD ["fastapi", "run", "--proxy-headers"]
