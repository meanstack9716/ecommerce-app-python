from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from bson import ObjectId
from app.models.promo_codes import PromoCode, UserPromoCode
from app.models.products import Products
from app.models.order import Order
from app.extensions import db

promo_code_bp = Blueprint('promo_code_bp', __name__, url_prefix='/api/promo-codes')

@promo_code_bp.route('/validate', methods=['POST'])
@jwt_required()
def validate_promo_code():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not all(field in data for field in ['code', 'order_amount', 'product_ids']):
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        promo_code = PromoCode.objects.get(code=data['code'], is_active=True)
    except PromoCode.DoesNotExist:
        return jsonify({"error": "Invalid promo code"}), 404
    
    if promo_code.is_single_use and UserPromoCode.objects(user_id=user_id, promo_code_id=promo_code.id).count() > 0:
        return jsonify({"error": "You have already used this promo code"}), 400
    
    try:
        products = Products.objects(id__in=[ObjectId(pid) for pid in data['product_ids']])
    except Exception:
        return jsonify({"error": "Invalid product IDs"}), 400
    
    is_valid, message = promo_code.is_valid(user_id, float(data['order_amount']), products)
    if not is_valid:
        return jsonify({"error": message}), 400
    
    discount_amount = promo_code.calculate_discount(float(data['order_amount']))
    
    return jsonify({
        "success": True,
        "discount_amount": discount_amount,
        "final_amount": float(data['order_amount']) - discount_amount,
        "promo_code": promo_code.code
    })

@promo_code_bp.route('/apply', methods=['POST'])
@jwt_required()
def apply_promo_code():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not all(field in data for field in ['code', 'order_id']):
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        order = Order.objects.get(id=ObjectId(data['order_id']), user_id=user_id)
    except Order.DoesNotExist:
        return jsonify({"error": "Order not found"}), 404
    
    if order.status != 'pending':
        return jsonify({"error": "Promo code can only be applied to pending orders"}), 400
    
    try:
        promo_code = PromoCode.objects.get(code=data['code'], is_active=True)
    except PromoCode.DoesNotExist:
        return jsonify({"error": "Invalid promo code"}), 404
    
    if promo_code.is_single_use and UserPromoCode.objects(user_id=user_id, promo_code_id=promo_code.id).count() > 0:
        return jsonify({"error": "You have already used this promo code"}), 400
    
    product_ids = [item.product_id.id for item in order.items]
    products = Products.objects(id__in=product_ids)
    
    is_valid, message = promo_code.is_valid(user_id, float(order.total_amount), products)
    if not is_valid:
        return jsonify({"error": message}), 400
    
    discount_amount = promo_code.calculate_discount(float(order.total_amount))
    
    order.applied_promo_code = promo_code
    order.promo_code_discount = discount_amount
    order.total_amount -= discount_amount
    order.save()
    
    UserPromoCode(
        user_id=user_id,
        promo_code_id=promo_code.id,
        order_id=order.id
    ).save()
    
    promo_code.increment_usage()
    
    return jsonify({
        "success": True,
        "order_id": str(order.id),
        "discount_amount": float(discount_amount),
        "new_total": float(order.total_amount)
    })

@promo_code_bp.route('/admin/create', methods=['POST'])
@jwt_required()
def create_promo_code():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    required_fields = ['code', 'discount_type', 'discount_value', 'start_date', 'end_date']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        promo_code = PromoCode(
            code=data['code'],
            description=data.get('description'),
            discount_type=data['discount_type'],
            discount_value=data['discount_value'],
            min_order_amount=data.get('min_order_amount'),
            max_discount_amount=data.get('max_discount_amount'),
            start_date=datetime.fromisoformat(data['start_date']),
            end_date=datetime.fromisoformat(data['end_date']),
            max_uses=data.get('max_uses'),
            is_single_use=data.get('is_single_use', False),
            applicable_to=data.get('applicable_to', 'all'),
            created_by=user_id
        )
        
        if data.get('applicable_to') == 'specific' and 'applicable_products' in data:
            for item in data['applicable_products']:
                applicable = PromoCodeApplicableProducts()
                if 'product_id' in item:
                    applicable.product_id = ObjectId(item['product_id'])
                if 'category_id' in item:
                    applicable.category_id = ObjectId(item['category_id'])
                if 'subcategory_id' in item:
                    applicable.subcategory_id = ObjectId(item['subcategory_id'])
                if 'subsubcategory_id' in item:
                    applicable.subsubcategory_id = ObjectId(item['subsubcategory_id'])
                if 'brand_id' in item:
                    applicable.brand_id = ObjectId(item['brand_id'])
                promo_code.applicable_products.append(applicable)
        
        promo_code.save()
        return jsonify({"success": True, "promo_code_id": str(promo_code.id)}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@promo_code_bp.route('/admin/list', methods=['GET'])
@jwt_required()
def list_promo_codes():
    promo_codes = PromoCode.objects.all()
    return jsonify([{
        "id": str(code.id),
        "code": code.code,
        "description": code.description,
        "discount_type": code.discount_type,
        "discount_value": float(code.discount_value),
        "start_date": code.start_date.isoformat(),
        "end_date": code.end_date.isoformat(),
        "max_uses": code.max_uses,
        "current_uses": code.current_uses,
        "is_active": code.is_active,
        "applicable_to": code.applicable_to
    } for code in promo_codes])

@promo_code_bp.route('/user/available', methods=['GET'])
@jwt_required()
def get_available_promo_codes():
    user_id = get_jwt_identity()
    now = datetime.utcnow()
    
    promo_codes = PromoCode.objects(
        is_active=True,
        start_date__lte=now,
        end_date__gte=now
    )
    
    result = []
    for code in promo_codes:
        if code.is_single_use and UserPromoCode.objects(user_id=user_id, promo_code_id=code.id).count() > 0:
            continue
        if code.max_uses and code.current_uses >= code.max_uses:
            continue
            
        result.append({
            "code": code.code,
            "description": code.description,
            "discount_type": code.discount_type,
            "discount_value": float(code.discount_value),
            "min_order_amount": float(code.min_order_amount) if code.min_order_amount else None,
            "max_discount_amount": float(code.max_discount_amount) if code.max_discount_amount else None,
            "end_date": code.end_date.isoformat(),
            "applicable_to": code.applicable_to
        })
    
    return jsonify(result)