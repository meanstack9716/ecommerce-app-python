import os
import base64
import uuid
from werkzeug.utils import secure_filename
from flask import current_app, request, url_for
from .validation import validate_required_fields

# Allowed extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# In-memory image store (replace with DB or Redis for production)
image_store = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_image(image):
    if image and not allowed_file(image.filename):
        return None, 'Invalid image file type'

    if image:
        # Create upload folder if it doesn't exist
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Generate a unique filename
        ext = image.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        
        # Save to filesystem
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        image.save(filepath)
        
        # Return relative URL
        return url_for('static', filename=f'uploads/{filename}', _external=True), None

    return None, None


def validate_fields(data, required_fields):
    is_valid, validation_errors = validate_required_fields(data, required_fields)
    if not is_valid:
        return False, validation_errors
    return True, None
