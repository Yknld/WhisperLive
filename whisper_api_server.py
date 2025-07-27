#!/usr/bin/env python3
import os
import tempfile
import whisper
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load Whisper model (use medium for better accuracy)
MODEL_SIZE = os.environ.get('WHISPER_MODEL', 'medium')
logger.info(f"Loading Whisper model: {MODEL_SIZE}")
model = whisper.load_model(MODEL_SIZE)
logger.info("Whisper model loaded successfully")

# Supported audio formats
ALLOWED_EXTENSIONS = {
    'wav', 'mp3', 'm4a', 'flac', 'aac', 'ogg', 'wma', 'mp4'
}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "model": MODEL_SIZE,
        "service": "whisper-api"
    })

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    """Transcribe uploaded audio file"""
    try:
        # Check if file is present
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        file = request.files['audio']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Unsupported file format'}), 400
        
        # Get optional parameters
        language = request.form.get('language', 'en')
        temperature = float(request.form.get('temperature', 0.0))
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.audio') as temp_file:
            file.save(temp_file.name)
            temp_filename = temp_file.name
        
        try:
            # Transcribe with Whisper
            logger.info(f"Transcribing audio file: {file.filename}")
            result = model.transcribe(
                temp_filename,
                language=language,
                temperature=temperature,
                no_speech_threshold=0.8,  # Reduce hallucinations
                fp16=False  # Disable for CPU compatibility
            )
            
            # Return transcription result
            response = {
                'text': result['text'].strip(),
                'language': result['language'],
                'segments': result['segments'],
                'model': MODEL_SIZE
            }
            
            logger.info(f"Transcription completed: {len(result['text'])} characters")
            return jsonify(response)
            
        finally:
            # Clean up temporary file
            os.unlink(temp_filename)
            
    except Exception as e:
        logger.error(f"Transcription error: {str(e)}")
        return jsonify({'error': f'Transcription failed: {str(e)}'}), 500

@app.route('/', methods=['GET'])
def index():
    """Root endpoint with API information"""
    return jsonify({
        "service": "Whisper Transcription API",
        "model": MODEL_SIZE,
        "endpoints": {
            "health": "/health",
            "transcribe": "/transcribe (POST with 'audio' file)"
        },
        "supported_formats": list(ALLOWED_EXTENSIONS)
    })

if __name__ == '__main__':
    # Only run the development server when called directly (not via Gunicorn)
    port = int(os.environ.get('PORT', 8000))
    logger.info(f"Starting Whisper API server on port {port}")
    logger.warning("Using development server - use Gunicorn for production!")
    app.run(host='0.0.0.0', port=port, debug=False) 