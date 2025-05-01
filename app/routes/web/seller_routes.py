from flask import render_template, redirect, session, url_for
from . import admin_api


@admin_api.route('/users/add-new-seller')
def add_new_seller():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))
    return render_template("admin/seller/add_new_seller.html")
