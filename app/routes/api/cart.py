from flask import Blueprint, request, jsonify, session
from app.models.productCart import ProductCart
from app.models.products import Products, ProductVariant, ProductVariantImage
from datetime import datetime
from constants import CART_ADD, CART_REMOVE, CART_LIST, CART_CHECKOUT
from bson import ObjectId
from constants import ALLOWED_SIZES

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
        return jsonify({"error": "Request must be JSON"}), 400

    try:
        data = request.get_json()
    except Exception:
        return jsonify({"error": "Invalid JSON data"}), 400

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid data format, expected JSON object"}), 400

    required_fields = ['product_id', 'selected_size', 'selected_color']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    quantity = data.get('quantity', 1)
    if not isinstance(quantity, int) or quantity <= 0:
        return jsonify({"error": "Quantity must be a positive integer"}), 400

    product = Products.objects(id=data['product_id']).first()
    if not product:
        return jsonify({"error": "Product not found"}), 404

    variant = ProductVariant.objects(
        product_id=data['product_id'],
        size=data['selected_size'],
        color_hexa_code=data['selected_color']
    ).first()

    if not variant:
        return jsonify({"error": f"No variant found for size {data['selected_size']} and color {data['selected_color']}"}), 404

    if variant.stock_quantity < quantity:
        return jsonify({
            "error": f"Insufficient stock for size {data['selected_size']} and color {data['selected_color']}. Available: {variant.stock_quantity}"
        }), 400

    # Get color name from variant
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
            return jsonify({
                "error": f"Cannot add {new_quantity} items. Only {variant.stock_quantity} available in stock."
            }), 400

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
        "cart_item": {
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


@cart_bp.route(CART_REMOVE, methods=['POST'])
def remove_from_cart():
    user_id = get_user_id()
    if isinstance(user_id, tuple):
        return user_id

    data = request.json
    product_id = data.get('product_id')
    variant_id = data.get('variant_id')

    if not product_id:
        return jsonify({"error": "product_id is required"}), 400

    cart = Cart.objects(user_id=user_id).first()
    if not cart:
        return jsonify({"error": "Cart not found"}), 404

    cart.items = [
        item for item in cart.items
        if not (item.product_id == product_id and item.variant_id == variant_id)
    ]
    cart.save()
    return jsonify({
        "message": "Item removed from cart",
        "cart": {
            "items": [
                {
                    "product_id": item.product_id,
                    "variant_id": item.variant_id,
                    "quantity": item.quantity,
                    "price": item.price,
                    "discount": item.discount,
                    "total_price": (item.price - item.discount) * item.quantity
                } for item in cart.items
            ],
            "total_price": cart.total_price
        }
    }), 200

@cart_bp.route(CART_LIST, methods=['GET'])
def get_cart():
    user_id = get_user_id()
    if isinstance(user_id, tuple):
        return user_id

    cart = Cart.objects(user_id=user_id).first()

    if not cart:
        return jsonify({"items": [], "total_price": 0.0}), 200

    items = []
    for item in cart.items:
        product = Products.objects(id=item.product_id).first()

        variant = ProductVariant.objects(id=item.variant_id).first() if item.variant_id else None
        variant_data = None

        product_image = None
        if item.product_id:
            first_variant = ProductVariant.objects(product_id=item.product_id).first()
            if first_variant:
                first_image = ProductVariantImage.objects(variant_id=first_variant.id).first()
                if first_image:
                    product_image = {
                        "image_url": first_image.image_url,
                        "alt_text": first_image.alt_text
                    }

        item_data = {
            "product_id": str(item.product_id),
            "size": item.size,
            "color": item.color,
            "quantity": item.quantity,
            "product": {
                "name": product.name if product else "Unknown Product",
                "details": product.details if product else None,
                "description": product.description if product else None,
                "sku_number": product.sku_number if product else None,
                "category_id": str(product.category_id.id) if product and product.category_id else None,
                "subcategory_id": str(product.subcategory_id.id) if product and product.subcategory_id else None,
                "subsubcategory_id": str(product.subsubcategory_id.id) if product and product.subsubcategory_id else None,
                "brand_id": str(product.brand_id.id) if product and product.brand_id else None,
                "material": product.material if product else None,
                "price": float(product.price) if product else 0.0,
                "discount_percentage": float(product.discount_price) if product and product.discount_price else None,
                "final_price": float(product.final_price) if product else 0.0,
                "stock_quantity": product.stock_quantity if product else 0,
                "image": product_image
            },
        }
        items.append(item_data)

    return jsonify({
        "items": items,
    }), 200

@cart_bp.route(CART_CHECKOUT, methods=['POST'])
def checkout():
    user_id = get_user_id()
    if isinstance(user_id, tuple):
        return user_id

    data = request.json
    shipping_address = data.get('shipping_address')
    shipping_method = data.get('shipping_method')

    cart = Cart.objects(user_id=user_id).first()
    if not cart or not cart.items:
        return jsonify({"error": "Cart is empty"}), 400

    try:
        cart.validate_cart(Product)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    order = Order(
        user_id=user_id,
        items=cart.items,
        total_price=cart.total_price,
        currency=cart.currency,
        shipping_address=shipping_address,
        shipping_method=shipping_method,
        status='pending'
    )
    order.save()

    cart.items = []
    cart.shipping_address = shipping_address
    cart.shipping_method = shipping_method
    cart.save()

    return jsonify({
        "message": "Order placed successfully",
        "order_id": str(order.id),
        "total_price": order.total_price
    }), 200