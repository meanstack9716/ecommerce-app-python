from flask import Blueprint, request, jsonify, current_app
from app.models import Products, ProductVariant , User, WishlistItem
from datetime import datetime
from constants import WISHLIST_ADD, WISHLIST_REMOVE, WISHLIST_LIST, ALLOWED_SIZES, WISHLIST_REMOVE_ALL
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
        return create_error_response({"error": validation_errors}, 400)

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

    # Check if item already exists in wishlist
    existing_item = WishlistItem.objects(
        user_id=user_id,
        product_id=product_id,
        size=selected_size,
        color_hexa_code=selected_color
    ).first()

    if existing_item:
        existing_item.quantity += quantity
        existing_item.save()
    else:
        wishlist_item = WishlistItem(
            user_id=user_id,
            product_id=product_id,
            size=selected_size,
            color=variant.color,
            color_hexa_code=variant.color_hexa_code,
            quantity=quantity
        )
        wishlist_item.save()

    wishlist_items = WishlistItem.objects(user_id=user_id)

    response_data = {
        "message": "Item added to wishlist",
        "data": [
            {
                "id": str(item.id),
                "product_id": str(item.product_id),
                "size": item.size,
                "color": item.color,
                "color_hexa_code": item.color_hexa_code,
                "quantity": item.quantity,
                "added_at": item.added_at.isoformat()
            } for item in wishlist_items
        ]
    }

    return jsonify(response_data), 200

@wishlist_bp.route(WISHLIST_REMOVE, methods=['DELETE'])
@jwt_required()
@jwt_error_handler
def remove_from_wishlist():
    user_id = get_jwt_identity()
    
    try:
        data = request.get_json()
    except Exception:
        return create_error_response({"error": "Invalid JSON data"}, 400)

    item_ids = data.get('item_ids')
    
    if not item_ids or not isinstance(item_ids, list):
        return create_error_response({"error": "item_ids must be a list of wishlist item IDs"}, 400)

    delete_result = WishlistItem.objects(
        user_id=user_id,
        id__in=item_ids
    ).delete()

    if delete_result == 0:
        return create_error_response({"error": "No matching items found in your wishlist"}, 400)

    remaining_items = WishlistItem.objects(user_id=user_id)

    response_data = {
        "message": f"Removed {delete_result} items from wishlist",
        "data": [
            {
                "id": str(item.id),
                "product_id": str(item.product_id),
                "size": item.size,
                "color": item.color,
                "color_hexa_code": item.color_hexa_code,
                "quantity": item.quantity,
                "added_at": item.added_at.isoformat()
            } for item in remaining_items
        ]
    }

    return jsonify(response_data), 200


@wishlist_bp.route(WISHLIST_LIST, methods=['GET'])
@jwt_required()
@jwt_error_handler
def get_wishlist():
    user_id = get_jwt_identity()
    port = current_app.config.get('SERVER_PORT', 8080)
    
    wishlist_items = WishlistItem.objects(user_id=user_id).order_by('-added_at')
    
    items_with_details = []
    for item in wishlist_items:
        product = Products.objects(id=item.product_id).first()
        if not product:
            continue
            
        variant = ProductVariant.objects(
            product_id=item.product_id,
            size=item.size,
            color_hexa_code=item.color_hexa_code
        ).first()
        
        image_urls = []
        if variant and hasattr(variant, 'images'):
            image_urls = [
                f"http://{local_ip}:{port}/static/uploads/{img.image_url}"
                for img in variant.images
                if hasattr(img, 'image_url')
            ]
        
        items_with_details.append({
            "wishlist_item_id": str(item.id),
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
                "images": image_urls,
                "variant_id": str(variant.id) if variant else None
            }
        })

    return jsonify({
        "data": items_with_details,
        "count": len(items_with_details)
    }), 200

@wishlist_bp.route(WISHLIST_REMOVE_ALL, methods=['DELETE'])
@jwt_required()
@jwt_error_handler
def remove_all_wishlist_items():
    user_id = get_jwt_identity()
    
    delete_result = WishlistItem.objects(user_id=user_id).delete()
    
    if delete_result == 0:
        return jsonify({
            "message": "Your wishlist was already empty",
            "deleted_count": 0
        }), 200
    
    return jsonify({
        "message": "All items removed from wishlist",
        "deleted_count": delete_result
    }), 200

def get_main_product_image(product):
    if hasattr(product, 'images') and product.images:
        return product.images[0].image_url
    return None