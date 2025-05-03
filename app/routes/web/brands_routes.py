from flask import render_template, session, redirect, url_for, request
from . import admin_api
from app.models import ProductBrands
from constants import GET_BRANDS_WEB_URL, ADD_BRAND_WEB_URL, UPDATE_BRAND_WEB_URL, DELETE_BRAND_API


@admin_api.route(GET_BRANDS_WEB_URL)
def get_brand_list_page():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))
    
    search_query = request.args.get('search', '')
    limit = int(request.args.get('limit', 10))
    
    if search_query:
        brands = ProductBrands.objects(name__icontains=search_query)
    else:
        brands = ProductBrands.objects.all()
    
    page = int(request.args.get('page', 1))
    brands_paginated = brands.paginate(page=page, per_page=limit)
    
    return render_template('admin/productBrands/brands_list.html', 
                           brands=brands_paginated.items, 
                           pagination=brands_paginated, 
                           search=search_query, 
                           limit=limit)


@admin_api.route(ADD_BRAND_WEB_URL)
def add_new_brand_page():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))
    return render_template('admin/productBrands/add_brands.html')


@admin_api.route(UPDATE_BRAND_WEB_URL, methods=['GET', 'POST'])
def update_brand_page(brand_id):
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))

    brand = ProductBrands.objects(id=brand_id).first()
    if not brand:
        return redirect(url_for('admin_api.get_brand_list_page'))
    return render_template('admin/productBrands/edit_brands.html', brand=brand)




@admin_api.route(DELETE_BRAND_API, methods=['POST'])
def delete_brand(brand_id):
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))

    brand = ProductBrands.objects(id=brand_id).first()
    if brand:
        brand.delete()

    return redirect(url_for('admin_api.get_brand_list_page'))

