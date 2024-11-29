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
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel(
  model_name="learnlm-1.5-pro-experimental",
  generation_config=generation_config,
)

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
Act as an expert in financial fraud detection and corruption risk assessment. Analyze the following data and give:

1. A **corruption suspicion percentage** based on the provided data.
2. A **brief analysis** explaining how the given factors contribute to the suspicion.
3. **Contextual insights** (e.g., salary norms, cost of living, and typical asset values in {ville}, {pays}).
4. **Recommendations** for further investigation if needed.

**Data:**
- Country and City: {pays}, {ville}
- Current Position: {poste}
- Monthly Gross Salary: {salaire}
- Main Asset (type and estimated value): {bien}
- Other Known Income Sources: {autres_revenus}

**Context:**
- Compare the individual's salary and asset value to local norms in {ville}, {pays}.
- Assess the individual's position (e.g., is {poste} a high-influence role that could lead to financial misconduct?).
- Consider the cost of living in {ville} and how it aligns with the individual's financial profile.

**Output format:**
1. Corruption Suspicion Percentage: X%
2. Analysis:
   - Factor 1: {{Explanation on salary vs. asset discrepancy or other red flags.}}
   - Factor 2: {{Explanation on the individual’s role and potential access to resources.}}
3. Contextual Insights: {{Brief context on salary averages, cost of living, and asset affordability in the region.}}
4. Recommendations: {{If applicable, suggest further investigative steps.}}

Make sure to **avoid returning "N/A"**, and give a clear analysis of potential corruption risks based on the data provided. Output should be in French.
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