from flask import Blueprint, request, jsonify, session
from app.models.cart import Cart, CartItem
from app.models.product import Product
from datetime import datetime
from constants import CART_ADD, CART_REMOVE, CART_LIST, CART_CHECKOUT
from bson import ObjectId

cart_bp = Blueprint('cart', __name__)

def get_user_id():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    return session['user_id']

@cart_bp.route(CART_ADD, methods=['POST'])
def add_to_cart():
    user_id = get_user_id()
    if isinstance(user_id, tuple):
        return user_id
    
    data = request.json
    product_id = data.get('product_id')
    variant_id = data.get('variant_id')
    quantity = data.get('quantity', 1)
    
    if not product_id or not isinstance(quantity, int) or quantity < 1:
        return jsonify({"error": "Invalid product_id or quantity"}), 400

    product = Product.objects(id=product_id).first()
    if not product:
        return jsonify({"error": "Product not found"}), 404

    price = product.price
    if variant_id:
        variant = product.variants.get(variant_id)
        if not variant:
            return jsonify({"error": "Variant not found"}), 404
        price = variant.get('price', price)

    cart_item = CartItem(
        product_id=product_id,
        variant_id=variant_id,
        quantity=quantity,
        price=float(price),
        original_price=float(price)
    )

    try:
        cart_item.validate_stock(Product)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    cart = Cart.objects(user_id=user_id).first()
    if not cart:
        cart = Cart(user_id=user_id, items=[])

    for item in cart.items:
        if item.product_id == product_id and item.variant_id == variant_id:
            item.quantity += quantity
            try:
                item.validate_stock(Product)
            except ValueError as e:
                return jsonify({"error": str(e)}), 400
            break
    else:
        cart.items.append(cart_item)

    cart.save()
    return jsonify({
        "message": "Item added to cart",
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
                "quantity": item.quantity,
                "price": item.price,
                "discount": item.discount,
                "total_price": (item.price - item.discount) * item.quantity
            } for item in cart.items
        ],
        "total_price": cart.total_price,
        "currency": cart.currency,
        "status": cart.status
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