from flask import render_template, session, redirect, url_for, request
from . import admin_api


@admin_api.route('/cart', methods=['GET', 'POST'])
def view_cart():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))
    return render_template('admin/addToCart/cart.html')



@admin_api.route('/checkout', methods=['GET', 'POST'])
def checkout_page():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))
    return render_template('admin/addToCart/checkout.html')