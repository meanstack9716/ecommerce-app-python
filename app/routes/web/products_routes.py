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
    per_page = request.args.get('limit', 10, type=int)

    category = request.args.get('category')
    status = request.args.get('status')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)

    query = {}

    if category:
        category_obj = Category.objects(name=category).first()
        if category_obj:
            query['category_id'] = category_obj.id

    if status:
        query['status'] = status

    if min_price is not None:
        query['final_price__gte'] = min_price

    if max_price is not None:
        query['final_price__lte'] = max_price

    products = AddProducts.objects(**query).order_by('-created_at').paginate(page=page, per_page=per_page)
    categories = Category.objects.all()

    return render_template(
        'admin/products/product_lists.html',
        products=products,
        categories=categories,
    )



@admin_api.route('/products/<product_id>', methods=['GET'])
def product_details(product_id):
    product = AddProducts.objects(id=product_id).first()
    if not product:
        return "Product not found", 404

    return render_template('admin/products/product_details.html', product=product)
