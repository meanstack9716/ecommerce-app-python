from flask import render_template, redirect, url_for, session, Blueprint, request, jsonify
from constants import API_SUBCATEGORY_LIST, API_ADD_SUBCATEGORY, API_GET_SUBCATEGORIES_BY_CATEGORY_ID
from app.models import SubCategory, Category
from app.utils.validation import validate_required_fields
from app.utils.image_upload import upload_image, validate_fields
from app.utils.utils import create_error_response
from bson import ObjectId

subcategory_bp = Blueprint('subcategory_bp', __name__)

@subcategory_bp.route(API_SUBCATEGORY_LIST)
def get_subcategory_list():
    category_id = request.args.get('categoryId', '').strip()
    query = SubCategory.objects


    if category_id:
        query = query(category=category_id)

    subcategories = query.all()

    subcategories_json = []
    for subcat in subcategories:
        subcategories_json.append({
            "id": str(subcat.id),
            "name": subcat.name,
            "description": subcat.description,
            "img_url": subcat.img_url,
            "created_at": subcat.created_at.isoformat(),
            "category": {
                "id": str(subcat.category.id) if subcat.category else None,
                "name": subcat.category.name if subcat.category else None,
                "description": subcat.category.description if subcat.category else None,
                "img_url": subcat.category.img_url if subcat.category else None,
            }
        })

    return jsonify({"data": subcategories_json}), 200


@subcategory_bp.route(API_ADD_SUBCATEGORY, methods=['GET', 'POST'])
def add_new_subcategory():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))

    categories = Category.objects.all()

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        image = request.files.get('image')
        category_id = request.form.get('category')

        required_fields = ['name', 'description', 'category']
        is_valid, validation_errors = validate_fields({
            'name': name,
            'description': description,
            'category': category_id
        }, required_fields)

        if not is_valid:
            return create_error_response({"error": validation_errors}, 400)

        category = Category.objects(id=ObjectId(category_id)).first()
        if not category:
            return create_error_response({'error': 'Invalid category ID'}, 400)

        image_filename, image_error = upload_image(image)
        if image_error:
            return create_error_response({'error': image_error}, 400)

        new_subcategory = SubCategory(
            name=name,
            description=description,
            category=category,
            img_url=image_filename
        )
        new_subcategory.save()

        return jsonify({
            'status': 'success',
            'message': 'SubCategory created successfully',
            'subcategory': {
                'name': new_subcategory.name,
                'description': new_subcategory.description,
                'category': new_subcategory.category.name,
                'img_url': new_subcategory.img_url
            }
        })

@subcategory_bp.route(API_GET_SUBCATEGORIES_BY_CATEGORY_ID, methods=['GET'])
def get_subcategories_by_category(category_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    subcategories = SubCategory.objects(category=category_id)
    subcategory_list = [{"id": str(sub.id), "name": sub.name} for sub in subcategories]
    return jsonify(subcategory_list)


@subcategory_bp.route('/delete_subcategory/<string:subcategory_id>', methods=['POST'])
def delete_subcategory(subcategory_id):
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))

    try:
        subcategory = SubCategory.objects(id=ObjectId(subcategory_id)).first()
        if not subcategory:
            return create_error_response({'error': 'SubCategory not found'}, 404)

        subcategory.delete()

        return jsonify({
            'status': 'success',
            'message': 'SubCategory deleted successfully'
        })
    except Exception as e:
        return create_error_response({'error': str(e)}, 500)
