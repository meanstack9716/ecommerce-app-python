from flask import Blueprint, request, jsonify, session
from app.models.order import Order, OrderItem
from app.models.user import User
from app.models.address import Address
from datetime import datetime
from app.models.productCart import ProductCart
from app.models.products import Products, ProductVariant, ProductVariantImage
import random
import string
from bson import ObjectId
import decimal
from app.utils.utils import create_error_response

order_bp = Blueprint('order', __name__)

def get_user_id():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    return session['user_id']


@order_bp.route('/api/orders/new', methods=['POST'])
def place_order():
    # Authentication check
    user_id = get_user_id()
    if isinstance(user_id, tuple):
        return user_id

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    required_fields = ['cart_items_ids', 'shipping_address_id', 'payment_method']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        shipping_address = Address.objects(
            user_id=user_id,
            id=ObjectId(data['shipping_address_id'])
        ).first()

        if not shipping_address:
            return jsonify({
                "error": "Shipping address not found",
                "message": "The specified shipping address doesn't exist or doesn't belong to you"
            }), 404

        address_fields = ['line1', 'city', 'state', 'postal_code', 'country']
        if not all(getattr(shipping_address, field) for field in address_fields):
            return jsonify({
                "error": "Incomplete shipping address",
                "message": "The shipping address is missing required fields"
            }), 400

    except Exception as e:
        return jsonify({
            "error": "Invalid shipping address",
            "message": str(e)
        }), 400

    cart_items_query = ProductCart.objects(user_id=user_id)
    
    if data['cart_items_ids']:
        try:
            cart_items_ids = [ObjectId(id) for id in data['cart_items_ids']]
            cart_items = cart_items_query.filter(id__in=cart_items_ids)
        except:
            return jsonify({"error": "Invalid cart item IDs format"}), 400
    else:
        cart_items = cart_items_query
    
    if not cart_items:
        return jsonify({"error": "No cart items found"}), 400

    seller_items = {}
    for cart_item in cart_items:
        product = cart_item.product_id
        if not product:
            continue
            
        seller_id = str(product.seller_id.id) if product.seller_id else None
        if seller_id not in seller_items:
            seller_items[seller_id] = {
                'seller': product.seller_id,
                'items': []
            }
        seller_items[seller_id]['items'].append(cart_item)

    orders = []
    order_numbers = set()
    while len(order_numbers) < len(seller_items):
        order_number = 'ORD-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        order_numbers.add(order_number)
    order_numbers = list(order_numbers)

    for i, (seller_id, seller_data) in enumerate(seller_items.items()):
        order_items = []
        total_amount = decimal.Decimal('0.00')

        # Process each item in cart
        for cart_item in seller_data['items']:
            product = cart_item.product_id
            price = decimal.Decimal(str(product.price))
            discount_percent = decimal.Decimal(str(product.discount_percent)) if hasattr(product, 'discount_percent') else decimal.Decimal('0')
            final_price = price * (1 - discount_percent / 100)
            item_total = final_price * cart_item.quantity

            order_item = OrderItem(
                product_id=product.id,
                selected_size=cart_item.selected_size,
                selected_color=cart_item.selected_color,
                selected_color_name=cart_item.selected_color_name,
                quantity=cart_item.quantity,
                price=float(price),
                discount_percent=float(discount_percent),
                final_price=float(final_price),
            )
            order_items.append(order_item)
            total_amount += item_total

        try:
            order = Order(
                user_id=user_id,
                seller_id=ObjectId(seller_id) if seller_id else None,
                order_number=order_numbers[i],
                items=order_items,
                total_amount=float(total_amount),
                status='pending',
                shipping_address={
                    'id': str(shipping_address.id),
                    'address_line1': shipping_address.line1,
                    'address_line2': shipping_address.line2 if shipping_address.line2 else '',
                    'city': shipping_address.city,
                    'state': shipping_address.state,
                    'postal_code': shipping_address.postal_code,
                    'country': shipping_address.country,
                    'address_type': shipping_address.address_type if shipping_address.address_type else 'home'
                },
                payment_method=data['payment_method'],
                payment_status='pending',
                order_note=data.get('order_note', ''),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            order.save()
            orders.append({
                "order_id": str(order.id),
                "order_number": order.order_number,
                "total_amount": float(total_amount),
                "items_count": len(order_items)
            })

        except Exception as e:
            for created_order in Order.objects(id__in=[o['order_id'] for o in orders]):
                created_order.delete()
            return jsonify({
                "error": "Failed to place order",
                "message": str(e)
            }), 500

    cart_items.delete()

    return jsonify({
        "message": "Orders placed successfully",
        "orders": orders,
        "total_orders": len(orders)
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