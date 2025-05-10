
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import bcrypt
import logging

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
from datetime import datetime
from functools import wraps
from flask.cli import with_appcontext
import click

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create a file handler
handler = logging.FileHandler('app.log')
handler.setLevel(logging.DEBUG)

# Create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %levelname)s - %(message)s')
handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(handler)

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SECRET_KEY'] = 'secret'

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    def __init__(self, username, email, password, is_admin=False):
        self.username = username
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        self.is_admin = is_admin

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
            session['username'] = user.username
            session['logged_in'] = True
            session['is_admin'] = user.is_admin
            user.last_login = datetime.utcnow()
            db.session.commit()
            return redirect(url_for('index'))
        return render_template('login.html', error='Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('logged_in', None)
    session.pop('is_admin', None)
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        conform_password = request.form['confirm_password']
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

# Create a reverse mapping for language codes to names
language_codes = {v: k for k, v in indian_languages.items()}

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
            if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
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
            
            # Return Gemini-compatible parts
            return [{"mime_type": "image/jpeg", "data": image_base64}]
            
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
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(f'uploads/{filename}')
            return redirect(url_for('home'))
    return render_template('upload.html')

@app.route('/process', methods=['POST'])
def process_image():
    logger.debug("Request received")
    logger.debug("Files in request: %s", list(request.files.keys()))
    logger.debug("Form data in request: %s", list(request.form.keys()))
    
    try:
        if 'file' not in request.files:
            logger.error("No file part in the request")
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        selected_language_code = request.form.get('language')
        
        logger.debug(f"File name: {file.filename}")
        logger.debug(f"Selected language code: {selected_language_code}")
        
        if not file or file.filename == '':
            logger.error("No file selected")
            return jsonify({'error': 'No file selected'}), 400
            
        if not selected_language_code or selected_language_code not in language_codes:
            logger.error("Invalid language selection")
            return jsonify({'error': f'Invalid language selection: {selected_language_code}'}), 400

        # Process with Gemini
        image_parts = upload_to_gemini(file)
        if not image_parts:
            logger.error("Failed to process image")
            return jsonify({'error': 'Failed to process image'}), 400

        # Create a new model instance for each request with the new model name
        model = genai.GenerativeModel('gemini-1.5-flash', generation_config=generation_config)
        
        # First detect text from image
        detect_prompt = "Extract and return only the text from this image. If there are multiple lines, preserve the line breaks."
        detect_response = model.generate_content([detect_prompt] + image_parts)
        detected_text = detect_response.text.strip()
        logger.debug(f"Detected text: {detected_text}")
        
        if not detected_text:
            logger.error("No text detected in image")
            return jsonify({'error': 'No text detected in image'}), 400
            
        # Detect language
        detected_lang = detect_language(detected_text) or "unknown"
        logger.debug(f"Detected language: {detected_lang}")

        # Get the language name for the translation prompt
        selected_language_name = language_codes[selected_language_code]

        # Translate text
        translate_prompt = f"Translate this text to {selected_language_name}. Return only the translated text, nothing else."
        translate_response = model.generate_content([translate_prompt, detected_text])
        translated_text = translate_response.text.strip()
        logger.debug(f"Translated text: {translated_text}")

        # Generate audio
        audio_file = text_to_speech(translated_text, selected_language_code)
        
        if not audio_file:
            logger.error("Failed to generate audio")
            return jsonify({'error': 'Failed to generate audio'}), 400

        # Save audio file
        temp_audio_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_audio.mp3')
        with open(audio_file, 'rb') as src, open(temp_audio_path, 'wb') as dst:
            dst.write(src.read())
        os.remove(audio_file)

        return jsonify({
            'detected_language': detected_lang,
            'translated_text': translated_text,
            'audio_path': 'static/uploads/temp_audio.mp3'
        })

    except Exception as e:
        logger.exception("Error processing request")
        return jsonify({'error': str(e)}), 500

@app.route('/download_audio')
def download_audio():
    audio_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_audio.mp3')
    if (os.path.exists(audio_path)):
        return send_file(audio_path, as_attachment=True, download_name='translated_audio.mp3')
    return jsonify({'error': 'Audio file not found'}), 404

@app.route('/results')
def results():
    return render_template('result.html')

# Admin middleware
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        username = session.get('username')
        user = User.query.filter_by(username=username).first()
        if not user or not user.is_admin:
            flash('Admin access required')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/users')
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/<int:user_id>/toggle_status', methods=['POST'])
@admin_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    if user.username != session.get('username'):  # Prevent admin from deactivating themselves
        user.is_active = not user.is_active
        db.session.commit()
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.username != session.get('username'):  # Prevent admin from deleting themselves
        db.session.delete(user)
        db.session.commit()
    return redirect(url_for('admin_users'))

@app.cli.command("create-admin")
@click.argument("username")
@with_appcontext
def create_admin(username):
    """Promote a user to admin status."""
    user = User.query.filter_by(username=username).first()
    if user:
        user.is_admin = True
        db.session.commit()
        click.echo(f"User {username} has been promoted to admin.")
    else:
        click.echo(f"User {username} not found.")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)

