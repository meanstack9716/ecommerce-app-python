from flask import render_template, session, redirect, url_for, jsonify, request
from . import admin_api
from app.models import Order, User
from bson import ObjectId

@admin_api.route('/orders')
def product_order_list_page():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))
    
    user = User.objects(id=session['user_id']).first()
    if not user:
        return redirect(url_for('admin_api.login_page'))

    try:
        items_per_page = 10
        if user.is_admin:
            orders = Order.objects().order_by('-created_at').limit(items_per_page)
            total_orders = Order.objects().count()
        else:
            orders = Order.objects(seller_id=ObjectId(user.id)).order_by('-created_at').limit(items_per_page)
            total_orders = Order.objects(seller_id=ObjectId(user.id)).count()
        
        total_pages = (total_orders + items_per_page - 1) // items_per_page

        print(f"Initial orders fetched: {len(orders)} for user_id: {session['user_id']}, is_admin: {user.is_admin}")

        return render_template(
            "admin/orderPage/orders.html",
            orders=orders,
            current_page=1,
            total_pages=total_pages,
            total_orders=total_orders,
            items_per_page=items_per_page
        )
    except Exception as e:
        print(f"Error in product_order_list_page: {str(e)}")
        return jsonify({'error': 'Server error occurred'}), 500

@admin_api.route('/orders', methods=['POST'])
def get_orders():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user = User.objects(id=session['user_id']).first()
    if not user:
        return jsonify({'error': 'User not found'}), 401

    try:
        data = request.get_json() or {}
        page = int(data.get('page', 1))
        items_per_page = int(data.get('items_per_page', 10))
        search = data.get('search', '').strip()
        status = data.get('status', '').strip()

        query = {}
        if not user.is_admin:
            query['seller_id'] = ObjectId(user.id)
        
        if search:
            query['$or'] = [
                {'order_number': {'$regex': search, '$options': 'i'}}
            ]
        
        if status:
            query['status'] = status

        print(f"Query: {query}, Page: {page}, Items per page: {items_per_page}")

        total_orders = Order.objects(__raw__=query).count()
        total_pages = (total_orders + items_per_page - 1) // items_per_page
        
        orders = Order.objects(__raw__=query).order_by('-created_at').skip((page - 1) * items_per_page).limit(items_per_page)
        
        orders_data = [{
            'id': str(order.id),
            'order_number': order.order_number,
            'created_at': order.created_at.isoformat(),
            'total_amount': float(order.total_amount),
            'status': order.status,
            'payment_status': order.payment_status
        } for order in orders]

        print(f"Fetched orders: {len(orders_data)}")

        return jsonify({
            'orders': orders_data,
            'current_page': page,
            'total_pages': total_pages,
            'total_orders': total_orders
        })

    except Exception as e:
        print(f"Error fetching orders: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@admin_api.route('/orders/<order_id>/status', methods=['POST'])
def update_order_status(order_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user = User.objects(id=session['user_id']).first()
    if not user:
        return jsonify({'error': 'User not found'}), 401

    try:
        order = Order.objects(id=order_id).first()
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        # Check if user is authorized to update this order
        if not user.is_admin and str(order.seller_id) != str(user.id):
            return jsonify({'error': 'Unauthorized to update this order'}), 403

        status = request.form.get('status')
        valid_statuses = ['pending', 'confirmed', 'processing', 'shipped', 'outOfDelivery', 'delivered', 'cancelled', 'return', 'refund']
        
        if status not in valid_statuses:
            return jsonify({'error': 'Invalid status'}), 400

        order.status = status
        order.save()
        
        print(f"Order {order_id} status updated to {status} by user {user.id}")
        
        return jsonify({'success': True, 'status': status})

    except Exception as e:
        print(f"Error updating order status: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500