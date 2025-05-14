from flask import render_template, redirect, url_for, session, request, jsonify
from constants import SUBCATEGORY_LIST_WEB_URL, Add_SUBCATEGORY_LIST_WEB_URL, GET_SUBCATEGORIES_FILTER_API_URL
from . import admin_api
from app.models import Category, SubCategory


def fetch_subcategories_data(category_id='', page=1, per_page=10):
    categories = [{'id': str(cat.id), 'name': cat.name} for cat in Category.objects.all()]

    query = SubCategory.objects()
    if category_id:
        query = query.filter(category=category_id)

    total_count = query.count()
    total_pages = (total_count + per_page - 1) // per_page

    subcategories = query.order_by('-id').skip((page - 1) * per_page).limit(per_page)

    subcategories_data = [
        {
            'id': str(subcategory.id),
            'name': subcategory.name,
            'description': subcategory.description,
            'img_url': subcategory.img_url,
            'category': {
                'id': str(subcategory.category.id),
                'name': subcategory.category.name
            }
        }
        for subcategory in subcategories
    ]

    return {
        'subcategories': subcategories_data,
        'categories': categories,
        'pagination': {
            'page': page,
            'pages': total_pages,
            'has_prev': page > 1,
            'has_next': page < total_pages,
            'prev_num': page - 1 if page > 1 else None,
            'next_num': page + 1 if page < total_pages else None,
            'total': total_count,
            'per_page': per_page
        }
    }

@admin_api.route(SUBCATEGORY_LIST_WEB_URL, methods=['GET'])
def get_subcategory_list_page():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))

    category_id = request.args.get('categoryId', '').strip()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('limit', 10))

    data = fetch_subcategories_data(category_id, page, per_page)

    return render_template(
        "admin/categorySubCategory/subcategory/subcategory_list.html",
        subcategories=data['subcategories'],
        categories=data['categories'],
        pagination=data['pagination'],
        limit=per_page,
        subcategories_api_url=GET_SUBCATEGORIES_FILTER_API_URL
    )

@admin_api.route(GET_SUBCATEGORIES_FILTER_API_URL, methods=['GET'])
def get_subcategories():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    category_id = request.args.get('categoryId', '').strip()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('limit', 10))

    data = fetch_subcategories_data(category_id, page, per_page)

    return jsonify({
        'subcategories': data['subcategories'],
        'categories': data['categories'],
        'pagination': data['pagination']
    })

@admin_api.route(Add_SUBCATEGORY_LIST_WEB_URL, methods=['POST','GET'])
def add_subcategory_page():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))
    
    categories = Category.objects.all()
    return render_template('admin/categorySubCategory/subcategory/add_subcategory.html', categories=categories)

