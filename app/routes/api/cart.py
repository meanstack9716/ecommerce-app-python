from flask import Blueprint, request, jsonify, session
from app.models.productCart import ProductCart
from app.models.products import Products, ProductVariant, ProductVariantImage
from datetime import datetime
from constants import CART_ADD, CART_REMOVE, CART_LIST, CART_CHECKOUT, CART_REMOVE_ALL
from bson import ObjectId
from constants import ALLOWED_SIZES
from app.utils.utils import create_error_response
from app.utils.image_upload import get_local_ip
from flask import current_app



cart_bp = Blueprint('cart', __name__)

def get_user_id():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    return session['user_id']

@cart_bp.route(CART_ADD, methods=['POST'])
def add_to_cart():
    user_id_response = get_user_id()
    if isinstance(user_id_response, tuple):
        return user_id_response
    user_id = user_id_response

    if not request.is_json:
        return create_error_response({"error": "Request must be JSON"}, 400)

    try:
        data = request.get_json()
    except Exception:
        return create_error_response({"error": "Invalid JSON data"}, 400)

    if not isinstance(data, dict):
        return create_error_response({"error": "Invalid data format, expected JSON object"}, 400)

    required_fields = ['product_id', 'selected_size', 'selected_color']
    for field in required_fields:
        if field not in data or not data[field]:
            return create_error_response({"error": f"Missing required field: {field}"}, 400)

    quantity = data.get('quantity', 1)
    if not isinstance(quantity, int) or quantity <= 0:
        return create_error_response({"error": "Quantity must be a positive integer"}, 400)

    product = Products.objects(id=data['product_id']).first()
    if not product:
        return create_error_response({"error": "Product not found"}, 404)

    variant = ProductVariant.objects(
        product_id=data['product_id'],
        size=data['selected_size'],
        color_hexa_code=data['selected_color']
    ).first()

    if not variant:
        return create_error_response({"error": f"No variant found for size {data['selected_size']} and color {data['selected_color']}"}, 404)

    if variant.stock_quantity < quantity:
        return create_error_response({
            "error": f"Insufficient stock for size {data['selected_size']} and color {data['selected_color']}. Available: {variant.stock_quantity}"
        }, 400)

    selected_color_name = variant.color

    existing_item = ProductCart.objects(
        product_id=data['product_id'],
        user_id=user_id,
        selected_size=data['selected_size'],
        selected_color=data['selected_color']
    ).first()

    if existing_item:
        new_quantity = existing_item.quantity + quantity
        if new_quantity > variant.stock_quantity:
            return create_error_response({
                "error": f"Cannot add {new_quantity} items. Only {variant.stock_quantity} available in stock."
            }, 400)

        existing_item.quantity = new_quantity
        existing_item.updated_at = datetime.utcnow()
        existing_item.selected_color_name = selected_color_name
        existing_item.save()
        cart_item = existing_item
        message = "Cart item quantity updated"
    else:
        cart_item = ProductCart(
            product_id=data['product_id'],
            user_id=user_id,
            quantity=quantity,
            selected_size=data['selected_size'],
            selected_color=data['selected_color'],
            selected_color_name=selected_color_name 
        )
        cart_item.save()
        message = "Item added to cart"

    response_data = {
        "message": message,
        "data": {
            "id": str(cart_item.id),
            "product_id": str(cart_item.product_id),
            "user_id": str(cart_item.user_id),
            "quantity": cart_item.quantity,
            "selected_size": cart_item.selected_size,
            "selected_color": cart_item.selected_color,
            "selected_color_name": cart_item.selected_color_name
        }
    }

    return jsonify(response_data), 200

