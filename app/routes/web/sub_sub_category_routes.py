
from flask import render_template, redirect, url_for, session, request
from constants import SUB_SUB_CATEGORY_LIST_WEB_URL,  SUB_SUB_CATEGORY_WEB_URL
from . import admin_api
from app.models import Category, SubSubCategory


@admin_api.route(SUB_SUB_CATEGORY_WEB_URL, methods=['POST', 'GET'])
def add_sub_sub_category_page():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))
    
    categories = Category.objects.all()
    
    return render_template(
        'admin/categorySubCategory/sub_sub_category/add_sub_sub_category.html',
        categories=categories,
    )

@admin_api.route(SUB_SUB_CATEGORY_LIST_WEB_URL, methods=['GET'])
def sub_sub_category_list_page():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))
    
    categories = Category.objects.all()
    return render_template('admin/categorySubCategory/sub_sub_category/sub_sub_category_list.html', categories=categories)