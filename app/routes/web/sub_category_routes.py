from flask import render_template, redirect, url_for, session, request
from constants import SUBCATEGORY_LIST_WEB_URL, Add_SUBCATEGORY_LIST_WEB_URL
from . import admin_api
from app.models import Category, SubCategory


@admin_api.route(SUBCATEGORY_LIST_WEB_URL, methods=['GET'])
def get_subcategory_list_page():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)

    category_id = request.args.get('categoryId', '').strip()

    categories = Category.objects.all()
    subcategories_query = SubCategory.objects()

    if category_id:
        subcategories_query = subcategories_query.filter(category=category_id)

    # ✅ Correct parameter name here
    subcategories = subcategories_query.paginate(page=page, per_page=limit)

    return render_template(
        "admin/categorySubCategory/subcategory/subcategory_list.html",
        subcategories=subcategories,
        categories=categories
    )


@admin_api.route(Add_SUBCATEGORY_LIST_WEB_URL, methods=['POST','GET'])
def add_subcategory_page():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))
    
    categories = Category.objects.all()
    return render_template('admin/categorySubCategory/subcategory/add_subcategory.html', categories=categories)

