FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# curl is used by the docker-compose healthcheck.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic.ini .
COPY alembic ./alembic
COPY app ./app

RUN mkdir -p /app/uploads

EXPOSE 8000

# Apply migrations (retrying briefly until the database is reachable), then
# start the API. All configuration comes from environment variables
# (see docker-compose.yml / .env.example). Binds to $PORT on Render,
# defaulting to 8000 locally.
CMD ["sh", "-c", "ok=0; for i in 1 2 3 4 5 6 7 8 9 10; do if alembic upgrade head; then ok=1; break; fi; echo 'migration attempt '"$i"' failed, retrying...'; sleep 2; done; if [ \"$ok\" -eq 0 ]; then echo 'DB migrations failed after retries'; exit 1; fi; exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]