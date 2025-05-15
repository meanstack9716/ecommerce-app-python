from flask import Blueprint, request, jsonify, session
from app.models.order import Order
from app.models.user import User
from datetime import datetime
from app.models.productCart import ProductCart
from app.models.products import Products, ProductVariant, ProductVariantImage
import random
import string

order_bp = Blueprint('order', __name__)

def get_user_id():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    return session['user_id']

@order_bp.route('/api/orders/new', methods=['POST'])
def place_order():
    user_id = get_user_id()
    if isinstance(user_id, tuple):
        return user_id

    data = request.json
    required_fields = ['cart_items_ids', 'shipping_address_id', 'payment_method']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    cart_items_query = ProductCart.objects(user_id=user_id)
    
    if data['cart_items_ids']:
        cart_items = cart_items_query.filter(id__in=data['cart_items_ids'])
    else:
        cart_items = cart_items_query
    
    if not cart_items:
        return jsonify({"error": "No cart items found"}), 400

    shipping_address = UserAddress.objects(
        user_id=user_id,
        id=data['shipping_address_id']
    ).first()
    if not shipping_address:
        return jsonify({"error": "Invalid shipping address"}), 400

    order_items = []
    total_amount = 0

    for cart_item in cart_items:
        product = Product.objects(id=cart_item.product_id).first()
        if not product:
            continue 

        price = float(product.price)
        discount_percent = float(product.discount_percent) if hasattr(product, 'discount_percent') else 0
        final_price = price * (1 - discount_percent / 100)
        item_total = final_price * cart_item.quantity

        order_item = OrderItem(
            product_id=product,
            selected_size=cart_item.selected_size,
            selected_color=cart_item.selected_color,
            selected_color_name=cart_item.selected_color_name,
            quantity=cart_item.quantity,
            price=price,
            discount_percent=discount_percent,
            final_price=final_price
        )
        order_items.append(order_item)
        total_amount += item_total

    order_number = 'ORD-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

    order = Order(
        user_id=user_id,
        seller_id=None,
        order_number=order_number,
        items=order_items,
        total_amount=total_amount,
        status='pending',
        shipping_address={
            'id': str(shipping_address.id),
            'name': shipping_address.name,
            'address_line1': shipping_address.address_line1,
            'address_line2': shipping_address.address_line2,
            'city': shipping_address.city,
            'state': shipping_address.state,
            'postal_code': shipping_address.postal_code,
            'country': shipping_address.country,
            'phone': shipping_address.phone
        },
        payment_method=data['payment_method'],
        payment_status='pending',
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    order.save()

    cart_items.delete()

    return jsonify({
        "message": "Order placed successfully",
        "order_id": str(order.id),
        "order_number": order.order_number,
        "total_amount": float(total_amount),
        "items_count": len(order_items)
    }), 201

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