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
db = mongo_client['corruption_db']
analyses_collection = db['analyses']

# Connexion à Redis
redis_client = redis.Redis(host='redis', port=6379, db=0)



# Configuration Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("learnlm-1.5-pro-experimental") #le modele didiée à ce type de qsts.

@app.route('/')
def index():
    analysis_count = redis_client.get('analysis_count')
    count = int(analysis_count) if analysis_count else 0
    return render_template('index.html', analysis_count=count)

@app.route('/analyser', methods=['POST'])
def analyser():
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

    response = model.generate_content(prompt)
    data['analyse'] = response.text
    
    analyses_collection.insert_one(data)
    redis_client.incr('analysis_count')
    
    return jsonify({
        'analyse': response.text,
        'count': int(redis_client.get('analysis_count'))
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)