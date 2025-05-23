from flask import render_template, session, redirect, url_for, request, jsonify
from . import admin_api
from app.models import User, PromoCode, PromoCodeApplicableProducts
from constants import ADD_PROMO_CODE_WEB_URL, PROMO_CODE_LIST
from datetime import datetime
from bson import ObjectId
from app.utils.utils import create_error_response
from app.utils.image_upload import validate_fields

@admin_api.route(ADD_PROMO_CODE_WEB_URL, methods=['GET', 'POST'])
def add_promo_code():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))
    
    if request.method == 'POST':
        return handle_promo_code_submission()
    
    return render_template('admin/promo_codes/add_promo_code.html')


@admin_api.route('/api/promo-codes', methods=['POST'])
def handle_promo_code_submission():
    if 'user_id' not in session:
        return create_error_response('Unauthorized', 401)

    try:
        data = request.form
        print(data, ">>>>")
        required_fields = ['code', 'discount_type', 'discount_value', 'start_date']
        
        is_valid, validation_errors = validate_fields(data, required_fields)

        if not is_valid:
            return create_error_response(validation_errors, 400)

        promo_data = {
            'code': data['code'].upper().strip(),
            'description': data.get('description'),
            'discount_type': data['discount_type'],
            'discount_value': float(data['discount_value']),
            'min_order_amount': float(data.get('min_order_amount', 0)),
            'max_discount_amount': float(data.get('max_discount_amount', 0)),
            'start_date': datetime.fromisoformat(data['start_date']),
            'expiry_date': datetime.fromisoformat(data['expiry_date']) if data.get('expiry_date') else None,
            'max_uses': int(data['max_uses']) if data.get('max_uses') else None,
            'uses_per_user': int(data.get('uses_per_user', 1)),
            'only_first_order': data.get('only_first_order', 'false').lower() == 'true',
            'is_active': data.get('is_active', 'true').lower() == 'true',
            'applicable_to': data.get('applicable_to', 'all'),
            'created_by': session['user_id']
        }

        if data.get('applicable_to') == 'specific' and data.getlist('products'):
            applicable_products = []
            for product_id in data.getlist('products'):
                applicable_products.append(
                    PromoCodeApplicableProducts(product_id=ObjectId(product_id))
                )
            if data.getlist('categories'):
                for category_id in data.getlist('categories'):
                    applicable_products.append(
                        PromoCodeApplicableProducts(category_id=ObjectId(category_id))
                    )
            promo_data['applicable_products'] = applicable_products

        promo_code = PromoCode(**promo_data)
        promo_code.save()

        return jsonify({
            'success': True,
            'message': 'Promo code created successfully',
            'promo_code_id': str(promo_code.id),
            'code': promo_code.code,
            'discount_value': float(promo_code.discount_value),
            'discount_type': promo_code.discount_type
        }), 201

    except ValueError as e:
        return create_error_response(f'Invalid data: {str(e)}', 400)
    except Exception as e:
        return create_error_response(f'Server error: {str(e)}', 500)


@admin_api.route(PROMO_CODE_LIST, methods=['GET'])
def promo_code_list():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))
    
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('limit', 10, type=int)
    search = request.args.get('search', '', type=str)
    status = request.args.get('status', '', type=str)
    discount_type = request.args.get('discount_type', '', type=str)
    
    # Build query
    query = {}
    if search:
        query['$or'] = [
            {'code__icontains': search},
            {'description__icontains': search}
        ]
    if status:
        query['is_active'] = (status == 'active')
    if discount_type:
        query['discount_type'] = discount_type
    
    # Fetch promo codes with pagination
    promo_codes = PromoCode.objects(**query).order_by('-created_at').paginate(page=page, per_page=per_page)
    
    # Prepare data for JSON response
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'data': [
                {
                    'id': str(promo.id),
                    'code': promo.code,
                    'description': promo.description,
                    'discount_type': promo.discount_type,
                    'discount_value': promo.discount_value,
                    'max_discount_amount': promo.max_discount_amount,
                    'start_date': promo.start_date.isoformat() if promo.start_date else None,
                    'expiry_date': promo.expiry_date.isoformat() if promo.expiry_date else None,
                    'current_uses': promo.current_uses,
                    'max_uses': promo.max_uses,
                    'is_active': promo.is_active
                } for promo in promo_codes.items
            ],
            'pagination': {
                'page': promo_codes.page,
                'pages': promo_codes.pages,
                'has_prev': promo_codes.has_prev,
                'has_next': promo_codes.has_next,
                'prev_num': promo_codes.prev_num,
                'next_num': promo_codes.next_num
            },
            'limit': per_page
        })
    
    return render_template('admin/promo_codes/promo_code_list.html', 
                         promos=promo_codes.items,
                         pagination=promo_codes,
                         search=search,
                         status=status,
                         discount_type=discount_type,
                         limit=per_page)

