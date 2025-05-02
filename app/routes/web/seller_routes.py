from flask import render_template, redirect, session, url_for, request
from . import admin_api
from app.models import Seller, Identification

@admin_api.route('/users/add-new-seller')
def add_new_seller():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))
    return render_template("admin/seller/add_new_seller.html")


@admin_api.route('/users/seller/list')
def get_seller_list():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))

    sellers = Seller.objects.all()

    enriched_sellers = []
    for seller in sellers:
        user = seller.user_id
        address = seller.address
        # get identification by user_id
        identification = Identification.objects(user_id=user).first()
        
        enriched_sellers.append({
            "seller": seller,
            "user": user,
            "address": address,
            "identification": identification
        })

    return render_template(
        "admin/seller/seller_list.html",
        sellers=enriched_sellers
    )


