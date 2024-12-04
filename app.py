import os
import logging
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
import google.generativeai as genai

# Configuration du journal
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration à partir des variables d'environnement
api_key = os.getenv('GOOGLE_API_KEY')
mongo_uri = os.getenv('MONGO_URI')

try:
    # Configuration de MongoDB
    mongo_client = MongoClient(mongo_uri)
    db = mongo_client['corruption_db']
    analyses = db['analyses']
    logger.info("Connexion à MongoDB réussie.")

    # Configuration de Gemini
    genai.configure(api_key=api_key)
    generation_config = {
        "temperature": 0.7,
        "max_output_tokens": 2048,
        "top_p": 0.95,
        "top_k": 40
    }

    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
    )
    logger.info("Configuration de Gemini réussie.")

except Exception as e:
    logger.error(f"Erreur lors de l'initialisation : {str(e)}")
    raise

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyser', methods=['POST'])
def analyser():
    try:
        # Récupérer les données du formulaire
        pays = request.form['pays']
        ville = request.form['ville']
        poste = request.form['poste']
        salaire = request.form['salaire']
        bien = request.form['bien']
        autres_revenus = request.form.get('autres_revenus', 'aucun')

        logger.info(f"Données reçues : Pays={pays}, Ville={ville}, Poste={poste}, Salaire={salaire}, Bien={bien}, Autres revenus={autres_revenus}")

        # Construire le prompt
        prompt = "donne moi une citation"

        # Générer l'analyse
        logger.info("Génération de l'analyse en cours...")
        response = model.generate_content(prompt)
        
        if not response:
            raise ValueError("Pas de réponse du modèle")
        
        texte_reponse = response.text
        if not texte_reponse:
            raise ValueError("Réponse vide du modèle")
            
        logger.info("Génération terminée.")

        # Enregistrement dans MongoDB
        analyses.insert_one({
            'input': {
                'pays': pays,
                'ville': ville,
                'poste': poste,
                'salaire': salaire,
                'bien': bien,
                'autres_revenus': autres_revenus
            },
            'output': {
                'texte_reponse': texte_reponse
            }
        })
        logger.info("Analyse enregistrée dans MongoDB.")

        return jsonify({
            'texte_reponse': texte_reponse
        })

    except Exception as e:
        logger.error(f"Erreur lors de l'analyse : {str(e)}")
        return jsonify({
            'error': 'Une erreur est survenue lors de l\'analyse.',
            'details': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8080)), debug=True)
