from flask import request, jsonify, session, Blueprint
from constants import API_CATEGORY_LIST, API_ADD_CATEGORY
from app.models import Category
from app.utils.validation import validate_required_fields
from app.utils.image_upload import upload_image, validate_fields
from app.utils.utils import create_error_response
from bson import ObjectId

category_bp = Blueprint('category_bp', __name__)

@category_bp.route(API_ADD_CATEGORY, methods=['POST'])
def add_new_category():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    name = request.form.get('name')
    description = request.form.get('description')
    image = request.files.get('image')

    required_fields = ['name', 'description']
    is_valid, validation_errors = validate_fields({
        'name': name,
        'description': description
    }, required_fields)

    if not is_valid:
        return create_error_response(validation_errors, 400)

    image_filename, image_error = upload_image(image)
    if image_error:
        return create_error_response({'image': image_error}, 400)

    new_category = Category(
        name=name,
        description=description,
        img_url=image_filename
    )
    new_category.save()

    return jsonify({
        'status': 'success',
        'message': 'Category created successfully',
        'category': {
            'id': str(new_category.id),
            'name': new_category.name,
            'description': new_category.description,
            'img_url': new_category.img_url
        }
    })

@category_bp.route(API_CATEGORY_LIST, methods=['GET'])
def get_category_list():
    search_query = request.args.get('search', '').strip()
    
    if search_query:
        categories = Category.objects(name__icontains=search_query)
    else:
        categories = Category.objects.all()

    categories_data = [{
        'id': str(category.id),
        'name': category.name,
        'description': category.description,
        'img_url': category.img_url,
        'created_at': category.created_at.isoformat() if category.created_at else None,
    } for category in categories]

    return jsonify({
        'status': 'success',
        'data': categories_data,
    })

@category_bp.route('/delete_category/<string:category_id>', methods=['POST'])
def delete_category(category_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        category = Category.objects(id=ObjectId(category_id)).first()
        if not category:
            return create_error_response({'error': 'Category not found'}, 404)

        category.delete()

        return jsonify({
            'status': 'success',
            'message': 'Category deleted successfully'
        })
    except Exception as e:
        return create_error_response({'error': str(e)}, 500)