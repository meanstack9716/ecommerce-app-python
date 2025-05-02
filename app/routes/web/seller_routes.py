from flask import render_template, redirect, session, url_for, request
from . import admin_api
from app.models import Seller, Identification
from mongoengine.queryset.visitor import Q

@admin_api.route('/users/add-new-seller')
def add_new_seller():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))
    return render_template("admin/seller/add_new_seller.html")

@admin_api.route('/users/seller/list')
def get_seller_list():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))

    search_query = request.args.get('search', '')
    approval_status = request.args.get('approval_status', '')

    sellers = Seller.objects.all()

    # Apply search filter if search query exists
    if search_query:
        sellers = sellers.filter(
            Q(businessName__icontains=search_query) | 
            Q(user_id__email__icontains=search_query) | 
            Q(user_id__phone_number__icontains=search_query)
        )

    # Apply approval status filter if provided
    if approval_status:
        sellers = sellers.filter(Seller.is_approved==approval_status)

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
        sellers=enriched_sellers,
        filters={'search': search_query, 'approval_status': approval_status}
    )