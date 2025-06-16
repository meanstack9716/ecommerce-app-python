from datetime import datetime
from bson import ObjectId
from flask import request, jsonify, Blueprint
from app.models import Order, Products, PromoCode
from constants import VALIDATE_PROMO_CODE
from app.utils.utils import create_error_response
from app.utils.jwt_handlers import jwt_error_handler
from flask_jwt_extended import jwt_required, get_jwt_identity

promo_bp = Blueprint('promo_code', __name__)

@promo_bp.route(VALIDATE_PROMO_CODE, methods=['POST'])
@jwt_error_handler
@jwt_required()
def validate_promo_code():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or 'promo_code' not in data or 'cart_items_ids' not in data:
        return create_error_response('Both promo_code and cart_items_ids are required', 400)
    
    promo_code_str = data['promo_code'].upper().strip()
    cart_items_ids = data['cart_items_ids']
    
    try:
        cart_object_ids = [ObjectId(item_id) for item_id in cart_items_ids]
    except:
        return create_error_response('Invalid cart item ID format', 400)
    
    current_datetime = datetime.utcnow()
    
    promo_code = PromoCode.objects(
        code=promo_code_str,
        is_active=True,
        start_date__lte=current_datetime,
    ).first()
    
    if not promo_code:
        return create_error_response('Invalid or expired promo code', 404)
    
    if promo_code.expiry_date and promo_code.expiry_date < current_datetime:
        return create_error_response('Promo code has expired', 400)
    
    if promo_code.only_first_order:
        has_previous_orders = Order.objects(
            user_id=user_id, 
            status__in=['completed', 'delivered']
        ).count() > 0
        if has_previous_orders:
            return create_error_response('This promo code is only valid for first orders', 400)
    
    if promo_code.applicable_to == 'specific':
        if not cart_items_ids:
            return create_error_response('This promo code requires specific items in cart', 400)
        
        products_in_cart = Product.objects(id__in=cart_object_ids).only(
            'id', 'category_id', 'subcategory_id', 'subsubcategory_id', 'brand_id'
        )
        
        applicable = False
        for product in products_in_cart:
            for applicable_rule in promo_code.applicable_products:
                if (applicable_rule.product_id and product.id == applicable_rule.product_id.id) or \
                   (applicable_rule.category_id and getattr(product, 'category_id', None) and \
                      product.category_id.id == applicable_rule.category_id.id) or \
                   (applicable_rule.subcategory_id and getattr(product, 'subcategory_id', None) and \
                      product.subcategory_id.id == applicable_rule.subcategory_id.id) or \
                   (applicable_rule.subsubcategory_id and getattr(product, 'subsubcategory_id', None) and \
                      product.subsubcategory_id.id == applicable_rule.subsubcategory_id.id) or \
                   (applicable_rule.brand_id and getattr(product, 'brand_id', None) and \
                      product.brand_id.id == applicable_rule.brand_id.id):
                    applicable = True
                    break
            if applicable:
                break
        
        if not applicable:
            return create_error_response('This promo code is not applicable to items in your cart', 400)
    
    response = {
        'valid': True,
        'promo_code': promo_code.code,
        'discount_type': promo_code.discount_type,
        'discount_value': float(promo_code.discount_value),
        'description': promo_code.description,
        'applicable_to_cart': True
    }
    
    return jsonify(response), 200