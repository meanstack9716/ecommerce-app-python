from flask import Blueprint, request, jsonify, session
from app.models.order import Order
from app.models.user import User
from datetime import datetime
from app.models.cart import Cart, CartItem
from app.models.products import Products, ProductVariant, ProductVariantImage

order_bp = Blueprint('order', __name__)

def get_user_id():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    return session['user_id']

@order_bp.route('/api/orders', methods=['POST'])
def create_order():
    user_id = get_user_id()
    if isinstance(user_id, tuple):
        return user_id

    data = request.json
    required_fields = ['shipping_address', 'shipping_method', 'payment_method']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    cart = Cart.objects(user_id=user_id).first()
    if not cart or not cart.items:
        return jsonify({"error": "Cart is empty"}), 400

    try:
        cart.validate_cart(Products)
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

@order_bp.route('/api/orders', methods=['GET'])
def get_orders():
    """Get all orders for current user"""
    user_id = get_user_id()
    if isinstance(user_id, tuple):
        return user_id

    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    orders = Order.objects(user_id=user_id).order_by('-created_at') \
             .skip((page-1)*per_page).limit(per_page)
    
    total = Order.objects(user_id=user_id).count()
    
    return jsonify({
        'data': [{
            'id': str(order.id),
            'total_price': float(order.total_price),
            'status': order.status,
            'payment_status': order.payment_status,
            'created_at': order.created_at.isoformat(),
            'item_count': len(order.items)
        } for order in orders],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total
        }
    })

@order_bp.route('/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    """Get order details"""
    user_id = get_user_id()
    if isinstance(user_id, tuple):
        return user_id

    order = Order.objects(id=order_id, user_id=user_id).first()
    if not order:
        return jsonify({"error": "Order not found"}), 404

    return jsonify({
        'id': str(order.id),
        'items': [{
            'product_id': str(item.product_id.id),
            'product_name': item.product_id.name,
            'variant_id': str(item.variant_id.id) if item.variant_id else None,
            'quantity': item.quantity,
            'price': float(item.price),
            'total_price': float(item.total_price)
        } for item in order.items],
        'total_price': float(order.total_price),
        'status': order.status,
        'payment_status': order.payment_status,
        'shipping_address': order.shipping_address,
        'shipping_method': order.shipping_method,
        'tracking_number': order.tracking_number,
        'created_at': order.created_at.isoformat()
    })

@order_bp.route('/orders/<order_id>/cancel', methods=['POST'])
def cancel_order(order_id):
    user_id = get_user_id()
    if isinstance(user_id, tuple):
        return user_id

    order = Order.objects(id=order_id, user_id=user_id).first()
    if not order:
        return jsonify({"error": "Order not found"}), 404

    if order.status not in ['pending', 'processing']:
        return jsonify({"error": "Order cannot be cancelled at this stage"}), 400

    order.update_status('cancelled')
    return jsonify({"message": "Order cancelled successfully"})

@order_bp.route('/admin/orders', methods=['GET'])
def admin_get_orders():
    
    status = request.args.get('status')
    query = {}
    if status:
        query['status'] = status
    
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    
    orders = Order.objects(**query).order_by('-created_at') \
             .skip((page-1)*per_page).limit(per_page)
    
    return jsonify({
        'data': [{
            'id': str(order.id),
            'user_id': str(order.user_id.id),
            'total_price': float(order.total_price),
            'status': order.status,
            'created_at': order.created_at.isoformat()
        } for order in orders]
    })

@order_bp.route('/admin/orders/<order_id>/status', methods=['PUT'])
def admin_update_order_status(order_id):
        
    data = request.json
    new_status = data.get('status')
    tracking_number = data.get('tracking_number')
    
    if not new_status:
        return jsonify({"error": "Status is required"}), 400
    
    order = Order.objects(id=order_id).first()
    if not order:
        return jsonify({"error": "Order not found"}), 404
    
    try:
        order.update_status(new_status)
        if tracking_number:
            order.tracking_number = tracking_number
            order.save()
        return jsonify({"message": "Order status updated"})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400