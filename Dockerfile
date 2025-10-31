FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends nginx \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x start.sh

ENV DATABASE_PATH=/data/movimientos.db \
    UVICORN_HOST=0.0.0.0 \
    UVICORN_PORT=8000 \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8800

COPY nginx/default.conf /etc/nginx/conf.d/default.conf
RUN rm -f /etc/nginx/sites-enabled/default

EXPOSE 80

CMD ["bash", "/app/start.sh"]
