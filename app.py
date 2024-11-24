from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
import redis
import random

app = Flask(__name__)

# Connexion à MongoDB
mongo_client = MongoClient('mongodb://mongo:27017/')
db = mongo_client['citations_db']
citations_collection = db['citations']

# Connexion à Redis
redis_client = redis.Redis(host='redis', port=6379, db=0)

# Éléments pour générer les citations
debuts = [
    "La clé du {0} est",
    "Pour atteindre le {0}, il faut",
    "Le secret du {0} réside dans",
    "Le chemin vers le {0} commence par",
]

milieux = [
    "la persévérance et",
    "l'imagination combinée à",
    "la passion mélangée à",
    "la détermination associée à",
]

fins = [
    "l'action constante.",
    "une vision claire.",
    "l'apprentissage continu.",
    "l'adaptabilité face aux défis.",
]

categories = ["Succès", "Bonheur", "Créativité", "Sagesse"]

@app.route('/')
def index():
    return render_template('index.html', categories=categories)

@app.route('/generer_citation', methods=['POST'])
def generer_citation():
    nom = request.form['nom']
    categorie = request.form['categorie']
    
    debut = random.choice(debuts).format(categorie.lower())
    milieu = random.choice(milieux)
    fin = random.choice(fins)
    
    citation = f"{debut} {milieu} {fin}"
    citation_personnalisee = f"Cher(e) {nom}, {citation}"
    
    # Sauvegarder dans MongoDB
    citations_collection.insert_one({
        'nom': nom,
        'categorie': categorie,
        'citation': citation_personnalisee
    })
    
    # Incrémenter le compteur dans Redis
    redis_client.incr('total_citations')
    
    return jsonify({'citation': citation_personnalisee})

@app.route('/statistiques')
def statistiques():
    total_citations = int(redis_client.get('total_citations') or 0)
    return jsonify({'total_citations': total_citations})

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

