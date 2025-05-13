from flask import Blueprint, request, jsonify, session
from app.models.wishlist import Wishlist, WishlistItem
from app.models.products import ProductVariant, Products
from datetime import datetime
from constants import WISHLIST_ADD, WISHLIST_REMOVE, WISHLIST_LIST, ALLOWED_SIZES

wishlist_bp = Blueprint('wishlist', __name__)

def get_user_id():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    return session['user_id']

@wishlist_bp.route(WISHLIST_ADD, methods=['POST'])
def add_to_wishlist():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    try:
        data = request.get_json()
    except Exception:
        return jsonify({"error": "Invalid JSON data"}), 400

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid data format, expected JSON object"}), 400

    product_id = data.get('product_id')
    variant_id = data.get('variant_id')
    size = data.get('size')

    user_id = get_user_id()
    if isinstance(user_id, tuple):
        return user_id

    if not product_id:
        return jsonify({"error": "product_id is required"}), 400

    if size and size not in ALLOWED_SIZES:
        return jsonify({"error": f"Invalid size. Must be one of {ALLOWED_SIZES}"}), 400

    product = Products.objects(id=product_id).first()
    if not product:
        return jsonify({"error": "Product not found"}), 404

    variant = None
    if variant_id or size:
        query = ProductVariant.objects(product_id=product)
        if variant_id:
            query = query.filter(id=variant_id)
        if size:
            query = query.filter(size=size)
        variant = query.first()
        if not variant:
            return jsonify({"error": "Variant not found for the specified product and size"}), 404

    wishlist_item = WishlistItem(
        product_id=product_id,
        variant_id=str(variant.id) if variant else None,
        size=size
    )

    try:
        wishlist_item.validate_product(Products)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    wishlist = Wishlist.objects(user_id=user_id).first()
    if not wishlist:
        wishlist = Wishlist(user_id=user_id, items=[], created_at=datetime.utcnow())

    existing_item = None
    for item in wishlist.items:
        if item.product_id == product_id and item.variant_id == wishlist_item.variant_id and item.size == size:
            existing_item = item
            break

    if existing_item:
        return jsonify({"message": "Item already in wishlist"}), 200
    else:
        wishlist.items.append(wishlist_item)

    wishlist.save()

    response_data = {
        "message": "Item added to wishlist",
        "wishlist": {
            "id": str(wishlist.id),
            "user_id": str(wishlist.user_id),
            "items": [
                {
                    "product_id": str(item.product_id),
                    "variant_id": str(item.variant_id) if item.variant_id else None,
                    "size": item.size,
                    "added_at": item.added_at.isoformat()
                } for item in wishlist.items
            ],
            "created_at": wishlist.created_at.isoformat(),
            "updated_at": wishlist.updated_at.isoformat()
        }
    }

    return jsonify(response_data), 200

@wishlist_bp.route(WISHLIST_REMOVE, methods=['POST'])
def remove_from_wishlist():
    user_id = get_user_id()
    if isinstance(user_id, tuple):
        return user_id

    data = request.json
    product_id = data.get('product_id')
    variant_id = data.get('variant_id')
    size = data.get('size')

    if not product_id:
        return jsonify({"error": "product_id is required"}), 400

    wishlist = Wishlist.objects(user_id=user_id).first()
    if not wishlist:
        return jsonify({"error": "Wishlist not found"}), 404

    wishlist.items = [
        item for item in wishlist.items
        if not (item.product_id == product_id and item.variant_id == variant_id and item.size == size)
    ]
    wishlist.save()

    return jsonify({
        "message": "Item removed from wishlist",
        "wishlist": {
            "items": [
                {
                    "product_id": item.product_id,
                    "variant_id": item.variant_id,
                    "size": item.size,
                    "added_at": item.added_at.isoformat()
                } for item in wishlist.items
            ]
        }
    }), 200

@wishlist_bp.route(WISHLIST_LIST, methods=['GET'])
def get_wishlist():
    user_id = get_user_id()
    if isinstance(user_id, tuple):
        return user_id

    wishlist = Wishlist.objects(user_id=user_id).first()

    if not wishlist:
        return jsonify({"items": []}), 200

    return jsonify({
        "items": [
            {
                "product_id": item.product_id,
                "variant_id": item.variant_id,
                "size": item.size,
                "added_at": item.added_at.isoformat()
            } for item in wishlist.items
        ],
        "updated_at": wishlist.updated_at.isoformat()
    }), 200