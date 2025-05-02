from flask import render_template, redirect, url_for, session, request
from constants import ADD_NEW_PRODUCT_WEB_URL, GET_PRODUCT_LIST_WEB_URL
from . import admin_api
from app.models import Category, SubCategory, SubSubCategory, AddProducts


@admin_api.route(ADD_NEW_PRODUCT_WEB_URL, methods=['GET'])
def add_products_page():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))
    
    categories = Category.objects.all()
    
    return render_template(
        'admin/products/add_new_product.html',
        categories=categories,
    )

@admin_api.route(GET_PRODUCT_LIST_WEB_URL, methods=['GET'])
def get_product_lists():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))

    page = request.args.get('page', 1, type=int)
    per_page = 10

    products = AddProducts.objects.order_by('-created_at').paginate(page=page, per_page=per_page)

    return render_template(
        'admin/products/product_lists.html',
        products=products
    )

@admin_api.route('/products/<product_id>', methods=['GET'])
def product_details(product_id):
    product = AddProducts.objects(id=product_id).first()
    if not product:
        return "Product not found", 404

    return render_template('admin/products/product_details.html', product=product)
