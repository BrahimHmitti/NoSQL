from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
import redis
import os
import google.generativeai as genai
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

# Connexion à MongoDB
mongo_client = MongoClient('mongodb://mongo:27017/')
db = mongo_client['citations_db']
citations_collection = db['citations']

# Connexion à Redis
redis_client = redis.Redis(host='redis', port=6379, db=0)

# Configuration Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash", 
    generation_config={
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 1024,
    }
)

categories = ["Succès", "Bonheur", "Créativité", "Sagesse"]

@app.route('/')
def index():
    return render_template('index.html', categories=categories)

@app.route('/generer_citation', methods=['POST'])
def generer_citation():
    nom = request.form['nom']
    categorie = request.form['categorie']
    
    # Générer citation avec Gemini
    prompt = f"Génère une citation inspirante sur le thème de '{categorie}' en français. La citation doit être courte (maximum 2 phrases)."
    chat = model.start_chat(history=[])
    response = chat.send_message(prompt)
    citation = response.text
    
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


    #