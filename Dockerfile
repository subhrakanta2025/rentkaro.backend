# Simple container for Cloud Run deployment
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Create non-root user
RUN adduser --disabled-password --gecos "" appuser

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

USER appuser

ENV FLASK_ENV=production \
    PORT=8080

EXPOSE 8080

CMD ["sh", "-c", "gunicorn -b 0.0.0.0:${PORT:-8080} run:app"]
