import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
import google.generativeai as genai
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Startup logging
logger.info("Application starting...")
api_key = os.getenv('GOOGLE_API_KEY')
mongo_uri = os.getenv('MONGO_URI')
logger.info(f"Environment variables loaded: API_KEY={'*' * len(api_key) if api_key else 'NOT SET'}")

try:
    # MongoDB setup with connection check
    logger.info("Attempting MongoDB connection...")
    mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    mongo_client.server_info()  # Test connection
    db = mongo_client['corruption_db']
    analyses = db['analyses']
    logger.info("MongoDB connection successful")

    # Gemini configuration
    logger.info("Configuring Gemini model...")
    genai.configure(api_key=api_key)
    generation_config = {
        "temperature": 0.7,
        "max_output_tokens": 2048,
        "top_p": 0.95,
        "top_k": 40
    }
    model = genai.GenerativeModel(model_name="gemini-1.5-pro")
    logger.info("Gemini model configured successfully")

except Exception as e:
    logger.critical(f"Initialization failed: {str(e)}")
    raise

@app.route('/health')
def health_check():
    try:
        # Check MongoDB
        mongo_client.server_info()
        # Check Gemini (lightweight test)
        model.generate_content("test")
        return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

@app.route('/')
def index():
    logger.info(f"Index page requested from IP: {request.remote_addr}")
    return render_template('index.html')

@app.route('/analyser', methods=['POST'])
def analyser():
    start_time = time.time()
    request_id = f"req_{int(start_time)}"
    logger.info(f"[{request_id}] New analysis request received from IP: {request.remote_addr}")

    try:
        # Form data validation
        required_fields = ['pays', 'ville', 'poste', 'salaire', 'bien']
        form_data = {field: request.form.get(field) for field in required_fields}
        autres_revenus = request.form.get('autres_revenus', 'aucun')
        
        if not all(form_data.values()):
            missing = [f for f in required_fields if not form_data[f]]
            logger.warning(f"[{request_id}] Missing required fields: {missing}")
            return jsonify({'error': 'Missing required fields', 'missing': missing}), 400

        logger.info(f"[{request_id}] Processing analysis for {form_data['ville']}, {form_data['pays']}")

        # Generate analysis
        try:
            logger.info(f"[{request_id}] Generating content with Gemini...")
            prompt = f"Analyze potential corruption indicators for a {form_data['poste']} in {form_data['ville']}, {form_data['pays']} with salary {form_data['salaire']} and assets {form_data['bien']}"
            response = model.generate_content(prompt)
            
            if not response or not response.text:
                raise ValueError("Empty response from Gemini")
                
            texte_reponse = response.text
            logger.info(f"[{request_id}] Content generated successfully")

        except Exception as e:
            logger.error(f"[{request_id}] Gemini generation failed: {str(e)}")
            raise

        # MongoDB storage
        try:
            document = {
                'request_id': request_id,
                'timestamp': datetime.now(),
                'client_ip': request.remote_addr,
                'input': {**form_data, 'autres_revenus': autres_revenus},
                'output': texte_reponse,
                'processing_time': time.time() - start_time
            }
            analyses.insert_one(document)
            logger.info(f"[{request_id}] Analysis saved to MongoDB")

        except Exception as e:
            logger.error(f"[{request_id}] MongoDB save failed: {str(e)}")
            raise

        processing_time = time.time() - start_time
        logger.info(f"[{request_id}] Request completed in {processing_time:.2f}s")

        return jsonify({
            'request_id': request_id,
            'texte_reponse': texte_reponse,
            'processing_time': processing_time
        })

    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"[{request_id}] Request failed after {processing_time:.2f}s: {str(e)}")
        return jsonify({
            'error': 'Analysis failed',
            'request_id': request_id,
            'details': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    logger.info(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)