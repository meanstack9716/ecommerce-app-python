from flask import Blueprint, request, session, jsonify, redirect, url_for
from app.models import ProductType, SubCategory, Category
from app.utils.image_upload import upload_image, validate_fields
from app.utils.utils import create_error_response
from bson import ObjectId
from constants import API_ADD_PRODUCTTYPE, API_GET_PRODUCT_TYPE_BY_SUBCATEGORY_ID

product_type_bp = Blueprint('product_type_bp', __name__)


@product_type_bp.route(API_ADD_PRODUCTTYPE, methods=['POST'])
def add_product_type():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))

    name = request.form.get('name')
    description = request.form.get('description')
    image = request.files.get('image')
    category_id_str = request.form.get('category')
    subcategory_id_str = request.form.get('subcategory')

    required_fields = ['name', 'description', 'category', 'subcategory']
    is_valid, errors = validate_fields({
        'name': name,
        'description': description,
        'category': category_id_str,
        'subcategory': subcategory_id_str
    }, required_fields)

    if not is_valid:
        return create_error_response(errors, 400)

    category = Category.objects(id=ObjectId(category_id_str)).first()
    if not category:
        return create_error_response({'category': 'Invalid category ID'}, 400)

    subcategory = SubCategory.objects(id=ObjectId(subcategory_id_str)).first()
    if not subcategory:
        return create_error_response({'subcategory': 'Invalid subcategory ID'}, 400)

    image_filename, image_error = upload_image(image)
    if image_error:
        return create_error_response({'image': image_error}, 400)

    new_ptype = ProductType(
        name=name,
        description=description,
        category_id=category,
        sub_category_id=subcategory,
        img_url=image_filename
    )
    new_ptype.save()

    return jsonify({
        'status': 'success',
        'message': 'ProductType created successfully',
        'product_type': {
            'name': new_ptype.name,
            'description': new_ptype.description,
            'category': new_ptype.category_id.name,
            'subcategory': new_ptype.sub_category_id.name,
            'img_url': new_ptype.img_url
        }
    })


@product_type_bp.route(API_GET_PRODUCT_TYPE_BY_SUBCATEGORY_ID, methods=['GET'])
def get_product_types(subcategory_id):
    product_types = ProductType.objects(sub_category_id=subcategory_id)
    return jsonify([
        {
            'name': pt.name,
            'img_url': pt.img_url,
            'description': pt.description,
            'categoryName': pt.category_id.name,
            'subcategoryName': pt.sub_category_id.name
        } for pt in product_types
    ])