from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
from app.models import Category, User
from constants import ADD_NEW_CATEGORY
from app.utils.validation import validate_required_fields
from app.utils.utils import create_error_response

category_bp = Blueprint('category', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@category_bp.route(ADD_NEW_CATEGORY, methods=['POST'])
def api_add_category():
    title = request.form.get('title')
    description = request.form.get('description')
    image = request.files.get('image')

    required_fields = ['title', 'description']
    is_valid, validation_errors = validate_required_fields({
        'title': title,
        'description': description
    }, required_fields)

    if not is_valid:
        return create_error_response(validation_errors, 400)

    if image and not allowed_file(image.filename):
        return create_error_response({'image': 'Invalid image file type'}, 400)

    if image:
        filename = secure_filename(image.filename)
        upload_folder = current_app.config['UPLOAD_FOLDER']
        image.save(os.path.join(upload_folder, filename))
        image_path = os.path.join(upload_folder, filename)
    else:
        image_path = None

    new_category = Category(
        title=title,
        description=description,
        image_path=image_path
    )
    
    new_category.save()

    return jsonify({
        'status': 'success',
        'message': 'Category created successfully',
        'category': {
            'title': new_category.title,
            'description': new_category.description,
            'image_path': new_category.image_path
        }
    })