FROM python:3.9-slim

# Install system packages properly
RUN apt-get update && apt-get install -y --no-install-recommends \
    apt-utils \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost:${PORT}/ || exit 1

CMD exec gunicorn --bind :$PORT app:app --workers 1 --threads 8