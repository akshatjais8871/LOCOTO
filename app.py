# from flask import Flask, render_template, request, jsonify, send_file
# import os
# import google.generativeai as genai
# from io import BytesIO
# from PIL import Image
# from gtts import gTTS
# from langdetect import detect
# from deep_translator import GoogleTranslator
# import tempfile
# from flask_cors import CORS
# import logging
# import base64

# app = Flask(__name__)
# CORS(app)

# # Set up logging
# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger(__name__)

# app.config['UPLOAD_FOLDER'] = 'static/uploads'
# app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# if not os.path.exists(app.config['UPLOAD_FOLDER']):
#     os.makedirs(app.config['UPLOAD_FOLDER'])

# # Configure Gemini API
# genai.configure(api_key="AIzaSyD4i5vCeP-dl8QRDetOdVc5gpjRe7SNe5o")

# generation_config = {
#     "temperature": 0.4,
#     "top_p": 0.8,
#     "top_k": 40,
#     "max_output_tokens": 2048,
# }

# # Define the available languages
# indian_languages = {
#     "Hindi": "hi",
#     "English": "en",
#     "Marathi": "mr",
#     "Telugu": "te",
#     "Tamil": "ta",
#     "Bengali": "bn",
#     "Gujarati": "gu",
#     "Kannada": "kn",
#     "Malayalam": "ml",
#     "Odia": "or",
#     "Punjabi": "pa",
#     "Urdu": "ur"
# }

# def upload_to_gemini(image_file):
#     try:
#         logger.debug("Starting upload_to_gemini function")
#         logger.debug(f"Image file type: {type(image_file)}")
        
#         # Save the uploaded file temporarily
#         temp_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_image.jpg')
#         image_file.save(temp_path)
        
#         # Open with PIL and convert to base64
#         with Image.open(temp_path) as image:
#             logger.debug(f"Image opened successfully: {image.format}, size: {image.size}")
            
#             # Convert to RGB if necessary
#             if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
#                 logger.debug("Converting image to RGB")
#                 image = image.convert('RGB')
            
#             # Save to bytes
#             image_bytes = BytesIO()
#             image.save(image_bytes, format='JPEG', quality=95)
#             image_bytes.seek(0)
            
#             # Convert to base64
#             image_base64 = base64.b64encode(image_bytes.getvalue()).decode('utf-8')
#             logger.debug("Image converted to base64 successfully")
            
#             # Clean up temp file
#             os.remove(temp_path)
            
#             # Create Gemini-compatible parts
#             return [{"mime_type": "image/jpeg", "data": image_base64}]
            
#     except Exception as e:
#         logger.error(f"Error in upload_to_gemini: {str(e)}")
#         logger.exception("Detailed error:")
#         return None

# def detect_language(text):
#     try:
#         return detect(text)
#     except Exception as e:
#         return None

# def translate_text(text, dest_language):
#     try:
#         return GoogleTranslator(source='auto', target=dest_language).translate(text)
#     except Exception as e:
#         return None

# def text_to_speech(text, language):
#     try:
#         tts = gTTS(text=text, lang=language, slow=False)
#         temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
#         tts.save(temp_file.name)
#         return temp_file.name
#     except Exception as e:
#         return None

# @app.route('/')
# def index():
#     return render_template('index.html', languages=indian_languages)

# @app.route('/process', methods=['POST'])
# def process_image():
#     logger.debug("Request received")
#     logger.debug("Files in request: %s", list(request.files.keys()))
#     logger.debug("Form data in request: %s", list(request.form.keys()))
    
#     try:
#         if 'file' not in request.files:
#             logger.error("No file part in the request")
#             return jsonify({'error': 'No file part'}), 400
        
#         file = request.files['file']
#         selected_language = request.form.get('language')
        
#         logger.debug(f"File name: {file.filename}")
#         logger.debug(f"Selected language: {selected_language}")
        
#         if not file or file.filename == '':
#             logger.error("No file selected")
#             return jsonify({'error': 'No file selected'}), 400
            
#         if not selected_language or selected_language not in indian_languages:
#             logger.error("Invalid language selection")
#             return jsonify({'error': f'Invalid language selection: {selected_language}'}), 400

#         # Process with Gemini
#         image_parts = upload_to_gemini(file)
#         if not image_parts:
#             logger.error("Failed to process image")
#             return jsonify({'error': 'Failed to process image'}), 400

#         # Create a new model instance for each request with the new model name
#         model = genai.GenerativeModel('gemini-1.5-flash', generation_config=generation_config)
        
#         # First detect text from image
#         detect_prompt = "Extract and return only the text from this image. If there are multiple lines, preserve the line breaks."
#         detect_response = model.generate_content([detect_prompt] + image_parts)
#         detected_text = detect_response.text.strip()
#         logger.debug(f"Detected text: {detected_text}")
        
#         if not detected_text:
#             logger.error("No text detected in image")
#             return jsonify({'error': 'No text detected in image'}), 400
            
#         # Detect language
#         detected_lang = detect_language(detected_text) or "unknown"
#         logger.debug(f"Detected language: {detected_lang}")

