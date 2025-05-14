from flask import render_template, redirect, url_for, session, request, jsonify
from constants import CATEGORY_LIST_WEB_URL, ADD_CATEGORY_WEB_URL, GET_CATEGORIES_FILTER_API_URL
from . import admin_api
from app.models import Category


def fetch_categories_data(search='', category_id='', page=1, per_page=10):
    query = Category.objects

    if search:
        query = query.filter(name__icontains=search)
    if category_id:
        query = query.filter(id=category_id)

    total_count = query.count()
    total_pages = (total_count + per_page - 1) // per_page 

    categories = query.order_by('-id').skip((page - 1) * per_page).limit(per_page)

    categories_data = [
        {
            'id': str(category.id),
            'name': category.name,
            'description': category.description,
            'img_url': category.img_url
        }
        for category in categories
    ]

    all_categories = [{'id': str(cat.id), 'name': cat.name} for cat in Category.objects.only('id', 'name')]

    return {
        'categories': categories_data,
        'all_categories': all_categories,
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

@admin_api.route(CATEGORY_LIST_WEB_URL, methods=['GET'])
def get_category_list_page():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))

    search = request.args.get('search', '').strip()
    category_id = request.args.get('categoryId', '').strip()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('limit', 10))

    data = fetch_categories_data(search, category_id, page, per_page)

    return render_template(
        "admin/categorySubCategory/category/category_list.html",
        categories=data['categories'],
        all_categories=data['all_categories'],
        pagination=data['pagination'],
        limit=per_page,
        categories_api_url=GET_CATEGORIES_FILTER_API_URL
    )

@admin_api.route(GET_CATEGORIES_FILTER_API_URL, methods=['GET'])
def get_categories():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    search = request.args.get('search', '').strip()
    category_id = request.args.get('categoryId', '').strip()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('limit', 10))

    data = fetch_categories_data(search, category_id, page, per_page)

    return jsonify({
        'categories': data['categories'],
        'all_categories': data['all_categories'],
        'pagination': data['pagination']
    })
@admin_api.route(ADD_CATEGORY_WEB_URL)
def add_new_category_page():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))
    return render_template('admin/categorySubCategory/category/add_new_category.html')


