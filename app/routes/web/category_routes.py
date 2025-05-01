from flask import render_template, redirect, url_for, session, request
from constants import CATEGORY_LIST_WEB_URL, ADD_CATEGORY_WEB_URL
from . import admin_api
from app.models import Category

@admin_api.route(CATEGORY_LIST_WEB_URL, methods=['GET'])
def get_category_list_page():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))

    search = request.args.get('search', '').strip()
    category_id = request.args.get('categoryId', '').strip()

    query = Category.objects

    if search:
        query = query.filter(name__icontains=search)

    if category_id:
        query = query.filter(id=category_id)

    categories = query.order_by('-id')
    all_categories = Category.objects.only('id', 'name')

    return render_template(
        "admin/categorySubCategory/category/category_list.html",
        categories=categories,
        all_categories=all_categories
    )



@admin_api.route(ADD_CATEGORY_WEB_URL)
def add_new_category_page():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))
    return render_template('admin/categorySubCategory/category/add_new_category.html')


