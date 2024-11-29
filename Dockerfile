FROM python:3.9-slim

# Install system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    apt-utils \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Healthcheck simple
HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost:${PORT}/ || exit 1

EXPOSE 8080

# Configuration gunicorn sans timeout
CMD ["gunicorn", "--bind", ":8080", "app:app", "--workers", "1", "--threads", "8"]