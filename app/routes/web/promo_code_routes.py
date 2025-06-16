from flask import render_template, session, redirect, url_for, request, jsonify
from . import admin_api
from app.models import User, PromoCode
from constants import ADD_PROMO_CODE_WEB_URL, PROMO_CODE_LIST, DELETE_PROMO_CODE
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

def handle_promo_code_submission():
    if 'user_id' not in session:
        return create_error_response('Unauthorized', 401)

    try:
        data = request.form
        required_fields = ['code', 'discount_type', 'discount_value', 'start_date']
        
        is_valid, validation_errors = validate_fields(data, required_fields)
        if not is_valid:
            return create_error_response(validation_errors, 400)

        promo_code_value = data['code'].upper().strip()

        if PromoCode.objects(code=promo_code_value).first():
            return create_error_response(f"Promo code '{promo_code_value}' already exists.", 400)

        promo_data = {
            'code': promo_code_value,
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
            'created_by': session['user_id']
        }

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

    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    search = request.args.get('promoSearch', '')
    status = request.args.get('status', '')
    discount_type = request.args.get('discount_type', '')

    query = PromoCode.objects

    if search:
        query = query.filter(
            Q(code__icontains=search) | 
            Q(description__icontains=search)
        )

    if status == 'active':
        query = query.filter(is_active=True)
    elif status == 'inactive':
        query = query.filter(is_active=False)

    if discount_type:
        query = query.filter(discount_type=discount_type)

    promo_codes = query.order_by('-created_at').paginate(page=page, per_page=limit)

    # Check if the request is expecting JSON (AJAX)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        promo_list = []
        for promo in promo_codes.items:
            promo_list.append({
                'id': str(promo.id),
                'code': promo.code,
                'description': promo.description,
                'discount_type': promo.discount_type,
                'discount_value': promo.discount_value,
                'max_discount_amount': promo.max_discount_amount,
                'start_date': promo.start_date.strftime('%Y-%m-%d') if promo.start_date else 'N/A',
                'expiry_date': promo.expiry_date.strftime('%Y-%m-%d') if promo.expiry_date else 'N/A',
                'current_uses': promo.current_uses,
                'max_uses': promo.max_uses,
                'is_active': promo.is_active
            })

        return jsonify({
            'promos': promo_list,
            'pagination': {
                'page': promo_codes.page,
                'per_page': promo_codes.per_page,
                'total': promo_codes.total,
                'pages': promo_codes.pages,
                'has_prev': promo_codes.has_prev,
                'has_next': promo_codes.has_next,
                'prev_num': promo_codes.prev_num,
                'next_num': promo_codes.next_num,
                'first_item': (promo_codes.page - 1) * promo_codes.per_page + 1,
                'last_item': min(promo_codes.page * promo_codes.per_page, promo_codes.total),
                'iter_pages': list(promo_codes.iter_pages(left_edge=1, right_edge=1, left_current=2, right_current=2))
            },
            'search': search,
            'status': status,
            'discount_type': discount_type,
            'limit': limit
        })

    return render_template(
        'admin/promo_codes/promo_code_list.html',
        promos=promo_codes,
        search=search,
        status=status,
        discount_type=discount_type,
        limit=limit
    )

@admin_api.route('/api/promo-codes/<string:promo_code_id>', methods=['GET', 'PUT'])
def edit_promo_code(promo_code_id):
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))
    
    try:
        promo_code = PromoCode.objects.get(id=promo_code_id)
    except PromoCode.DoesNotExist:
        return create_error_response('Promo code not found', 404)
    
    if request.method == 'GET':
        return jsonify({
            'code': promo_code.code,
            'description': promo_code.description,
            'discount_type': promo_code.discount_type,
            'discount_value': float(promo_code.discount_value),
            'start_date': promo_code.start_date.isoformat(),
            'expiry_date': promo_code.expiry_date.isoformat() if promo_code.expiry_date else None,
            'is_active': promo_code.is_active,
            'max_uses': promo_code.max_uses,
            'min_order_amount': float(promo_code.min_order_amount) if promo_code.min_order_amount else None,
            'max_discount_amount': float(promo_code.max_discount_amount) if promo_code.max_discount_amount else None,
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
            promo_code.max_uses = int(data['max_uses']) if data.get('max_uses') else promo_code.max_uses
            promo_code.min_order_amount = float(data['min_order_amount']) if data.get('min_order_amount') else promo_code.min_order_amount
            promo_code.max_discount_amount = float(data['max_discount']) if data.get('max_discount') else promo_code.max_discount_amount        
            
            promo_code.save()
            
            return jsonify({
                'success': True,
                'message': 'Promo code updated successfully'
            })
        
        except ValueError as e:
            return create_error_response(str(e), 400)
        except Exception as e:
            return create_error_response(str(e), 500)

@admin_api.route(DELETE_PROMO_CODE, methods=['DELETE'])
def delete_promo_code(promo_code_id):
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))
    
    try:
        promo_code = PromoCode.objects.get(id=promo_code_id)
    except PromoCode.DoesNotExist:
        return create_error_response('Promo code not found', 404)
    
    try:
        promo_code.delete()
        return jsonify({
            'success': True,
            'message': 'Promo code deleted successfully'
        })
    except Exception as e:
        return create_error_response(str(e), 500)