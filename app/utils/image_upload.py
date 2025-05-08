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
        image_bytes = image.read()
        content_type = image.mimetype
        encoded_image = base64.b64encode(image_bytes).decode('utf-8')

        image_id = str(uuid.uuid4())[:8]

        image_store[image_id] = {'data': encoded_image, 'content_type': content_type}

        base_url = request.host_url.rstrip('/')
        image_url = f"{base_url}/image/{image_id}"

        return image_url, None

    return None, None

def validate_fields(data, required_fields):
    is_valid, validation_errors = validate_required_fields(data, required_fields)
    if not is_valid:
        return False, validation_errors
    return True, None
