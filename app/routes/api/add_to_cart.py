from flask import Blueprint, request, jsonify, session, flash, redirect, url_for, json
from app.models import ProductBrands
from app.utils.utils import create_error_response
from app.utils.image_upload import upload_image
from app.utils.validation import validate_required_fields

from datetime import datetime

add_to_cart_bp = Blueprint('add_to_cart_bp', __name__)

@add_to_cart_bp.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    required_fields = ['product_id', 'product_name', 'product_sku_number', 'product_price', 'size', 'color', 'quantity', 'product_images']
    missing_fields = [field for field in required_fields if field not in request.form]
    
    if missing_fields:
        flash(f"Missing required fields: {', '.join(missing_fields)}", 'error')
        return redirect(url_for(''))

    try:
        # Extract form data
        product_id = request.form['product_id']
        product_name = request.form['product_name']
        product_sku_number = request.form['product_sku_number']
        product_price = float(request.form['product_price'])
        size = request.form['size']
        color = request.form['color']
        quantity = int(request.form['quantity'])
        product_images = json.loads(request.form['product_images']) 



        # Add the product data to the cart
        cart_item = {
            'product_id': product_id,
            'product_name': product_name,
            'product_sku_number': product_sku_number,
            'product_price': product_price,
            'size': size,
            'color': color,
            'quantity': quantity,
            'product_images': product_images
        }

        # Save to session (or database if necessary)
        if 'cart' not in session:
            session['cart'] = []
        session['cart'].append(cart_item)

        # Flash success message
        flash('Item added to cart successfully!', 'success')

        # Redirect to the cart page
        return redirect(url_for('admin_api.view_cart'))

    except Exception as e:
        flash(f"Error occurred: {str(e)}", 'error')
        return redirect(url_for('admin_api.view_cart')) 
