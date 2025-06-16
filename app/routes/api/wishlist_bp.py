from flask import Blueprint, request, jsonify, current_app
from app.models import ProductVariant, Products, User, Wishlist, WishlistItem
from datetime import datetime
from constants import WISHLIST_ADD, WISHLIST_REMOVE, WISHLIST_LIST, ALLOWED_SIZES
from app.utils.validation import validate_required_fields
from app.utils.utils import create_error_response
from app.utils.jwt_handlers import jwt_error_handler
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.image_upload import get_local_ip

wishlist_bp = Blueprint('wishlist', __name__)
local_ip = get_local_ip()

@wishlist_bp.route(WISHLIST_ADD, methods=['POST'])
@jwt_error_handler
@jwt_required()
def add_to_wishlist():
    user_id = get_jwt_identity()
    user = User.objects(id=user_id).first()

    try:
        data = request.get_json()
    except Exception:
        return jsonify({"error": "Invalid JSON data"}), 400

    required_fields = ['product_id', 'selected_size', 'selected_color']
    is_valid, validation_errors = validate_required_fields(data, required_fields)
    if not is_valid:
        return create_error_response(validation_errors, 400)

    product_id = data['product_id']
    selected_size = data['selected_size']
    selected_color = data['selected_color']
    quantity = int(data.get('quantity', 1))

    if selected_size not in ALLOWED_SIZES:
        return create_error_response({"error": f"Invalid size. Must be one of {ALLOWED_SIZES}"}, 400)

    product = Products.objects(id=product_id).first()
    if not product:
        return jsonify({"error": "Product not found"}), 404

    variant = ProductVariant.objects(
        product_id=product_id,
        size=selected_size,
        color_hexa_code=selected_color
    ).first()

    if not variant:
        return create_error_response({"error": "Variant not found for the specified product, size, and color"}, 404)

    wishlist_item = WishlistItem(
        product_id=product_id,
        size=selected_size,
        color=variant.color,
        color_hexa_code=variant.color_hexa_code,
        quantity=quantity
    )

    try:
        wishlist_item.validate_product(Products)
    except ValueError as e:
        return create_error_response({"error": str(e)}, 400)

    wishlist = Wishlist.objects(user_id=user_id).first()
    if not wishlist:
        wishlist = Wishlist(user_id=user_id, items=[], created_at=datetime.utcnow())

    existing_item = None
    for item in wishlist.items:
        if (item.product_id == product_id and 
            item.size == selected_size and
            item.color_hexa_code == variant.color_hexa_code):
            existing_item = item
            break

    if existing_item:
        existing_item.quantity += quantity
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
                    "size": item.size,
                    "color": item.color,
                    "color_hexa_code": item.color_hexa_code,
                    "quantity": item.quantity,
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
    user_id = get_jwt_identity()
    user = User.objects(id=user_id).first()

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
@jwt_error_handler
@jwt_required()
def get_wishlist():
    user_id = get_jwt_identity()
    user = User.objects(id=user_id).first()
    port = current_app.config.get('SERVER_PORT', 8080)
    wishlist = Wishlist.objects(user_id=user_id).first()

    if not wishlist:
        return jsonify({"items": []}), 200

    items_with_details = []
    for item in wishlist.items:
        product = Products.objects(id=item.product_id).first()
        if not product:
            continue
            
        variant = ProductVariant.objects(
            product_id=item.product_id,
            size=item.size,
            color_hexa_code=item.color_hexa_code
        ).first()
        
        items_with_details.append({
            "product_id": str(item.product_id),
            "size": item.size,
            "color": item.color,
            "color_hexa_code": item.color_hexa_code,
            "quantity": item.quantity,
            "added_at": item.added_at.isoformat(),
            "product_details": {
                "name": product.name,
                "price": float(product.price),
                "discount_price": float(product.discount_price) if product.discount_price else None,
                "final_price": float(product.final_price),
                "stock_quantity": variant.stock_quantity if variant else 0,
                "images": [
                    f"http://{local_ip}:{port}/static/uploads/{img.image_url}" 
                    for img in variant.images
                ] if variant and hasattr(variant, 'images') else []
            }
        })

    return jsonify({
        "items": items_with_details,
        "created_at": wishlist.created_at.isoformat(),
        "updated_at": wishlist.updated_at.isoformat()
    }), 200


def get_main_product_image(product):
    if hasattr(product, 'images') and product.images:
        return product.images[0].image_url
    return None