from flask import render_template, session, redirect, url_for, request, jsonify
from . import admin_api
from app.models import User, PromoCode, PromoCodeApplicableProducts
from constants import ADD_PROMO_CODE_WEB_URL
from datetime import datetime
from bson import ObjectId
from app.utils.utils import create_error_response

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
        
        # Validate required fields
        required_fields = ['code', 'discount_type', 'discount_value', 'start_date']
        for field in required_fields:
            if field not in data or not data[field]:
                return create_error_response(f'{field} is required', 400)

        promo_data = {
            'code': data['code'].upper().strip(),
            'discount_type': data['discount_type'],
            'discount_value': float(data['discount_value']),
            'start_date': datetime.fromisoformat(data['start_date']),
            'end_date': datetime.fromisoformat(data['end_date']) if data.get('end_date') else None,
            'created_by': session['user_id'],
            'is_active': data.get('is_active', 'false').lower() == 'true',
            'is_single_use': data.get('is_single_use', 'false').lower() == 'true',
            'max_uses': int(data['max_uses']) if data.get('max_uses') else None,
            'min_order_amount': float(data['min_order_amount']) if data.get('min_order_amount') else None,
            'max_discount_amount': float(data['max_discount']) if data.get('max_discount') else None,
            'applicable_to': data.get('product_restriction', 'all')
        }

        # Handle product restrictions
        if data.get('product_restriction') == 'specific' and data.getlist('products'):
            promo_data['applicable_products'] = [
                PromoCodeApplicableProducts(product_id=ObjectId(product_id))
                for product_id in data.getlist('products')
            ]

        promo_code = PromoCode(**promo_data)
        promo_code.save()

        return jsonify({
            'success': True,
            'message': 'Promo code created successfully',
            'promo_code_id': str(promo_code.id)
        }), 201

    except ValueError as e:
        return create_error_response(str(e), 400)
    except Exception as e:
        return create_error_response(str(e), 500)

@admin_api.route('/api/promo-code-list', methods=['GET'])
def promo_code_list():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))
    
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('limit', 10, type=int)
    search = request.args.get('search', '', type=str)
    
    # Build query
    query = {}
    if search:
        query['code__icontains'] = search
    
    # Fetch promo codes with pagination
    promo_codes = PromoCode.objects(**query).order_by('-created_at').paginate(page=page, per_page=per_page)
    
    # For HTML response
    return render_template('admin/promo_codes/promo_code_list.html', 
                         promos=promo_codes.items,
                         pagination=promo_codes,
                         search=search,
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
            'end_date': promo_code.end_date.isoformat() if promo_code.end_date else None,
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
            promo_code.end_date = datetime.fromisoformat(data.get('end_date')) if data.get('end_date') else promo_code.end_date
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