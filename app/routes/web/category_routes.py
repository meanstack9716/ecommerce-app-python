from flask import render_template
from . import admin_api

@admin_api.route('/add_new_category')
def add_new_category():
    return render_template('admin/category/add_new_category.html')
