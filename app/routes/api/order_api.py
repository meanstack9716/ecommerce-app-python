from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Address, Seller, User, ProductCart, Products, ProductVariant, ProductVariantImage, Order, OrderItem
from datetime import datetime, timedelta
import random
import string
from bson import ObjectId
import decimal
from app.utils.utils import create_error_response
from constants import ORDER_PLACE_API, ORDER_LIST_API, GET_ORDER_STATUS_TYPES, ORDER_STATUS
from app.utils.jwt_handlers import jwt_error_handler
from mongoengine.queryset.visitor import Q

order_bp = Blueprint('order', __name__)

@order_bp.route(ORDER_PLACE_API, methods=['POST'])
@jwt_error_handler
@jwt_required()
def place_order():
    user_id = get_jwt_identity()
    user = User.objects(id=user_id).first()
    
    if not user:
        return create_error_response({'error': 'User not found'}, 404)

    data = request.get_json()
    if not data:
        return create_error_response({'error': 'No data provided'}, 400)

    required_fields = ['cart_items_ids', 'shipping_address_id', 'payment_method']
    is_valid, validation_errors = validate_fields(data, required_fields)
    if not is_valid:
        return create_error_response(validation_errors, 400)

    try:
        shipping_address = Address.objects(
            user_id=user_id,
            id=ObjectId(data['shipping_address_id'])
        ).first()

        if not shipping_address:
            return create_error_response({
                'error': 'Shipping address not found',
                'message': 'The specified shipping address doesn\'t exist or doesn\'t belong to you'
            }, 404)

        address_fields = ['line1', 'city', 'state', 'postal_code', 'country']
        if not all(getattr(shipping_address, field) for field in address_fields):
            return create_error_response({
                'error': 'Incomplete shipping address',
                'message': 'The shipping address is missing required fields'
            }, 400)

    except Exception as e:
        return create_error_response({
            'error': 'Invalid shipping address',
            'message': str(e)
        }, 400)

    cart_items_query = ProductCart.objects(user_id=user_id)
    
    if data['cart_items_ids']:
        try:
            cart_items_ids = [ObjectId(id) for id in data['cart_items_ids']]
            cart_items = cart_items_query.filter(id__in=cart_items_ids)
        except:
            return create_error_response({'error': 'Invalid cart item IDs format'}, 400)
    else:
        cart_items = cart_items_query
    
    if not cart_items:
        return create_error_response({'error': 'No cart items found'}, 400)

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
                    'type': shipping_address.type if shipping_address.type else 'home'
                },
                payment_method=data['payment_method'],
                payment_status='pending',
                order_note=data.get('order_note', ''),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            order.save()
            orders.append({
                'order_id': str(order.id),
                'order_number': order.order_number,
                'total_amount': float(total_amount),
                'items_count': len(order_items)
            })

        except Exception as e:
            for created_order in Order.objects(id__in=[o['order_id'] for o in orders]):
                created_order.delete()
            return create_error_response({
                'error': 'Failed to place order',
                'message': str(e)
            }, 500)

    cart_items.delete()

    return jsonify({
        'message': 'Orders placed successfully',
        'orders': orders,
        'total_orders': len(orders)
    }), 201

@order_bp.route(ORDER_LIST_API, methods=['GET'])
@jwt_error_handler
@jwt_required()
def get_order_lists():
    user_id = get_jwt_identity()
    user = User.objects(id=user_id).first()

    if not user:
        return create_error_response({'status': 'error', 'message': 'User not found', 'data': None}, 404)
    
    search = request.args.get('search', '').strip()
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    
    orders = Order.objects(user_id=user_id)
    
    if search:
        matching_products = Products.objects(name__icontains=search).only('id')
        product_ids = [str(p.id) for p in matching_products]
        
        matching_sellers = Seller.objects(businessName__icontains=search).only('id')
        seller_ids = [str(s.id) for s in matching_sellers]
        
        orders = orders.filter(
            Q(order_number__icontains=search) |
            Q(items__product_id__in=product_ids) |
            Q(seller_id__in=seller_ids)
        )
    
    if from_date:
        try:
            from_date_obj = datetime.strptime(from_date, '%Y-%m-%d')
            orders = orders.filter(created_at__gte=from_date_obj)
        except ValueError:
            pass
    
    if to_date:
        try:
            to_date_obj = datetime.strptime(to_date, '%Y-%m-%d') + timedelta(days=1)
            orders = orders.filter(created_at__lte=to_date_obj)
        except ValueError:
            pass
    
    orders = orders.order_by('-created_at')
    
    def get_safe_reference(ref):
        try:
            return str(ref.id) if ref else None
        except:
            return None
    
    order_list = []
    for order in orders:
        seller_details = {}
        if order.seller_id:
            seller = Seller.objects(id=order.seller_id.id).first()
            if seller:
                seller_details = {
                    'seller_name': seller.businessName,
                    'seller_contact': seller.businessMobile,
                    'seller_email': seller.businessEmail
                }
        
        order_data = {
            'id': str(order.id),
            'order_number': order.order_number,
            'total_amount': float(order.total_amount),
            'orderStatus': order.status.capitalize(),
            'payment_method': order.payment_method,
            'payment_status': order.payment_status.capitalize(),
            'created_at': order.created_at.isoformat() + 'Z' if order.created_at else None,
            'seller_details': seller_details,
            'items': [{
                'product_id': get_safe_reference(item.product_id),
                'product_name': item.product_id.name if item.product_id else None,
                'selected_size': item.selected_size,
                'selected_color': item.selected_color,
                'quantity': item.quantity,
                'price': float(item.price),
                'final_price': float(item.final_price)
            } for item in order.items]
        }
        order_list.append(order_data)
    
    return jsonify({
        'status': 'success',
        'message': 'Orders fetched successfully',
        'data': order_list
    })


@order_bp.route(GET_ORDER_STATUS_TYPES, methods=['GET'])
@jwt_error_handler
@jwt_required()
def get_order_statuses():
    return jsonify({
        'status': 'success',
        'message': 'Order statuses fetched successfully',
        'data': ORDER_STATUS
    }), 200
