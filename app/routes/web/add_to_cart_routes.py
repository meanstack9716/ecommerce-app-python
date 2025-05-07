from flask import render_template, session, redirect, url_for, request
from . import admin_api


@admin_api.route('/cart')
def view_cart():
    cart = session.get('cart', [])
    return render_template('admin/addToCart/cart.html', cart=cart)
