
from flask import render_template, redirect, url_for, session, request
from constants import PRODUCT_LIST_WEB_URL, ADD_PRODUCT_TYPE_WEB_URL
from . import admin_api
from app.models import Category, ProductType


@admin_api.route(ADD_PRODUCT_TYPE_WEB_URL, methods=['POST', 'GET'])
def add_product_type_page():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))
    
    categories = Category.objects.all()
    
    return render_template(
        'admin/categorySubCategory/product_types/add_products.html',
        categories=categories,
    )

@admin_api.route(PRODUCT_LIST_WEB_URL, methods=['GET'])
def product_list_page():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))
    
    categories = Category.objects.all()
    return render_template('admin/categorySubCategory/product_types/product_list.html', categories=categories)