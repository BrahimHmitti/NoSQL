# Stage 1: Build
FROM python:3.9-slim as builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.9-slim

WORKDIR /app

# Copier uniquement les dépendances installées
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages

# Copier les fichiers de l'application
COPY . .
COPY .env .env

EXPOSE 5000

CMD ["python", "app.py"]