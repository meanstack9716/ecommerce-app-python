from flask import render_template, redirect, url_for, session, Blueprint, request, jsonify
from constants import GET_SUBCATEGORY_LIST, ADD_NEW_SUBCATEGORY
from app.models import SubCategory, Category
from app.utils.validation import validate_required_fields
from app.utils.image_upload import upload_image, validate_fields
from app.utils.utils import create_error_response
from bson import ObjectId

subcategory_bp = Blueprint('subcategory_bp', __name__)

@subcategory_bp.route(GET_SUBCATEGORY_LIST)
def get_subcategory_list():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))

    search_query = request.args.get('search', '').strip()

    if search_query:
        subcategories = SubCategory.objects(name__icontains=search_query)
    else:
        subcategories = SubCategory.objects.all()

    return render_template("admin/subcategory/subcategory_list.html", subcategories=subcategories)


@subcategory_bp.route(ADD_NEW_SUBCATEGORY, methods=['GET', 'POST'])
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
            return create_error_response(validation_errors, 400)

        category = Category.objects(id=ObjectId(category_id)).first()
        if not category:
            return create_error_response({'category': 'Invalid category ID'}, 400)

        image_filename, image_error = upload_image(image)
        if image_error:
            return create_error_response({'image': image_error}, 400)

        new_subcategory = SubCategory(
            name=name,
            description=description,
            category=category,
            image_path=image_filename
        )
        new_subcategory.save()

        return jsonify({
            'status': 'success',
            'message': 'SubCategory created successfully',
            'subcategory': {
                'name': new_subcategory.name,
                'description': new_subcategory.description,
                'category': new_subcategory.category.name,
                'image_path': new_subcategory.image_path
            }
        })

    return render_template('admin/subcategory/add_new_subcategory.html', categories=categories)


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
