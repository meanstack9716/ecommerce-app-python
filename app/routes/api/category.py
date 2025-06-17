from flask import request, jsonify, session, Blueprint
from constants import API_CATEGORY_LIST, API_ADD_CATEGORY, API_CATEGORY_LIST_BY_ID
from app.models import Category, SubCategory, SubSubCategory
from app.utils.validation import validate_required_fields
from app.utils.image_upload import upload_image, validate_fields
from app.utils.utils import create_error_response
from bson import ObjectId
from flask import current_app
from app.utils.image_upload import get_local_ip

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
        return create_error_response({"error": validation_errors}, 400)

    image_filename, image_error = upload_image(image)
    if image_error:
        return create_error_response({'error': image_error}, 400)

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
    local_ip = get_local_ip()
    port = current_app.config.get('SERVER_PORT', 8080)
    if search_query:
        categories = Category.objects(name__icontains=search_query)
    else:
        categories = Category.objects.all()

    categories_data = []

    for category in categories:
        subcategories = SubCategory.objects(category=category)
        subcategories_data = []
        
        total_sub_subcategories = 0

        for subcategory in subcategories:
            subsubcategories = SubSubCategory.objects(sub_category_id=subcategory)
            sub_sub_categories_data = []
            
            sub_sub_category_count = subsubcategories.count()
            total_sub_subcategories += sub_sub_category_count

            for subsub in subsubcategories:
                sub_sub_categories_data.append({
                    'id': str(subsub.id),
                    'name': subsub.name,
                    'description': subsub.description,
                    'img_url': f"http://{local_ip}:{port}/static/uploads/{subsub.img_url}" or '',
                })

            subcategories_data.append({
                'id': str(subcategory.id),
                'name': subcategory.name,
                'description': subcategory.description,
                'img_url': f"http://{local_ip}:{port}/static/uploads/{subcategory.img_url}" or '',
                'sub_sub_categories': sub_sub_categories_data,
                'sub_sub_category_count': sub_sub_category_count,
            })

        categories_data.append({
            'id': str(category.id),
            'name': category.name,
            'description': category.description,
            'img_url': f"http://{local_ip}:{port}/static/uploads/{category.img_url}" or '',
            'sub_categories': subcategories_data,
            'sub_category_count': subcategories.count(),
            'sub_sub_category_count': total_sub_subcategories,
        })

    return jsonify({
        'status': 'success',
        'data': categories_data,
    })


@category_bp.route(API_CATEGORY_LIST_BY_ID, methods=['GET'])
def get_category_with_children(category_id):
    try:
        category = Category.objects.get(id=category_id)
    except Category.DoesNotExist:
        return jsonify({
            'status': 'error',
            'message': 'Category not found'
        }), 404

    # Fetch subcategories for this category
    subcategories = SubCategory.objects(category=category)
    
    subcategories_data = []
    for subcategory in subcategories:
        # Fetch sub-subcategories for this subcategory
        subsubcategories = SubSubCategory.objects(
            category_id=category,
            sub_category_id=subcategory
        )
        subsubcategories_data = [{
            'id': str(subsub.id),
            'name': subsub.name,
            'description': subsub.description,
            'img_url': subsub.img_url,
            'created_at': subsub.created_at.isoformat() if subsub.created_at else None
        } for subsub in subsubcategories]

        subcategories_data.append({
            'id': str(subcategory.id),
            'name': subcategory.name,
            'description': subcategory.description,
            'img_url': subcategory.img_url,
            'created_at': subcategory.created_at.isoformat() if subcategory.created_at else None,
            'subsubcategories': subsubcategories_data
        })

    category_data = {
        'id': str(category.id),
        'name': category.name,
        'description': category.description,
        'img_url': category.img_url,
        'created_at': category.created_at.isoformat() if category.created_at else None,
        'subcategories': subcategories_data
    }

    return jsonify({
        'status': 'success',
        'data': category_data
    })