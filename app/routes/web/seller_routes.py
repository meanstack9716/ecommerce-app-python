from flask import render_template, redirect, session, url_for, request, jsonify
from . import admin_api
from app.models import Seller, Identification
from mongoengine.queryset.visitor import Q
from constants import ADD_SELLER_WEB_URL, GET_SELLER_LIST_WEB_URL, GET_SELLERS_API_URL
from app.models import User
from app.models import Address

@admin_api.route(ADD_SELLER_WEB_URL)
def add_new_seller():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))
    return render_template("admin/seller/add_new_seller.html")

def fetch_sellers_data(search_query='', approval_status='', page=1, per_page=10):
    query = Seller.objects

    if approval_status:
        query = query.filter(is_approved=approval_status)

    if search_query:
        # Search in User fields
        user_query = Q(email__icontains=search_query) | Q(phone_number__icontains=search_query)
        matching_users = User.objects(user_query)
        matching_user_ids = [user.id for user in matching_users]

        # Search in Address fields (direct fields now)
        address_query = Q(city__icontains=search_query) | Q(line1__icontains=search_query)
        matching_addresses = Address.objects(address_query)
        matching_address_ids = [address.id for address in matching_addresses]

        # Build the main search query
        search_regex = Q(businessName__icontains=search_query)
        if matching_user_ids:
            search_regex |= Q(user_id__in=matching_user_ids)
        if matching_address_ids:
            search_regex |= Q(address__in=matching_address_ids)

        query = query.filter(search_regex)

    total_count = query.count()
    total_pages = (total_count + per_page - 1) // per_page

    start_idx = (page - 1) * per_page
    paginated_sellers = query.skip(start_idx).limit(per_page)

    enriched_sellers = []
    for idx, seller in enumerate(paginated_sellers, start=start_idx + 1):
        user = seller.user_id
        address = seller.address
        identification = Identification.objects(user_id=user).first()

        # Simplified address data access (direct fields)
        address_data = {
            "line1": address.line1 if address else "",
            "city": address.city if address else "",
            "state": address.state if address else "",
            "postal_code": address.postal_code if address else "",
            "country": address.country if address else ""
        }

        enriched_sellers.append({
            "index": idx,
            "seller": {
                "id": str(seller.id),
                "businessName": seller.businessName,
                "businessType": seller.businessType,
                "businessEmail": seller.businessEmail,
                "gst_number": seller.gst_number,
                "is_approved": seller.is_approved,
                "created_at": seller.created_at.isoformat() if seller.created_at else None
            },
            "user": {
                "id": str(user.id) if user else "",
                "email": user.email if user else "",
                "first_name": user.first_name if user else "",
                "last_name": user.last_name if user else "",
                "phone_number": user.phone_number if user else ""
            },
            "address": address_data,
            "identification": {
                "pan_number": identification.pan_number if identification else None,
                "address_proof_id_type": identification.address_proof_id_type if identification else None
            }
        })

    return {
        'data': enriched_sellers,
        'meta': {
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_count': total_count,
                'total_pages': total_pages,
                'has_prev': page > 1,
                'has_next': page < total_pages,
                'prev_page': page - 1 if page > 1 else None,
                'next_page': page + 1 if page < total_pages else None
            },
            'filters': {
                'search_query': search_query,
                'approval_status': approval_status
            }
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
        sellers=data['data'],
        filters=data['meta']['filters'],
        pagination=data['meta']['pagination'],
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
        'data': data['data'],
        'meta': data['meta']
    })