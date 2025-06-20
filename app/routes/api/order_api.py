from flask import Blueprint, request, jsonify, redirect, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Address, Seller, User, ProductCart, Products, ProductVariant, ProductVariantImage, Order, OrderItem, Category, SubCategory, SubSubCategory, PromoCode
from datetime import datetime, timedelta
import random
import string
import requests
import os
import json
from bson import ObjectId
import decimal
from app.utils.utils import create_error_response
from constants import ORDER_PLACE_API, ORDER_LIST_API, GET_ORDER_STATUS_TYPES, ORDER_STATUS, CREATE_RAZORPAY_PAYMENT_LINK, PAYMENT_CALLBACK_API, RAZOR_PAY_PAYMENT_LINK, VERIFY_PAYMENT
from app.utils.jwt_handlers import jwt_error_handler
from mongoengine.queryset.visitor import Q
from app.utils.validation import validate_required_fields

order_bp = Blueprint('order', __name__)

@order_bp.route(ORDER_PLACE_API, methods=['POST'])
@jwt_error_handler
@jwt_required()
def place_order():
    user_id = get_jwt_identity()
    try:
        user = User.objects(id=user_id).first()
    except DoesNotExist:
        return create_error_response({'error': 'User not found'}, 404)
    
    if not user:
        return create_error_response({'error': 'User not found'}, 404)

    data = request.get_json()
    if not data:
        return create_error_response({'error': 'No data provided'}, 400)

    required_fields = ['cart_items_ids', 'shipping_address_id', 'payment_method']
    is_valid, validation_errors = validate_required_fields(data, required_fields)
    if not is_valid:
        return create_error_response(validation_errors, 400)

    valid_payment_methods = ['cod', 'card']
    if data['payment_method'] not in valid_payment_methods:
        return create_error_response({'error': 'Invalid payment method'}, 400)

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
        except Exception:
            return create_error_response({'error': 'Invalid cart item IDs format'}, 400)
    else:
        cart_items = cart_items_query
    
    if not cart_items:
        return create_error_response({'error': 'No cart items found'}, 400)

    promo_code = None
    promo_discount = decimal.Decimal('0.00')
    if 'promo_code' in data and data['promo_code']:
        promo_code_str = data['promo_code'].upper().strip()
        current_datetime = datetime.utcnow()
        
        try:
            total_amount = decimal.Decimal('0.00')
            for item in cart_items:
                product = item.product_id
                if product:
                    final_price = decimal.Decimal(str(product.final_price))
                    total_amount += final_price * item.quantity

            promo_code = PromoCode.objects(
                code=promo_code_str,
                is_active=True,
                start_date__lte=current_datetime
            ).first()

            if not promo_code:
                return create_error_response({'error': 'Invalid or expired promo code'}, 400)

            if promo_code.expiry_date and promo_code.expiry_date < current_datetime:
                return create_error_response({'error': 'Promo code has expired'}, 400)

            if promo_code.only_first_order and Order.objects(user_id=user_id).count() > 0:
                return create_error_response({'error': 'This promo code is only valid for first orders'}, 400)

            if total_amount < decimal.Decimal(str(promo_code.min_order_amount)):
                return create_error_response({
                    'error': f'Minimum order amount of {promo_code.min_order_amount} required'
                }, 400)

            if promo_code.max_uses and promo_code.used_count >= promo_code.max_uses:
                return create_error_response({'error': 'Promo code usage limit reached'}, 400)

            promo_discount = promo_code.calculate_discount(float(total_amount))
            promo_discount = decimal.Decimal(str(promo_discount))

        except Exception as e:
            return create_error_response({'error': f'Promo code validation failed: {str(e)}'}, 400)

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

    order_numbers = set()
    while len(order_numbers) < len(seller_items):
        order_number = 'ORD-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        order_numbers.add(order_number)
    order_numbers = list(order_numbers)

    orders = []
    payment_links = []

    try:
        for i, (seller_id, seller_data) in enumerate(seller_items.items()):
            total_amount = decimal.Decimal('0.00')
            order_items = []
            
            for cart_item in seller_data['items']:
                product = cart_item.product_id
                price = decimal.Decimal(str(product.price))
                discount_percent = decimal.Decimal(str(product.discount_percent)) if hasattr(product, 'discount_percent') else decimal.Decimal('0')
                final_price = price * (1 - discount_percent / 100)
                total_amount += final_price * cart_item.quantity

                order_item = OrderItem(
                    product_id=product,
                    selected_size=cart_item.selected_size,
                    selected_color=cart_item.selected_color,
                    selected_color_name=cart_item.selected_color_name,
                    quantity=cart_item.quantity,
                    price=price,
                    discount_percent=discount_percent,
                    final_price=int(final_price * 100)
                )
                order_items.append(order_item)

            seller_promo_discount = decimal.Decimal('0.00')
            if promo_code:
                seller_ratio = total_amount / (total_amount + sum(o['total_amount'] for o in orders))
                seller_promo_discount = promo_discount * seller_ratio
                total_amount -= seller_promo_discount

            if total_amount < decimal.Decimal('1.00'):
                return create_error_response({
                    'error': 'Invalid amount',
                    'message': 'Total amount must be at least 1 INR'
                }, 400)

            order = Order(
                user_id=user,
                seller_id=seller_data['seller'] if seller_data['seller'] else None,
                order_number=order_numbers[i],
                items=order_items,
                total_amount=total_amount,
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
                applied_promo_code=promo_code,
                promo_code_discount=seller_promo_discount,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            if data['payment_method'] == 'card':
                customer_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Customer"
                payment_link = generate_razorpay_payment_link(
                    amount=float(total_amount),
                    reference_id=order_numbers[i],
                    customer_name=customer_name,
                    customer_email=user.email,
                    customer_phone=user.phone_number if hasattr(user, 'phone_number') and user.phone_number else '',
                    description=f"Order {order_numbers[i]}",
                )
                payment_links.append({
                    'order_number': order_numbers[i],
                    'payment_link_id': payment_link['id'],
                    'payment_link_url': payment_link['short_url'],
                    'amount': total_amount
                })
                order.payment_link_id = payment_link['id']

            order.save()
            orders.append({
                'order_id': str(order.id),
                'order_number': order.order_number, 
                'amount': float(total_amount),
                'items_count': len(order_items),
                'promo_discount': float(seller_promo_discount)
            })

        if promo_code:
            promo_code.used_count += 1
            promo_code.save()

        response_data = {
            'message': f"{'Payment links and orders' if data['payment_method'] == 'card' else 'Orders'} created successfully",
            'orders': orders,
            'promo_code': promo_code.code if promo_code else None,
            'total_promo_discount': float(promo_discount) if promo_code else 0,
            'payment_links': [{
                'payment_link_id': pl['payment_link_id'],
                'payment_link_url': pl['payment_link_url'],
                'amount': float(pl['amount']),
                'order_number': pl['order_number']
            } for pl in payment_links] if data['payment_method'] == 'card' else []
        }

        return jsonify(response_data), 201

    except Exception as e:
        for order in Order.objects(order_number__in=[o['order_number'] for o in orders]):
            order.delete()
        return create_error_response({
            'error': 'Failed to create order',
            'message': str(e)
        }, 500)


@order_bp.route(PAYMENT_CALLBACK_API, methods=['GET'])
def payment_callback():
    try:
        payment_id = request.args.get('razorpay_payment_id')
        payment_link_id = request.args.get('razorpay_payment_link_id')
        payment_link_reference_id = request.args.get('razorpay_payment_link_reference_id')
        order_number = request.args.get('order_number')

        if not all([payment_id, payment_link_id, payment_link_reference_id, order_number]):
            return create_error_response({
                'error': 'Invalid callback parameters',
                'message': 'Missing required callback parameters'
            }, 400)

        payment_link = get_razorpay_payment_link(payment_link_id)
        if payment_link['status'] != 'paid':
            return create_error_response({
                'error': 'Payment not completed',
                'message': 'Payment link status is not paid'
            }, 400)

        order = Order.objects(
            order_number=order_number,
            payment_link_id=payment_link_id
        ).first()

        if not order:
            return create_error_response({
                'error': 'Order not found',
                'message': 'No matching order found'
            }, 404)

        order.payment_id = payment_id
        order.payment_status = 'paid'
        order.status = 'confirmed'
        order.updated_at = datetime.utcnow()
        order.save()
        app_base_url = os.getenv('APP_BASE_URL')
        app_redirect_url = f"ecommerce://order-success?order_number={order_number}&status=success"
        return redirect(app_redirect_url, code=302)

    except Exception as e:
        app_redirect_url = f"{os.getenv('APP_BASE_URL')}/order-failed?error={str(e)}"
        return redirect(app_redirect_url, code=302)

@order_bp.route('/order-success')
def order_success():
    order_number = request.args.get('order_number')
    status = request.args.get('status')
    return f"Order {order_number} status: {status}"

@order_bp.route(VERIFY_PAYMENT, methods=['POST'])
@jwt_required()
def verify_payment():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    required_fields = ['order_number', 'payment_id']
    is_valid, validation_errors = validate_required_fields(data, required_fields)
    if not is_valid:
        return create_error_response(validation_errors, 400)

    try:
        order = Order.objects(
            user_id=user_id,
            order_number=data['order_number'],
            payment_id=data['payment_id']
        ).first()

        if not order:
            return create_error_response({'error': 'Order not found'}, 404)

        payment_link = get_razorpay_payment_link(order.payment_link_id)
        if payment_link['status'] != 'paid':
            return create_error_response({
                'error': 'Payment not verified',
                'message': 'Payment status is not paid'
            }, 400)

        if order.payment_status != 'paid':
            order.payment_status = 'paid'
            order.status = 'confirmed'
            order.updated_at = datetime.utcnow()
            order.save()

        return jsonify({
            'message': 'Payment verified successfully',
            'order_number': order.order_number,
            'status': order.status
        }), 200

    except Exception as e:
        return create_error_response({
            'error': 'Payment verification failed',
            'message': str(e)
        }, 500)

def generate_razorpay_payment_link(amount, reference_id, customer_name, customer_email, customer_phone='', description=None):
    url = RAZOR_PAY_PAYMENT_LINK
    amount_in_paise = int(amount * 100)
    
    if amount_in_paise < 100:
        raise ValueError("Amount must be at least 1 INR")

    expire_by = int((datetime.utcnow() + timedelta(days=7)).timestamp())
    
    payload = {
        'amount': amount_in_paise,
        'currency': 'INR',
        'description': description or f"Order {reference_id}",
        'customer': {
            'name': customer_name,
            'email': customer_email,
            'contact': customer_phone or ''
        },
        'reference_id': reference_id,
        'notify': {
            'sms': bool(customer_phone),
            'email': bool(customer_email)
        },
        'reminder_enable': True,
        'expire_by': expire_by,
        'notes': {
            'order_number': reference_id
        },
        'callback_url': f"ecommerce://payment-callback?order_number={reference_id}",
        'callback_method': 'get'
    }

    auth = (os.getenv('RAZORPAY_KEY_ID'), os.getenv('RAZORPAY_KEY_SECRET'))
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, data=json.dumps(payload), auth=auth, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        error_message = str(e)
        try:
            error_details = response.json()
            error_message = error_details.get('error', {}).get('description', str(e))
        except ValueError:
            pass
        raise Exception(f"Razorpay payment link creation failed: {error_message}")

def get_razorpay_payment_link(payment_link_id):
    url = f"https://api.razorpay.com/v1/payment_links/{payment_link_id}"
    auth = (os.getenv('RAZORPAY_KEY_ID'), os.getenv('RAZORPAY_KEY_SECRET'))
    
    try:
        response = requests.get(url, auth=auth)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        try:
            error_details = response.json()
            error_message = error_details.get('error', {}).get('description', str(e))
        except ValueError:
            error_message = str(e)
        raise Exception(f"Razorpay payment link fetch failed: {error_message}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Razorpay payment link fetch failed: {str(e)}")

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
    status = request.args.get('status')
    
    orders = Order.objects(user_id=user_id)
    
    if search:
        product_ids = [str(p.id) for p in Products.objects(name__icontains=search).only('id')]
        seller_ids = [str(s.id) for s in Seller.objects(businessName__icontains=search).only('id')]
        
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
    
    if status:
        orders = orders.filter(status=status)
    
    orders = orders.order_by('-created_at')
    
    order_list = []
    for order in orders:
        seller = Seller.objects(id=order.seller_id.id).first() if order.seller_id else None
        
        promo_code = None
        if order.applied_promo_code:
            promo_code = PromoCode.objects(id=order.applied_promo_code.id).first()
        
        items = []
        for idx, item in enumerate(order.items):
            product = Products.objects(id=item.product_id.id).first() if item.product_id else None
            if not product:
                continue
                
            category = Category.objects(id=product.category_id.id).first() if product.category_id else None
            sub_category = SubCategory.objects(id=product.subcategory_id.id).first() if product.subcategory_id else None
            
            gallery = []
            sizes = []
            if hasattr(product, 'variants'):
                for variant in product.variants:
                    if variant.color_hexa_code == item.selected_color or variant.color == item.selected_color_name:
                        if hasattr(variant, 'images'):
                            for img in variant.images:
                                gallery.append({
                                    'color': variant.color,
                                    'id': str(img.id),
                                    'img_url': url_for('serve_uploaded_files', filename=img.image_url, _external=True) if img.image_url else None 
                                    
                                })
                    
                    if not any(size['value'] == variant.size for size in sizes):
                        sizes.append({
                            'value': variant.size,
                            'size_type': 'standard',
                            'id': str(variant.id)
                        })
            
            product_data = {
                'id': str(product.id),
                'title': product.name,
                'price': float(product.price),
                'final_price': float(product.final_price),
                'thumbnail_url': getattr(product, 'thumbnail_url', None),
                'category': {
                    'name': category.name if category else None,
                    'id': str(category.id) if category else None
                } if category else None,
                'sub_category': {
                    'name': sub_category.name if sub_category else None,
                    'id': str(sub_category.id) if sub_category else None
                } if sub_category else None,
                'seller': {
                    'business_name': seller.businessName if seller else None,
                    'id': str(seller.id) if seller else None
                },
                'gallery': gallery,
                'sizes': sizes
            }
            
            items.append({
                'item_id': f"{order.id}-{idx}",
                'product': product_data,
                'quantity': item.quantity,
                'price': float(item.price),
                'final_price': float(item.final_price),
                'selected_size': item.selected_size,
                'selected_color': item.selected_color,
                'selected_color_name': item.selected_color_name
            })
        
        order_data = {
            'id': str(order.id),
            'order_number': order.order_number,
            'status': order.status,
            'total_amount': float(order.total_amount),
            'created_at': order.created_at.isoformat() + 'Z',
            'items': items,
            'payment_method': order.payment_method,
            'payment_status': order.payment_status,
            'seller': {
                'id': str(seller.id) if seller else None,
                'business_name': seller.businessName if seller else None
            },
            'promo_code': {
                'id': str(promo_code.id) if promo_code else None,
                'code': promo_code.code if promo_code else None,
                'discount_type': promo_code.discount_type if promo_code else None,
                'discount_value': float(promo_code.discount_value) if promo_code else 0,
                'discount_amount': float(order.promo_code_discount) if hasattr(order, 'promo_code_discount') else 0
            } if promo_code else None
        }
        order_list.append(order_data)
    
    return jsonify({
        'status': 'success',
        'message': 'Orders fetched successfully',
        'data': order_list,
        'count': len(order_list)
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