@cart_bp.route(CART_LIST, methods=['GET'])
def get_cart():
    user_id = get_user_id()
    if isinstance(user_id, tuple):
        return user_id
    local_ip = get_local_ip()
    port = current_app.config.get('SERVER_PORT', 8080)
    
    cart_items = ProductCart.objects(user_id=user_id).select_related()
    
    cart_data = []
    for item in cart_items:
        product_data = None
        if item.product_id:
            product = item.product_id
            
            sizes = []
            # Only include variants that match the selected color
            for variant in product.variants:
                if variant.color_hexa_code == item.selected_color:  # Filter by selected color
                    size_exists = False
                    for size in sizes:
                        if size['value'] == variant.size:
                            size_exists = True
                            size['variants'].append({
                                'value': variant.color_hexa_code,
                                'name': variant.color,
                                'stock_quantity': variant.stock_quantity,
                                'id': str(variant.id)
                            })
                            break
                    
                    if not size_exists:
                        sizes.append({
                            'product_id': str(product.id),
                            'value': variant.size,
                            'size_type': 'standard',
                            'id': str(variant.id),
                            'variants': [{
                                'value': variant.color_hexa_code,
                                'name': variant.color,
                                'stock_quantity': variant.stock_quantity,
                                'id': str(variant.id)
                            }]
                        })
            
            # Build gallery with only the selected color's images
            gallery = []
            for variant in product.variants:
                if variant.color_hexa_code == item.selected_color:  # Filter by selected color
                    for image in variant.images:
                        gallery.append({
                            'color': variant.color,
                            'id': str(image.id),
                            'img_url': f"http://{local_ip}:{port}/static/uploads/{image.image_url}"
                        })
            
            product_data = {
                'id': str(product.id),
                'title': product.name,
                'details': product.details,
                'description': product.description,
                'stock_quantity': product.stock_quantity,
                'price': float(product.price),
                'discount_price': float(product.discount_price) if product.discount_price else None,
                'final_price': float(product.final_price),
                'status': product.status,
                'sizes': sizes,
                'gallery': gallery
            }
        
        cart_data.append({
            'id': str(item.id),
            'selected_size': item.selected_size,
            'selected_color': item.selected_color,
            'selected_color_name': item.selected_color_name,
            'quantity': item.quantity,
            'product': product_data,
        })
    
    return {
        'status': 'success',
        'data': cart_data
    }
    
@cart_bp.route(CART_REMOVE, methods=['POST'])
def remove_from_cart():
    user_id = get_user_id()
    if isinstance(user_id, tuple):
        return user_id

    data = request.json
    item_ids = data.get('item_ids')

    if not item_ids or not isinstance(item_ids, list):
        return create_error_response({"error": "item_ids array is required"}, 400)

    delete_result = ProductCart.objects(
        id__in=item_ids,
        user_id=user_id
    ).delete()

    if delete_result == 0:
        return create_error_response({
            "error": "No matching items found in cart",
            "details": "Either items don't exist or don't belong to this user"
        }, 404)

    remaining_items = ProductCart.objects(user_id=user_id)
    
    cart_data = [{
        "item_id": str(item.id),
        "product_id": str(item.product_id.id) if item.product_id else None,
        "selected_size": item.selected_size,
        "selected_color": item.selected_color,
        "selected_color_name": item.selected_color_name,
        "quantity": item.quantity,
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat()
    } for item in remaining_items]

    return jsonify({
        "status": "success",
        "message": f"Removed {delete_result} item(s) from cart",
        "data": {
            "remaining_items": cart_data,
            "remaining_count": len(cart_data)
        }
    }), 200


@cart_bp.route(CART_REMOVE_ALL, methods=['DELETE'])
def remove_all_from_cart():
    user_id = get_user_id()
    if isinstance(user_id, tuple):
        return user_id

    delete_result = ProductCart.objects(user_id=user_id).delete()

    if delete_result == 0:
        return create_error_response({
            "error": "No items found in cart",
            "details": "The cart is already empty"
        }, 404)

    return jsonify({
        "status": "success",
        "message": f"Removed all {delete_result} item(s) from cart",
        "data": {
            "remaining_items": [],
            "remaining_count": 0
        }
    }), 200