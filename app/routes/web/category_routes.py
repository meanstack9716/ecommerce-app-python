from flask import render_template, redirect, url_for, session, request
from constants import CATEGORY_LIST_WEB_URL, ADD_CATEGORY_WEB_URL, SUBCATEGORY_LIST_WEB_URL, Add_SUBCATEGORY_LIST_WEB_URL, PRODUCT_LIST_WEB_URL, PRODUCT_ADD_WEB_URL
from . import admin_api
from app.models import Category, SubCategory, ProductType

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


@admin_api.route(SUBCATEGORY_LIST_WEB_URL, methods=['GET'])
def get_subcategory_list_page():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))

    search_query = request.args.get('search', '').strip()

    if search_query:
        subcategories = SubCategory.objects(name__icontains=search_query)
    else:
        subcategories = SubCategory.objects.all()

    return render_template(
        "admin/categorySubCategory/subcategory/subcategory_list.html",
        subcategories=subcategories
    )

@admin_api.route(Add_SUBCATEGORY_LIST_WEB_URL, methods=['POST','GET'])
def add_subcategory_page():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))
    
    categories = Category.objects.all()
    return render_template('admin/categorySubCategory/subcategory/add_subcategory.html', categories=categories)


@admin_api.route(PRODUCT_ADD_WEB_URL, methods=['POST', 'GET'])
def add_product_type_page():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))
    
    categories = Category.objects.all()
    
    return render_template(
        'admin/categorySubCategory/products/add_products.html',
        categories=categories,
    )

@admin_api.route(PRODUCT_LIST_WEB_URL, methods=['GET'])
def product_list_page():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))
    
    # Fetch product types from the database
    product_types = ProductType.objects.all()
    categories = Category.objects.all()
    subcategories = SubCategory.objects.all()
    return render_template('admin/categorySubCategory/products/product_list.html', product_types=product_types, categories=categories, subcategories=subcategories)
