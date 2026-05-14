FROM python:3.11-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

EXPOSE 8000

# src/ is mounted as a volume in dev mode via docker-compose
# Production: copy src explicitly and use `uv run fastapi run`
CMD ["uv", "run", "fastapi", "dev", "src/main.py", "--host", "0.0.0.0", "--port", "8000"]
