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

# Create uploads directory with proper permissions
RUN mkdir -p uploads/agencies uploads/kyc uploads/vehicles && \
    chown -R appuser:appuser uploads

USER appuser

ENV FLASK_ENV=production

EXPOSE 8080

# Use gunicorn with proper workers and timeout for Cloud Run
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 --access-logfile - --error-logfile - run:app
