from flask import render_template, redirect, url_for, session
from constants import ADD_NEW_PRODUCT_WEB_URL
from . import admin_api
from app.models import Category, SubCategory, ProductType


@admin_api.route(ADD_NEW_PRODUCT_WEB_URL, methods=['POST', 'GET'])
def add_product_type_page():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))
    
    categories = Category.objects.all()
    
    return render_template(
        'admin/adsProducts/addNewProduct.html',
        categories=categories,
    )