from datetime import datetime
from bson import ObjectId
from flask import request, jsonify
from app.models.promo_code import PromoCode, PromoCodeUsage
from app.models.user import User
from app.models.order import Order
from app.models.product import Product
from constants import VALIDATE_PROMO_CODE

promo_bp = Blueprint('promo_code', __name__)

@promo_bp.route(VALIDATE_PROMO_CODE, methods=['POST'])
@jwt_error_handler
@jwt_required()
def validate_promo_code():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or 'promo_code' not in data:
        return create_error_response('Promo code is required', 400)
    
    promo_code_str = data['promo_code'].upper().strip()
    cart_items_ids = data.get('cart_items_ids', [])

    order_amount = float(data.get('order_amount', 0))
    
    current_datetime = datetime.now()
    
    # Find active promo code
    promo_code = PromoCode.objects(
        code=promo_code_str,
        is_active=True,
        start_date__lte=current_datetime,
    ).first()
    
    if not promo_code:
        return create_error_response('Invalid or expired promo code', 404)
    
    if promo_code.expiry_date and promo_code.expiry_date < current_datetime:
        return create_error_response('Promo code has expired', 400)
    
    if order_amount < promo_code.min_order_amount:
        return create_error_response(
            f'Minimum order amount of {promo_code.min_order_amount} required for this promo code',
            400
        )
    
    if promo_code.applicable_to == 'specific':
        if not cart_items_ids:
            return create_error_response('This promo code requires specific items in cart', 400)
        
        applicable = False
        applicable_product_ids = []
        applicable_category_ids = []
        
        for item in promo_code.applicable_products:
            if item.product_id:
                applicable_product_ids.append(item.product_id)
            if item.category_id:
                applicable_category_ids.append(item.category_id)
        
        products_in_cart = Product.objects(id__in=[ObjectId(pid) for pid in cart_items_ids]).only('id', 'category_id')
        
        for product in products_in_cart:
            if product.id in applicable_product_ids:
                applicable = True
                break
            if product.category_id in applicable_category_ids:
                applicable = True
                break
        
        if not applicable:
            return create_error_response('This promo code is not applicable to items in your cart', 400)
    
    # Check max uses
    if promo_code.max_uses is not None:
        usage_count = PromoCodeUsage.objects(promo_code=promo_code).count()
        if usage_count >= promo_code.max_uses:
            return create_error_response('This promo code has reached its maximum usage limit', 400)
    
    # Check user-specific limits
    user_usage_count = PromoCodeUsage.objects(promo_code=promo_code, user_id=user_id).count()
    
    if promo_code.only_first_order:
        has_previous_orders = Order.objects(user_id=user_id, status__in=['completed', 'delivered']).count() > 0
        if has_previous_orders:
            return create_error_response('This promo code is only valid for first orders', 400)
    
    if user_usage_count >= promo_code.uses_per_user:
        return create_error_response('You have reached the maximum usage limit for this promo code', 400)
    
    discount_amount = 0
    if promo_code.discount_type == 'percentage':
        discount_amount = order_amount * (promo_code.discount_value / 100)
        if promo_code.max_discount_amount > 0:
            discount_amount = min(discount_amount, promo_code.max_discount_amount)
    else:
        discount_amount = min(promo_code.discount_value, order_amount)
    
    response = {
        'valid': True,
        'promo_code': promo_code.code,
        'discount_type': promo_code.discount_type,
        'discount_value': promo_code.discount_value,
        'discount_amount': round(discount_amount, 2),
        'min_order_amount': promo_code.min_order_amount,
        'max_discount_amount': promo_code.max_discount_amount,
        'description': promo_code.description,
        'applicable_to_cart': True
    }
    
    return jsonify(response), 200