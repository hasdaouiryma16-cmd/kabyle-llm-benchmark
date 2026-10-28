FROM python:3.12-slim

# uv : gestionnaire de dépendances rapide, avec fichier de verrouillage (uv.lock)
COPY --from=ghcr.io/astral-sh/uv:0.8.0 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dépendances d'abord (couche mise en cache tant que uv.lock ne change pas)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY . .

RUN useradd --create-home --uid 1000 lab && mkdir -p /app/var && chown -R lab /app
USER lab

EXPOSE 8000
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
