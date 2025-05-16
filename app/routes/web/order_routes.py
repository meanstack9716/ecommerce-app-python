from flask import render_template, session, redirect, url_for
from . import admin_api

@admin_api.route('/orders')
def orders():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))
    return render_template("admin/orderPage/orders.html")