#         # Translate text
#         translate_prompt = f"Translate this text to {selected_language}. Return only the translated text, nothing else."
#         translate_response = model.generate_content([translate_prompt, detected_text])
#         translated_text = translate_response.text.strip()
#         logger.debug(f"Translated text: {translated_text}")

#         # Generate audio
#         target_language_code = indian_languages[selected_language]
#         audio_file = text_to_speech(translated_text, target_language_code)
        
#         if not audio_file:
#             logger.error("Failed to generate audio")
#             return jsonify({'error': 'Failed to generate audio'}), 400

#         # Save audio file
#         temp_audio_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_audio.mp3')
#         with open(audio_file, 'rb') as src, open(temp_audio_path, 'wb') as dst:
#             dst.write(src.read())
#         os.remove(audio_file)

#         return jsonify({
#             'detected_language': detected_lang,
#             'translated_text': translated_text,
#             'audio_path': 'static/uploads/temp_audio.mp3'
#         })

#     except Exception as e:
#         logger.exception("Error processing request")
#         return jsonify({'error': str(e)}), 500

# @app.route('/download_audio')
# def download_audio():
#     audio_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_audio.mp3')
#     if (os.path.exists(audio_path)):
#         return send_file(audio_path, as_attachment=True, download_name='translated_audio.mp3')
#     return jsonify({'error': 'Audio file not found'}), 404

# if __name__ == '__main__':
#     app.run(debug=True)
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import bcrypt

from flask import Flask, render_template, request, jsonify, send_file
import os
import google.generativeai as genai
from io import BytesIO
from PIL import Image
from gtts import gTTS
from langdetect import detect
from deep_translator import GoogleTranslator
import tempfile
from flask_cors import CORS
import logging
import base64
app = Flask(__name__)
CORS(app)


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SECRET_KEY'] = 'secret'

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))
    
with app.app_context():
    db.create_all()


    

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first() or User.query.filter_by(email=username).first()
        if user and user.check_password(password):
            return redirect(url_for('home'))
        return render_template('login.html', error='Invalid username or password')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        conform_password = request.form['confirm-password']
        if password != conform_password:
            return render_template('register.html', error='Passwords do not match')
        try:
            if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
                return render_template('register.html', error='Username already exists')
        except:
            pass
        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/aboutus')
def aboutus():
    return render_template('aboutus.html')

@app.route('/feedback')
def feedback():
    return render_template('feedback.html')

# @app.route('/contactus')
# def contactus():
#     return render_template('contactus.html')



#FOR UPLOAADING

app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16MB max file size

# Creates the uploads folder if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Configure Gemini API
genai.configure(api_key="AIzaSyD4i5vCeP-dl8QRDetOdVc5gpjRe7SNe5o")
generation_config = {
"temperature": 0.4,
"top_p": 0.8,
"top_k": 40,
"max_output_tokens": 2048,
}

# Define the available languages
indian_languages = {
"Hindi": "hi",
"English": "en",
"Marathi": "mr",
"Telugu": "te",
"Tamil": "ta",
"Bengali": "bn",
"Gujarati": "gu",
"Kannada": "kn",
"Malayalam": "ml",
"Odia": "or",
"Punjabi": "pa",
"Urdu": "ur"
}

def upload_to_gemini(image_file):
    try:
        logger.debug("Starting upload_to_gemini function")
        logger.debug(f"Image file type: {type(image_file)}")
# Save the uploaded file temporarily
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_image.jpg')
        image_file.save(temp_path)
# Open with PIL and convert to base64
        with Image.open(temp_path) as image:
            logger.debug(f"Image opened successfully: {image.format}, size: {image.size}")
# Convert to RGB if necessary
        if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in
        image.info):
            logger.debug("Converting image to RGB")
            image = image.convert('RGB')
# Save to bytes
        image_bytes = BytesIO()
        image.save(image_bytes, format='JPEG', quality=95)
        image_bytes.seek(0)
# Convert to base64
        image_base64 = base64.b64encode(image_bytes.getvalue()).decode('utf-8')
        logger.debug("Image converted to base64 successfully")
# Clean up temp file
        os.remove(temp_path)
# Create Gemini-compatible partsreturn [{"mime_type": "image/jpeg", "data": image_base64}]
    except Exception as e:
        logger.error(f"Error in upload_to_gemini: {str(e)}")
        logger.exception("Detailed error:")
    return None

#detect_language
def detect_language(text):
    try:
        return detect(text)
    except Exception as e:
        return None

#translate_text
def translate_text(text, dest_language):
    try:
        return GoogleTranslator(source='auto', target=dest_language).translate(text)
    except Exception as e:
        return None
    
#text_to_speech
def text_to_speech(text, language):
    try:
        tts = gTTS(text=text, lang=language, slow=False)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tts.save(temp_file.name)
        return temp_file.name
    except Exception as e:
        return None    
    

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(f'uploads/{filename}')
            return redirect(url_for('home'))
    return render_template('upload.html')


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)

