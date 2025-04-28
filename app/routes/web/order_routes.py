from flask import render_template
from . import admin_api

@admin_api.route('/orders')
def orders():
    return render_template("admin/orderPage/orders.html")
