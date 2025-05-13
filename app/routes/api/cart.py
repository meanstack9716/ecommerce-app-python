from flask import Blueprint, request, jsonify, session
from app.models.cart import Cart, CartItem
from app.models.products import ProductVariant
from app.models.products import Products
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
    quantity = data.get('quantity', 1)
    color = data.get('color')

    user_id = get_user_id()
    if isinstance(user_id, tuple):
        return user_id

    if not product_id:
        return jsonify({"error": "product_id is required"}), 400

    # Validate size if provided
    if size and size not in ALLOWED_SIZES:
        return jsonify({"error": f"Invalid size. Must be one of {ALLOWED_SIZES}"}), 400
    
    if not color:
        return jsonify({"error": "color is required"}), 400

    try:
        quantity = int(quantity)
        if quantity < 1:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"error": "quantity must be a positive integer"}), 400

    product = Products.objects(id=product_id).first()
    if not product:
        return jsonify({"error": "Product not found"}), 404

    price = float(product.final_price)

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
        price = float(product.final_price)

    cart_item = CartItem(
        product_id=product_id,
        variant_id=str(variant.id) if variant else None,
        size=size,
        color=color,
        quantity=quantity,
        price=price,
        original_price=float(product.price),
        discount=float(product.price - product.final_price) if product.discount_price else 0.0
    )

    try:
        cart_item.validate_stock(Products)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    cart = Cart.objects(user_id=user_id).first()
    if not cart:
        cart = Cart(user_id=user_id, items=[], created_at=datetime.utcnow())

    existing_item = None
    for item in cart.items:
        if (item.product_id == product_id and item.variant_id == cart_item.variant_id and item.size == size and item.color == color):
            existing_item = item
            break

    if existing_item:
        existing_item.quantity += quantity
        try:
            existing_item.validate_stock(Products)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
    else:
        cart.items.append(cart_item)

    cart.updated_at = datetime.utcnow()
    cart.save()

    response_data = {
        "message": "Item added to cart",
        "cart": {
            "id": str(cart.id),
            "user_id": str(cart.user_id),
            "items": [
                {
                    "product_id": str(item.product_id),
                    "variant_id": str(item.variant_id) if item.variant_id else None,
                    "size": item.size,
                    "color": item.color,
                    "quantity": item.quantity,
                    "price": item.price,
                    "original_price": item.original_price,
                    "total_price": item.price * item.quantity
                } for item in cart.items
            ],
            "total_items": sum(item.quantity for item in cart.items),
            "total_price": sum(item.price * item.quantity for item in cart.items),
            "created_at": cart.created_at.isoformat(),
            "updated_at": cart.updated_at.isoformat()
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

    return jsonify({
        "items": [
            {
                "product_id": item.product_id,
                "variant_id": item.variant_id,
                "size": item.size,
                "color": item.color,
                "quantity": item.quantity,
                "price": item.price,
                "discount": item.discount,
                "total_price": (item.price - item.discount) * item.quantity
            } for item in cart.items
        ],
        "total_price": cart.total_price,
        "currency": cart.currency,
        "status": cart.status or "active"
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

    from app.models.order import Order
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