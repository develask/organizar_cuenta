FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_PATH=/data/movimientos.db \
    APP_PORT=8000 \
    MCP_TRANSPORT=sse \
    MCP_PORT=8800 \
    MCP_ALLOWED_ORIGINS=*

WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

VOLUME ["/data"]

EXPOSE 8000 8800

CMD ["python", "run_services.py"]
