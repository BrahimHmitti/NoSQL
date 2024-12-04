import os
import time
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from pymongo import MongoClient, errors
from pymongo.errors import ConnectionFailure
import google.generativeai as genai
from pythonjsonlogger import jsonlogger

# Enhanced logging setup
logger = logging.getLogger(__name__)
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    '%(asctime)s %(levelname)s %(message)s',
    timestamp=True
)
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

app = Flask(__name__)

# Environment configuration with fallbacks
api_key = os.getenv('GOOGLE_API_KEY')
mongo_uri = os.getenv('MONGO_URI')
db_name = os.getenv('DB_NAME', 'corruption_db')
collection_name = os.getenv('COLLECTION_NAME', 'analyses')

# Global variables for services
mongo_client = None
db = None
analyses = None
model = None

def init_mongodb():
    """Initialize MongoDB connection with shorter timeouts"""
    global mongo_client, db, analyses
    try:
        mongo_client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=2000,  # Réduit à 2 secondes
            connectTimeoutMS=2000,
            socketTimeoutMS=2000
        )
        mongo_client.server_info()
        db = mongo_client[db_name]
        analyses = db[collection_name]
        logger.info("MongoDB connection successful")
        return True
    except Exception as e:
        logger.error(f"MongoDB connection failed: {str(e)}")
        return False

def init_gemini():
    """Initialize Gemini model"""
    global model
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 2048,
                "top_p": 0.95,
                "top_k": 40
            }
        )
        # Test model
        test_response = model.generate_content("test")
        if test_response and test_response.text:
            logger.info("Gemini model initialized successfully")
            return True
    except Exception as e:
        logger.error(f"Gemini initialization failed: {str(e)}")
        return False

# Initialize services
if not init_mongodb():
    logger.warning("Starting without MongoDB connection")
if not init_gemini():
    logger.warning("Starting without Gemini model")

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    status = {
        'timestamp': datetime.utcnow().isoformat(),
        'mongodb_connected': False,
        'gemini_available': False
    }
    
    try:
        if mongo_client:
            mongo_client.server_info()
            status['mongodb_connected'] = True
    except Exception as e:
        status['mongodb_error'] = str(e)

    try:
        if model:
            test_response = model.generate_content("test")
            status['gemini_available'] = bool(test_response and test_response.text)
    except Exception as e:
        status['gemini_error'] = str(e)

    status['healthy'] = all([status['mongodb_connected'], status['gemini_available']])
    return jsonify(status), 200 if status['healthy'] else 503

@app.route('/analyser', methods=['POST'])
def analyser():
    request_id = f"req_{int(time.time())}"
    logger.info(f"[{request_id}] Analysis request received")

    try:

    # Get form data first
        data = {
        'pays': request.form['pays'],
        'ville': request.form['ville'],
        'poste': request.form['poste'],
        'salaire': request.form['salaire'],
        'bien': request.form['bien'],
        'autres_revenus': request.form.get('autres_revenus', 'aucun'),
    }
    

        prompt = f"""
Agissez comme un expert en détection de corruption et d'anomalies financières. Analysez les données suivantes et fournissez :

1. Un **pourcentage de risque de corruption** basé sur les informations fournies (X%).
2. Une **explication concise** en 2-3 phrases, détaillant les éléments spécifiques qui contribuent à ce score de suspicion.
3. **Contexte supplémentaire** : Prenez en compte les facteurs régionaux comme les salaires moyens, le coût de la vie et les valeurs immobilières pour établir une comparaison avec la situation financière de la personne.
4. **Ne retournez jamais "N/A"**, chaque analyse doit être complète, même si le risque de corruption est faible. 

**Données à analyser** :
- **Pays/Ville** : {data['pays']}, {data['ville']}
- **Poste** : {data['poste']}
- **Salaire mensuel brut** : {data['salaire']}
- **Bien principal** (type et valeur estimée) : {data['bien']}
- **Autres revenus** : {data['autres_revenus']}

### **Contexte spécifique** :
- Comparez le salaire et la valeur du bien avec les moyennes de {data['ville']}, {data['pays']}, en tenant compte des écarts potentiels.
- Analysez le rôle de {data['poste']} pour déterminer s'il donne un accès privilégié à des ressources financières ou s'il peut faciliter des comportements corrompus.
- Prenez en compte la situation économique locale, comme le coût de la vie et la capacité d'acquisition d'un bien dans cette région.

**Format de sortie** :
1. **Pourcentage de suspicion de corruption** : X%
2. **Analyse concise** : 
   - Facteur 1 : {{Explication de la différence entre le salaire et le bien, ou d'autres éléments révélateurs de risque.}}
   - Facteur 2 : {{Explication du rôle professionnel et de l'accès aux ressources financières.}}
3. **Contexte local** : {{Brève analyse des normes locales concernant le salaire, le coût de la vie et l'accessibilité des biens immobiliers.}}
4. **Recommandations** : {{S'il y a lieu, suggérer des étapes supplémentaires pour une enquête plus approfondie.}}

Assurez-vous de ne pas retourner "N/A" et fournissez une analyse complète même pour des résultats faibles ou modérés de suspicion et ne mit pas du texte en gras.
"""
        logger.info(f"[{request_id}] Generating analysis...")
        response = model.generate_content(prompt)
        
        return jsonify({
            'analysis': response.text
        })

    except Exception as e:
        logger.error(f"[{request_id}] Error: {str(e)}")
        return jsonify({
            'error': str(e)
        }), 500
if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)