from flask import Blueprint, jsonify
from datetime import datetime, timedelta
from app.extensions import db
from mongoengine.queryset.visitor import Q
from bson import ObjectId
import pytz
from app.models import Order
sales_api = Blueprint('sales_api', __name__)

@sales_api.route('/api/sales/overview', methods=['GET'])
def sales_overview():
    try:
        now = datetime.now(pytz.UTC)
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)

        orders = Order.objects(
            created_at__gte=start_of_month,
            created_at__lte=end_of_month,
            status__in=['confirmed', 'processing', 'shipped', 'outOfDelivery', 'delivered']
        )

        total_sales = sum(order.total_amount for order in orders)
        order_count = orders.count()
        avg_order_value = total_sales / order_count if order_count > 0 else 0

        return jsonify({
            'status': 'success',
            'data': {
                'total_sales': float(total_sales),
                'order_count': order_count,
                'avg_order_value': float(avg_order_value)
            }
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@sales_api.route('/api/sales/over-time', methods=['GET'])
def sales_over_time():
    """Get sales data aggregated by month for the last 5 months."""
    try:
        now = datetime.now(pytz.UTC)
        months = []
        sales_data = []

        for i in range(5):
            month_start = (now - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
            orders = Order.objects(
                created_at__gte=month_start,
                created_at__lte=month_end,
                status__in=['confirmed', 'processing', 'shipped', 'outOfDelivery', 'delivered']
            )
            total_sales = sum(order.total_amount for order in orders)
            months.append(month_start.strftime('%b'))
            sales_data.append(float(total_sales))

        return jsonify({
            'status': 'success',
            'data': {
                'labels': months[::-1],  # Reverse to show oldest to newest
                'sales': sales_data[::-1]
            }
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@sales_api.route('/api/sales/top-products', methods=['GET'])
def top_products():
    """Get top 5 products by units sold in the current month."""
    try:
        now = datetime.now(pytz.UTC)
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)

        pipeline = [
            {'$match': {
                'created_at': {'$gte': start_of_month, '$lte': end_of_month},
                'status': {'$in': ['confirmed', 'processing', 'shipped', 'outOfDelivery', 'delivered']}
            }},
            {'$unwind': '$items'},
            {'$group': {
                '_id': '$items.product_id',
                'total_units': {'$sum': '$items.quantity'}
            }},
            {'$lookup': {
                'from': 'products',
                'localField': '_id',
                'foreignField': '_id',
                'as': 'product'
            }},
            {'$unwind': '$product'},
            {'$project': {
                'name': '$product.name',
                'total_units': 1
            }},
            {'$sort': {'total_units': -1}},
            {'$limit': 5}
        ]

        results = Order.objects().aggregate(pipeline)
        products = [{'name': item['name'], 'units': item['total_units']} for item in results]

        return jsonify({
            'status': 'success',
            'data': {
                'labels': [p['name'] for p in products],
                'units': [p['units'] for p in products]
            }
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@sales_api.route('/api/sales/recent', methods=['GET'])
def recent_sales():
    """Get the 5 most recent sales."""
    try:
        orders = Order.objects(
            status__in=['confirmed', 'processing', 'shipped', 'outOfDelivery', 'delivered']
        ).order_by('-created_at').limit(5)

        recent_orders = []
        for order in orders:
            user = db.User.objects(id=order.user_id.id).first()
            product_names = [db.Products.objects(id=item.product_id.id).first().name for item in order.items]
            recent_orders.append({
                'order_id': order.order_number,
                'customer': user.name if user else 'Unknown',
                'product': product_names[0] if product_names else 'Unknown',
                'amount': float(order.total_amount),
                'date': order.created_at.strftime('%Y-%m-%d')
            })

        return jsonify({
            'status': 'success',
            'data': recent_orders
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500