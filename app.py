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
model = genai.GenerativeModel("learnlm-1.5-pro-experimental")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyser', methods=['POST'])
def analyser():
    # Récupérer les données du formulaire
    pays = request.form['pays']
    ville = request.form['ville']
    poste = request.form['poste']
    salaire = request.form['salaire']
    bien = request.form['bien']
    autres_revenus = request.form.get('autres_revenus', 'aucun')
    
# Build the prompt
    prompt = f"""
Act as an expert in financial fraud detection and corruption risk assessment. Analyze the following data about an individual and provide:
1. A corruption suspicion score (percentage) based on the provided data.
2. A detailed analysis explaining the factors that contribute to the suspicion, considering the context and the data provided.
3. Context-specific insights (e.g., salary averages, cost of living, asset norms in the individual's region, and any potential red flags).
4. Recommendations for further investigation if necessary, based on identified inconsistencies or areas of concern.

**Data:**
- Country and City: {pays}, {ville}
- Current Position: {poste}
- Monthly Gross Salary: {salaire}
- Main Asset (type and estimated value): {bien}
- Other Known Income Sources: {autres_revenus}

**Context:**
- Use regional economic indicators like average salary, cost of living, and asset affordability in {pays}/{ville} to assess the consistency of the individual's financial profile.
- Consider the level of influence and access to resources associated with the position of {poste}. Is this position associated with high levels of financial discretion or access to company funds?
- Compare the individual's salary and asset to the average figures in {pays}/{ville} to check for anomalies or signs of potential illicit wealth accumulation.

Output format:
1. Corruption Suspicion Percentage: X%
2. Detailed Analysis:
   - Factor 1: {{Explanation of how this factor contributes to suspicion (e.g., salary vs. asset discrepancy)}}
   - Factor 2: {{Explanation of how this factor contributes to suspicion (e.g., position's access to financial resources)}}
   - Factor 3: {{Any other relevant factor (e.g., unreported income sources)}}
3. Contextual Insights: {{Provide detailed analysis based on local economic context, such as typical salaries, cost of living, and the market for assets in the region.}}
4. Recommendations: {{Suggest further investigative steps (e.g., obtaining more detailed financial documents, reviewing company transactions, etc.)}}

The output should be in French and tailored to the specific data provided. Ensure that the analysis takes into account both financial indicators and the individual's professional context. dont ever return a Score de suspicion :
N/A.
"""

    # Generate analysis with Gemini
    response = model.generate_content(prompt)

    # Parse the response
    lines = response.text.split('\n')
    score = next((line for line in lines if "Pourcentage" in line), "N/A")
    analyse = "\n".join(line for line in lines if "Factor" in line or "Facteur" in line)
    contexte = next((line for line in lines if "Contextual" in line or "Contexte" in line), "N/A")
    recommandations = next((line for line in lines if "Recommendations" in line or "Recommandations" in line), "N/A")

    return jsonify({
        'score': score,
        'analyse': analyse,
        'contexte': contexte,
        'recommandations': recommandations
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)