@admin_api.route('/api/promo-codes/<string:promo_code_id>', methods=['GET', 'PUT', 'DELETE'])
def edit_promo_code(promo_code_id):
    if 'user_id' not in session:
        return create_error_response('Unauthorized', 401)
    
    try:
        promo_code = PromoCode.objects.get(id=promo_code_id)
    except PromoCode.DoesNotExist:
        return create_error_response('Promo code not found', 404)
    
    if request.method == 'GET':
        # For displaying the edit form
        return jsonify({
            'code': promo_code.code,
            'description': promo_code.description,
            'discount_type': promo_code.discount_type,
            'discount_value': float(promo_code.discount_value),
            'start_date': promo_code.start_date.isoformat(),
            'expiry_date': promo_code.expiry_date.isoformat() if promo_code.expiry_date else None,
            'is_active': promo_code.is_active,
            'is_single_use': promo_code.is_single_use,
            'max_uses': promo_code.max_uses,
            'min_order_amount': float(promo_code.min_order_amount) if promo_code.min_order_amount else None,
            'max_discount_amount': float(promo_code.max_discount_amount) if promo_code.max_discount_amount else None,
            'applicable_to': promo_code.applicable_to,
            'applicable_products': [str(product.product_id.id) for product in promo_code.applicable_products] 
                if promo_code.applicable_products else []
        })
    
    elif request.method == 'PUT':
        try:
            data = request.form if request.form else request.json
            
            # Update basic fields
            promo_code.description = data.get('description', promo_code.description)
            promo_code.discount_type = data.get('discount_type', promo_code.discount_type)
            promo_code.discount_value = float(data.get('discount_value', promo_code.discount_value))
            promo_code.start_date = datetime.fromisoformat(data.get('start_date')) if data.get('start_date') else promo_code.start_date
            promo_code.expiry_date = datetime.fromisoformat(data.get('expiry_date')) if data.get('expiry_date') else promo_code.expiry_date
            promo_code.is_active = data.get('is_active', str(promo_code.is_active)).lower() == 'true'
            promo_code.is_single_use = data.get('is_single_use', str(promo_code.is_single_use)).lower() == 'true'
            promo_code.max_uses = int(data['max_uses']) if data.get('max_uses') else promo_code.max_uses
            promo_code.min_order_amount = float(data['min_order_amount']) if data.get('min_order_amount') else promo_code.min_order_amount
            promo_code.max_discount_amount = float(data['max_discount']) if data.get('max_discount') else promo_code.max_discount_amount
            promo_code.applicable_to = data.get('product_restriction', promo_code.applicable_to)
            
            # Handle product restrictions
            if data.get('product_restriction') == 'specific' and data.getlist('products'):
                promo_code.applicable_products = [
                    PromoCodeApplicableProducts(product_id=ObjectId(product_id))
                    for product_id in data.getlist('products')
                ]
            elif data.get('product_restriction') != 'specific':
                promo_code.applicable_products = []
            
            promo_code.save()
            
            return jsonify({
                'success': True,
                'message': 'Promo code updated successfully'
            })
        
        except ValueError as e:
            return create_error_response(str(e), 400)
        except Exception as e:
            return create_error_response(str(e), 500)
    
    elif request.method == 'DELETE':
        try:
            promo_code.delete()
            return jsonify({
                'success': True,
                'message': 'Promo code deleted successfully'
            })
        except Exception as e:
            return create_error_response(str(e), 500)