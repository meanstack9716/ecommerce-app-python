import os
from werkzeug.utils import secure_filename
from flask import current_app
from .validation import validate_required_fields

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_image(image):
    if image and not allowed_file(image.filename):
        return None, 'Invalid image file type'

    if image:
        filename = secure_filename(image.filename)
        upload_folder = current_app.config['UPLOAD_FOLDER']
        image.save(os.path.join(upload_folder, filename))
        return filename, None
    return None, None

def validate_fields(data, required_fields):
    is_valid, validation_errors = validate_required_fields(data, required_fields)
    if not is_valid:
        return False, validation_errors
    return True, None
