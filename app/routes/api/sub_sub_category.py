from flask import Blueprint, request, session, jsonify, redirect, url_for
from app.models import SubSubCategory, SubCategory, Category
from app.utils.image_upload import upload_image, validate_fields
from app.utils.utils import create_error_response
from bson import ObjectId
from constants import SUB_SUB_CATEGORY_ADD_API, GET_SUBSUBCATEGORIES_BY_CATEGORY_ID_API, DELETE_SUB_SUB_CATEGORY_WEB_URL

sub_sub_category_bp = Blueprint('sub_sub_category_bp', __name__)


@sub_sub_category_bp.route(SUB_SUB_CATEGORY_ADD_API, methods=['POST'])
def add_sub_sub_category():
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
        return create_error_response({"error" : errors}, 400)

    category = Category.objects(id=ObjectId(category_id_str)).first()
    if not category:
        return create_error_response({'error': 'Invalid category ID'}, 400)

    subcategory = SubCategory.objects(id=ObjectId(subcategory_id_str)).first()
    if not subcategory:
        return create_error_response({'error': 'Invalid subcategory ID'}, 400)

    image_filename, image_error = upload_image(image)
    if image_error:
        return create_error_response({'error': image_error}, 400)

    new_ptype = SubSubCategory(
        name=name,
        description=description,
        category_id=category,
        sub_category_id=subcategory,
        img_url=image_filename
    )
    new_ptype.save()

    return jsonify({
        'status': 'success',
        'message': 'SubSubCategory created successfully',
        'product_type': {
            'name': new_ptype.name,
            'description': new_ptype.description,
            'category': new_ptype.category_id.name,
            'subcategory': new_ptype.sub_category_id.name,
            'img_url': url_for('serve_uploaded_files', filename=new_ptype.img_url, _external=True) if new_ptype.img_url else ''
        }
    })


@sub_sub_category_bp.route(GET_SUBSUBCATEGORIES_BY_CATEGORY_ID_API, methods=['GET'])
def get_sub_sub_category():
    subCategory_id = request.args.get('subCategoryId')
    if not subCategory_id:
        return jsonify({'success': False, 'message': 'categoryId is required'}), 400

    product_types = SubSubCategory.objects(sub_category_id=subCategory_id)
    return jsonify([
        {
            'id': str(pt.id),
            'name': pt.name,
            'img_url': url_for('serve_uploaded_files', filename=pt.img_url, _external=True) if pt.img_url else '',
            'description': pt.description,
            'categoryName': pt.category_id.name,
            'subcategoryName': pt.sub_category_id.name
        } for pt in product_types
    ])


@sub_sub_category_bp.route(DELETE_SUB_SUB_CATEGORY_WEB_URL, methods=['DELETE'])
def delete_sub_sub_category(sub_sub_category_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized access'}), 401
    
    if not sub_sub_category_id:
        return jsonify({'success': False, 'message': 'Sub-sub category ID is required'}), 400
    
    try:
        sub_sub_category = SubSubCategory.objects(id=ObjectId(sub_sub_category_id)).first()
        if not sub_sub_category:
            return jsonify({'success': False, 'message': 'Sub-sub category not found'}), 404
        
        sub_sub_category.delete()
        
        return jsonify({
            'success': True,
            'message': 'Sub-sub category deleted successfully'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'An error occurred while deleting the sub-sub category',
            'error': str(e)
        }), 500
