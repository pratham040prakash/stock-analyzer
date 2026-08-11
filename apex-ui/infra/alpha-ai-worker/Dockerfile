FROM python:3.12-slim

WORKDIR /app

COPY analyzer /app/analyzer
COPY apex-ui/infra/alpha-ai-worker/server.py /app/server.py

RUN pip install --no-cache-dir -r /app/analyzer/requirements.txt 2>/dev/null || true

ENV PORT=8080
EXPOSE 8080

CMD ["python", "/app/server.py"]
