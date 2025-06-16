from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.utils import create_error_response
from app.utils.jwt_handlers import jwt_error_handler
from mongoengine.queryset.visitor import Q
from datetime import datetime
from bson import ObjectId
from app.models.promo_code import PromoCode, PromoCodeUsage
from app.models.user import User
from app.models.order import Order
from constants import VALIDATE_PROMO_CODE

promo_bp = Blueprint('promo_code', __name__)

@promo_bp.route(VALIDATE_PROMO_CODE, methods=['POST'])
@jwt_error_handler
@jwt_required()
def validate_promo_code():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or 'promo_code' not in data or 'order_amount' not in data:
        return create_error_response('Promo code and order amount are required', 400)
    
    promo_code_str = data['promo_code'].upper().strip()
    order_amount = float(data['order_amount'])
    product_ids = data.get('product_ids', [])
    category_ids = data.get('category_ids', [])
    
    current_datetime = datetime.now()
    
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
        applicable = False
        
        if product_ids:
            applicable_products = [p.product_id for p in promo_code.applicable_products if p.product_id]
            if any(ObjectId(pid) in applicable_products for pid in product_ids):
                applicable = True
        
        if not applicable and category_ids:
            applicable_categories = [p.category_id for p in promo_code.applicable_products if p.category_id]
            if any(ObjectId(cid) in applicable_categories for cid in category_ids):
                applicable = True
        
        if not applicable:
            return create_error_response('This promo code is not applicable to items in your order', 400)
    
    if promo_code.max_uses is not None:
        usage_count = PromoCodeUsage.objects(promo_code=promo_code).count()
        if usage_count >= promo_code.max_uses:
            return create_error_response('This promo code has reached its maximum usage limit', 400)
    
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
        'description': promo_code.description
    }
    
    return jsonify(response), 200

