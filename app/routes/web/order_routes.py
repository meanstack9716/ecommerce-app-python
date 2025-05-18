from flask import render_template, session, redirect, url_for, jsonify, request
from . import admin_api
from app.models import Order, User, Seller
from bson import ObjectId
from constants import ORDER_LIST_WEB_URL, ORDER_STATUS_UPDATE_WEB_URL, ORDER_STATUS
from app.utils.utils import create_error_response


@admin_api.route(ORDER_LIST_WEB_URL, methods=['GET'])
def product_order_list_page():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))
    
    user = User.objects(id=session['user_id']).first()
    if not user:
        return redirect(url_for('admin_api.login_page'))

    try:
        items_per_page = 10
        
        if user.is_admin:
            query = {}
        else:
            seller = Seller.objects(user_id=ObjectId(user.id)).first()
            if not seller:
                return render_template("admin/orderPage/orders.html"), 403
            query = {'seller_id': seller.id}
        
        total_orders = Order.objects(__raw__=query).count()
        total_pages = (total_orders + items_per_page - 1) // items_per_page
        
        orders = Order.objects(__raw__=query).order_by('-created_at').limit(items_per_page)

        return render_template(
            "admin/orderPage/orders.html",
            orders=orders,
            current_page=1,
            total_pages=total_pages,
            total_orders=total_orders,
            items_per_page=items_per_page,
            is_admin=user.is_admin
        )
    except Exception as e:
        print(f"Error in product_order_list_page: {str(e)}")
        return render_template("admin/orderPage/orders.html"), 500

@admin_api.route(ORDER_LIST_WEB_URL, methods=['POST'])
def get_orders():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))
    
    user = User.objects(id=session['user_id']).first()
    if not user:
        return redirect(url_for('admin_api.login_page'))

    try:
        data = request.get_json() or {}
        page = max(1, int(data.get('page', 1)))
        items_per_page = max(1, min(int(data.get('items_per_page', 10)), 100))
        search = data.get('search', '').strip()
        status = data.get('status', '').strip()

        if user.is_admin:
            query = {}
        else:
            seller = Seller.objects(user_id=user.id).first()
            if not seller:
                return jsonify({'error': 'Seller profile not found'}), 403
            query = {'seller_id': seller.id}
        
        if search:
            query['$or'] = [
                {'order_number': {'$regex': search, '$options': 'i'}},
                {'customer_name': {'$regex': search, '$options': 'i'}},
                {'customer_email': {'$regex': search, '$options': 'i'}}
            ]
        
        if status and status != 'all':
            query['status'] = status

        total_orders = Order.objects(__raw__=query).count()
        total_pages = max(1, (total_orders + items_per_page - 1) // items_per_page)
        page = min(page, total_pages)
        
        orders = Order.objects(__raw__=query)\
                     .order_by('-created_at')\
                     .skip((page - 1) * items_per_page)\
                     .limit(items_per_page)

        orders_data = [{
            'id': str(order.id),
            'order_number': order.order_number,
            'created_at': order.created_at.isoformat(),
            'total_amount': float(order.total_amount),
            'status': order.status,
            'payment_status': order.payment_status,
            'customer_name': getattr(order, 'customer_name', ''),
            'customer_email': getattr(order, 'customer_email', '')
        } for order in orders]

        return jsonify({
            'success': True,
            'orders': orders_data,
            'current_page': page,
            'total_pages': total_pages,
            'total_orders': total_orders,
            'items_per_page': items_per_page
        })

    except ValueError as e:
        print(f"Invalid request parameters: {str(e)}")
        return create_error_response({'error': 'Invalid request parameters'}, 400)
    except Exception as e:
        print(f"Error fetching orders: {str(e)}")
        return create_error_response({'error': 'Server error occurred'}, 500)

@admin_api.route(ORDER_STATUS_UPDATE_WEB_URL, methods=['POST'])
def update_order_status(order_id):
    if 'user_id' not in session:
        return create_error_response({'error': 'Unauthorized'}, 401)
    
    user = User.objects(id=session['user_id']).first()
    if not user:
        return create_error_response({'error': 'User not found'}, 401)

    try:
        order = Order.objects(id=order_id).first()
        if not order:
            return create_error_response({'error': 'Order not found'}, 404)
        
        if not user.is_admin:
            seller = Seller.objects(user_id=user.id).first()
            if not seller or str(order.seller_id.id) != str(seller.id):
                return create_error_response({'error': 'Unauthorized to update this order'}, 403)

        status = request.form.get('status')
        valid_statuses = ORDER_STATUS
        
        if status not in valid_statuses:
            return create_error_response({'error': 'Invalid status'}, 400)

        order.status = status
        order.save()
        
        print(f"Order {order_id} status updated to {status} by user {user.id}")
        
        return jsonify({'success': True, 'status': status})

    except Exception as e:
        print(f"Error updating order status: {str(e)}")
        return create_error_response({'error': f'Server error: {str(e)}'}, 500)