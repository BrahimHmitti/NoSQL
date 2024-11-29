# deploy.sh
#!/bin/bash

echo "🚀 Déploiement sur Cloud Run..."

# Construction de l'image
gcloud builds submit --tag gcr.io/serverless-corruption/corruption-detector

# Déploiement avec secrets
gcloud run deploy corruption-detector \
    --image gcr.io/serverless-corruption/corruption-detector \
    --platform managed \
    --region europe-west1 \
    --allow-unauthenticated \
    --update-secrets=GOOGLE_API_KEY=google-api-key:latest,MONGO_URI=mongo-uri:latest

echo "✅ Déploiement terminé"