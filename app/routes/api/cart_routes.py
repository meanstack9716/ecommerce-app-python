from flask import Blueprint, request, jsonify
from app.models.cart import Cart, CartItem
from datetime import datetime
from constants import CART_ADD, CART_REMOVE, CART_LIST, CART_CHECKOUT

cart_bp = Blueprint('cart', __name__)

@cart_bp.route(CART_ADD, methods=['POST'])
def add_to_cart():
    data = request.json
    user_id = data.get('user_id')
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    price = data.get('price')

    cart = Cart.objects(user_id=user_id).first()
    if not cart:
        cart = Cart(user_id=user_id, items=[])

    existing_item = next((item for item in cart.items if item.product_id == product_id), None)
    if existing_item:
        existing_item.quantity += quantity
    else:
        cart.items.append(CartItem(product_id=product_id, quantity=quantity, price=price))

    cart.updated_at = datetime.utcnow()
    cart.save()
    return jsonify({"message": "Item added to cart"}), 200

@cart_bp.route(CART_REMOVE, methods=['POST'])
def remove_from_cart():
    data = request.json
    user_id = data.get('user_id')
    product_id = data.get('product_id')

    cart = Cart.objects(user_id=user_id).first()
    if not cart:
        return jsonify({"message": "Cart not found"}), 404

    cart.items = [item for item in cart.items if item.product_id != product_id]
    cart.updated_at = datetime.utcnow()
    cart.save()
    return jsonify({"message": "Item removed from cart"}), 200

@cart_bp.route(CART_LIST, methods=['GET'])
def get_cart():
    user_id = request.args.get('user_id')
    cart = Cart.objects(user_id=user_id).first()
    if not cart:
        return jsonify({"items": []}), 200

    items = [
        {
            "product_id": item.product_id,
            "quantity": item.quantity,
            "price": item.price,
            "total_price": item.quantity * item.price
        }
        for item in cart.items
    ]
    return jsonify({"items": items}), 200

@cart_bp.route(CART_CHECKOUT, methods=['POST'])
def checkout():
    data = request.json
    user_id = data.get('user_id')

    cart = Cart.objects(user_id=user_id).first()
    if not cart or not cart.items:
        return jsonify({"message": "Cart is empty"}), 400

    cart.items = []
    cart.updated_at = datetime.utcnow()
    cart.save()
    return jsonify({"message": "Order placed successfully"}), 200
