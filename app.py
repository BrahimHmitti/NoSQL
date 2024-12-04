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
    """Initialize MongoDB connection with retry logic"""
    global mongo_client, db, analyses
    max_retries = 3
    retry_delay = 1

    for attempt in range(max_retries):
        try:
            mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            # Test connection
            mongo_client.server_info()
            db = mongo_client[db_name]
            analyses = db[collection_name]
            logger.info("MongoDB connection successful")
            return True
        except Exception as e:
            logger.warning(f"MongoDB connection attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                logger.error("All MongoDB connection attempts failed")
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
        # Validate required fields
        required_fields = ['pays', 'ville', 'poste', 'salaire', 'bien']
        form_data = {field: request.form.get(field) for field in required_fields}
        missing_fields = [f for f in required_fields if not form_data.get(f)]
        
        if missing_fields:
            logger.warning(f"[{request_id}] Missing required fields: {missing_fields}")
            return jsonify({
                'error': 'Missing required fields',
                'missing': missing_fields,
                'request_id': request_id
            }), 400

        # Include optional fields
        form_data['autres_revenus'] = request.form.get('autres_revenus', 'aucun')
        
        # Generate analysis
        if not model:
            raise Exception("Gemini model not available")

        prompt = f"Analyze corruption potential for {form_data['poste']} in {form_data['ville']}, {form_data['pays']} " \
                f"with salary {form_data['salaire']} and assets {form_data['bien']}"
        
        logger.info(f"[{request_id}] Generating analysis...")
        response = model.generate_content(prompt)
        
        if not response or not response.text:
            raise ValueError("Empty response from Gemini")
        
        analysis_text = response.text
        logger.info(f"[{request_id}] Analysis generated successfully")

        # Save to MongoDB if available
        if analyses:
            try:
                result = analyses.insert_one({
                    'request_id': request_id,
                    'timestamp': datetime.utcnow(),
                    'input': form_data,
                    'output': analysis_text
                })
                logger.info(f"[{request_id}] Analysis saved to MongoDB")
            except Exception as db_error:
                logger.error(f"[{request_id}] MongoDB save failed: {str(db_error)}")
                # Continue with response even if save fails
        else:
            logger.warning(f"[{request_id}] MongoDB not available, skipping save")

        return jsonify({
            'analysis': analysis_text,
            'request_id': request_id,
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error(f"[{request_id}] Error processing request: {str(e)}")
        return jsonify({
            'error': 'Analysis failed',
            'details': str(e),
            'request_id': request_id
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)