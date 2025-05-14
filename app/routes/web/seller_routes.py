from flask import render_template, redirect, session, url_for, request, jsonify
from . import admin_api
from app.models import Seller, Identification
from mongoengine.queryset.visitor import Q
from constants import ADD_SELLER_WEB_URL, GET_SELLER_LIST_WEB_URL, GET_SELLERS_API_URL


@admin_api.route(ADD_SELLER_WEB_URL)
def add_new_seller():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))
    return render_template("admin/seller/add_new_seller.html")

def fetch_sellers_data(search_query='', approval_status='', page=1, per_page=10):
    # Fetch all sellers
    sellers = Seller.objects.all()

    # Apply approval status filter
    if approval_status:
        sellers = sellers.filter(is_approved=approval_status)

    # Apply search filter
    filtered_sellers = []
    for seller in sellers:
        user = seller.user_id
        if (
            (search_query.lower() in seller.businessName.lower()) or
            (search_query.lower() in user.email.lower()) or
            (search_query.lower() in user.phone_number.lower())
        ):
            filtered_sellers.append(seller)

    # Calculate pagination info
    total_count = len(filtered_sellers)
    total_pages = (total_count + per_page - 1) // per_page  # Ceiling division

    # Apply pagination
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_sellers = filtered_sellers[start_idx:end_idx]

    # Enrich seller data
    enriched_sellers = []
    for idx, seller in enumerate(paginated_sellers, start=start_idx + 1):
        user = seller.user_id
        address = seller.address
        identification = Identification.objects(user_id=user).first()

        enriched_sellers.append({
            "index": idx,
            "seller": {
                "businessName": seller.businessName,
                "businessType": seller.businessType,
                "is_approved": seller.is_approved
            },
            "user": {
                "email": user.email,
                "phone_number": user.phone_number
            },
            "address": {
                "personal_address": {
                    "line1": address.personal_address.line1,
                    "city": address.personal_address.city
                }
            },
            "identification": {
                "pan_number": identification.pan_number if identification else "---"
            }
        })

    return {
        'sellers': enriched_sellers,
        'pagination': {
            'page': page,
            'pages': total_pages,
            'has_prev': page > 1,
            'has_next': page < total_pages,
            'prev_num': page - 1 if page > 1 else None,
            'next_num': page + 1 if page < total_pages else None,
            'total': total_count,
            'per_page': per_page
        }
    }

@admin_api.route(GET_SELLER_LIST_WEB_URL)
def get_seller_list():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))

    search_query = request.args.get('search', '').strip()
    approval_status = request.args.get('approval_status', '').strip()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('limit', 10))

    data = fetch_sellers_data(search_query, approval_status, page, per_page)

    return render_template(
        "admin/seller/seller_list.html",
        sellers=data['sellers'],
        filters={'search': search_query, 'approval_status': approval_status},
        pagination=data['pagination'],
        limit=per_page,
        sellers_api_url=GET_SELLERS_API_URL
    )

@admin_api.route(GET_SELLERS_API_URL, methods=['GET'])
def get_sellers():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    search_query = request.args.get('search', '').strip()
    approval_status = request.args.get('approval_status', '').strip()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('limit', 10))

    data = fetch_sellers_data(search_query, approval_status, page, per_page)

    return jsonify({
        'sellers': data['sellers'],
        'pagination': data['pagination'],
        'filters': {'search': search_query, 'approval_status': approval_status}
    })