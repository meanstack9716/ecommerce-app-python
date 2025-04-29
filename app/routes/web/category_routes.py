from flask import render_template, redirect, url_for, session, Blueprint, request, jsonify
from constants import GET_CATEGORY_LIST, ADD_NEW_CATEGORY
from app.models import Category
from app.utils.validation import validate_required_fields
from app.utils.image_upload import upload_image, validate_fields
from app.utils.utils import create_error_response

category_bp = Blueprint('category_bp', __name__)

@category_bp.route(GET_CATEGORY_LIST)
def get_category_list():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))

    categories = Category.objects.all()
    return render_template("admin/category/category_list.html", categories=categories)


@category_bp.route(ADD_NEW_CATEGORY, methods=['GET', 'POST'])
def add_new_category():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))

    if request.method == 'POST':
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

        image_path, image_error = upload_image(image)
        if image_error:
            return create_error_response({'image': image_error}, 400)

        new_category = Category(
            name=name,
            description=description,
            image_path=image_path
        )
        new_category.save()

        return jsonify({
            'status': 'success',
            'message': 'Category created successfully',
            'category': {
                'name': new_category.name,
                'description': new_category.description,
                'image_path': new_category.image_path
            }
        })

    return render_template('admin/category/add_new_category.html')
