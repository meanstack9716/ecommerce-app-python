from flask import render_template, session, redirect, url_for
from . import admin_api
from app.models.order import Order

@admin_api.route('/orders')
def orders():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))
    
    orders = Order.objects().order_by('-created_at')
    
    return render_template("admin/orderPage/orders.html", orders=orders)


@admin_api.route('/orders/updates')
def update_order_status():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))
    
    orders = Order.objects().order_by('-created_at')
    
    return render_template("admin/orderPage/orders.html", orders=orders)