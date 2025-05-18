from flask import render_template, redirect, url_for, session, request,jsonify
from constants import ADD_NEW_PRODUCT_WEB_URL, GET_PRODUCT_LIST_WEB_URL, GET_PRODUCT_DETAILS_WEB_URL, GET_PROUDCT_EDIT_PAGE_BY_ID_WEB_URL
from . import admin_api
from app.models import Category, SubCategory, SubSubCategory, Products, User, Seller
from app.utils.utils import create_error_response

from app.utils.image_upload import get_local_ip
local_ip = get_local_ip()

@admin_api.route(ADD_NEW_PRODUCT_WEB_URL, methods=['GET'])
def add_products_page():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))

    categories = Category.objects.all()

    return render_template(
        'admin/products/add_new_product.html',
        categories=categories,
    )

def get_filtered_products(seller_id=None):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('limit', 10, type=int)
    category = request.args.get('category')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)

    query = {}

    if seller_id is not None:
        query['seller_id'] = seller_id

    if category:
        category_obj = Category.objects(name=category).first()
        if category_obj:
            query['category_id'] = category_obj.id
        else:
            return None, Category.objects.all(), f"Category '{category}' not found"

    if min_price is not None:
        query['final_price__gte'] = min_price

    if max_price is not None:
        query['final_price__lte'] = max_price

    try:
        products = Products.objects(**query).order_by('-created_at').paginate(page=page, per_page=per_page)
        return products, Category.objects.all(), None
    except Exception as e:
        return None, Category.objects.all(), str(e)

@admin_api.route(GET_PRODUCT_LIST_WEB_URL, methods=['GET'])
def get_product_lists():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))

    current_user = User.objects(id=session['user_id']).first()
    if not current_user:
        return redirect(url_for('admin_api.login_page'))

    if current_user.is_admin:
        products, categories, error = get_filtered_products()
    else:
        seller = Seller.objects(user_id=current_user).first()
        if not seller:
            error_message = 'Seller profile not found. Please contact administrator.'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return create_error_response({'error': error_message}, 400)
            return render_template(
                'admin/products/product_lists.html',
                products=None,
                categories=Category.objects.all(),
                local_ip=local_ip,
                error=error_message,
                is_admin=False
            )
        products, categories, error = get_filtered_products(seller_id=seller.id)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if error:
            return create_error_response({'error': error}, 400)
        if not products or products.total == 0:
            return jsonify({'message': 'No products found'}), 200

        product_data = []
        for product in products.items:
            image_url = None
            if product.variants and product.variants[0].images:
                image_url = f"http://{local_ip}:8080/static/uploads/{product.variants[0].images[0].image_url}"

            product_data.append({
                'name': product.name,
                'price': float(product.price) if product.price else 0,
                'discount_price': float(product.discount_price) if product.discount_price else 0,
                'final_price': float(product.final_price) if product.final_price else 0,
                'sku_number': product.sku_number or '-',
                'image_url': image_url,
                'edit_url': url_for('admin_api.edit_product', product_id=str(product.id)),
                'details_url': url_for('admin_api.product_details', product_id=str(product.id))
            })

        return jsonify({
            'products': product_data,
            'page': products.page,
            'pages': products.pages,
            'has_prev': products.has_prev,
            'has_next': products.has_next,
            'prev_num': products.prev_num,
            'next_num': products.next_num
        })

    # Handle AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if error:
            return jsonify({'error': error}), 400

        product_data = []
        for product in products.items:
            image_url = None
            if product.variants and product.variants[0].images:
                image_url = f"http://{local_ip}:8080/static/uploads/{product.variants[0].images[0].image_url}"

            product_data.append({
                'name': product.name,
                'price': product.price,
                'discount_price': product.discount_price,
                'final_price': product.final_price,
                'sku_number': product.sku_number or '-',
                'image_url': image_url,
                'edit_url': url_for('admin_api.edit_product', product_id=product.id),
                'details_url': url_for('admin_api.product_details', product_id=product.id)
            })

        return jsonify({
            'products': product_data,
            'page': products.page,
            'pages': products.pages,
            'has_prev': products.has_prev,
            'has_next': products.has_next,
            'prev_num': products.prev_num,
            'next_num': products.next_num
        })

    return render_template(
        'admin/products/product_lists.html',
        products=products,
        categories=categories,
        local_ip=local_ip,
        error=error,
        is_admin=current_user.is_admin
    )


@admin_api.route(GET_PRODUCT_DETAILS_WEB_URL, methods=['GET'])
def product_details(product_id):
    product = Products.objects(id=product_id).first()
    if not product:
        return "Product not found", 404

    sizes_data = {}
    gallery_data = {}

    for variant in product.variants:
        # Populate sizes_data
        if variant.size not in sizes_data:
            sizes_data[variant.size] = {
                'product_id': str(product.id),
                'value': variant.size,
                'size_type': 'standard',
                'id': str(variant.id) + '_size',
                'variants': []
            }
        sizes_data[variant.size]['variants'].append({
            'value': variant.color_hexa_code if hasattr(variant, 'color_hexa_code') else variant.color,
            'name': variant.color,
            'stock_quantity': variant.stock_quantity,
            'id': str(variant.id)
        })

        # Populate gallery_data (using a set for uniqueness)
        for image in variant.images:
            if variant.color not in gallery_data:
                gallery_data[variant.color] = set()
            gallery_data[variant.color].add((str(image.id), image.image_url))

    # Create the final gallery list
    gallery = []
    for color, image_set in gallery_data.items():
        for img_id, img_url in image_set:
            gallery.append({
                'color': color,
                'id': img_id,
                'img_url': img_url
            })

    thumbnail_url = None
    if product.variants and product.variants[0].images:
        thumbnail_url = product.variants[0].images[0].image_url

    product_dict = {
        'seller_id': str(product.seller_id.id) if product.seller_id else None,
        'title': product.name,
        'description': product.description,
        'details': product.details,
        'price': float(product.price) if product.price else None,
        'discount_percent': product.discount_price,
        'sku': product.sku_number,
        'stock_quantity': sum(v.stock_quantity for v in product.variants) if product.variants else 0,
        'final_price': product.final_price,
        'id': str(product.id),
        'thumbnail_url': thumbnail_url,
        'sizes': list(sizes_data.values()),
        'gallery': gallery,
        'category': {
            'name': product.category_id.name if product.category_id else None,
            'description': getattr(product.category_id, 'description', None),
            'id': str(product.category_id.id) if product.category_id else None,
            'img_url': getattr(product.category_id, 'img_url', None)
        },
        'sub_category': {
            'name': product.subcategory_id.name if product.subcategory_id else None,
            'description': getattr(product.subcategory_id, 'description', None),
            'category_id': str(product.subcategory_id.category.id) if product.subcategory_id and product.subcategory_id.category else None,
            'id': str(product.subcategory_id.id) if product.subcategory_id else None,
            'img_url': getattr(product.subcategory_id, 'img_url', None)
        },
        'sub_sub_category': {
            'name': product.subsubcategory_id.name if product.subsubcategory_id else None,
            'description': getattr(product.subsubcategory_id, 'description', None),
            'category_id': str(product.subsubcategory_id.category_id.id) if product.subsubcategory_id and product.subsubcategory_id.category_id else None,
            'sub_category_id': str(product.subsubcategory_id.sub_category_id.id) if product.subsubcategory_id and product.subsubcategory_id.sub_category_id else None,
            'id': str(product.subsubcategory_id.id) if product.subsubcategory_id else None,
            'img_url': getattr(product.subsubcategory_id, 'img_url', None)
        },
        'brand': {
            'name': product.brand_id.name if product.brand_id else None,
            'description': getattr(product.brand_id, 'description', None),
            'id': str(product.brand_id.id) if product.brand_id else None,
            'img_url': getattr(product.brand_id, 'img_url', None)
        }
    }

    return render_template('admin/products/product_details.html', product=product_dict, local_ip=local_ip)



@admin_api.route(GET_PROUDCT_EDIT_PAGE_BY_ID_WEB_URL, methods=['GET'])
def edit_product(product_id):
    product = Products.objects(id=product_id).first()
    if not product:
        return "Product not found", 404

    colors_data = {}
    
    for variant in product.variants:
        color_name = variant.color
        color_value = variant.color_hexa_code if hasattr(variant, 'color_hexa_code') else variant.color
        
        if color_name not in colors_data:
            colors_data[color_name] = {
                'name': color_name,
                'value': color_value,
                'sizes': [],
                'images': set()
            }
        
        colors_data[color_name]['sizes'].append({
            'size': variant.size,
            'size_type': 'standard',
            'stock_quantity': variant.stock_quantity,
            'variant_id': str(variant.id)
        })
        
        for image in variant.images:
            colors_data[color_name]['images'].add(image.image_url)
    
    for color_data in colors_data.values():
        color_data['images'] = list(color_data['images'])

    product_dict = {
        'seller_id': str(product.seller_id.id) if product.seller_id else None,
        'title': product.name,
        'description': product.description,
        'details': product.details,
        'price': float(product.price) if product.price else None,
        'discount_percent': product.discount_price,
        'sku': product.sku_number,
        'stock_quantity': sum(v.stock_quantity for v in product.variants) if product.variants else 0,
        'final_price': product.final_price,
        'id': str(product.id),
        'colors': list(colors_data.values()),
        'category': {
            'name': product.category_id.name if product.category_id else None,
            'id': str(product.category_id.id) if product.category_id else None,
        },
        'sub_category': {
            'name': product.subcategory_id.name if product.subcategory_id else None,
            'id': str(product.subcategory_id.id) if product.subcategory_id else None,
        },
        'sub_sub_category': {
            'name': product.subsubcategory_id.name if product.subsubcategory_id else None,
            'id': str(product.subsubcategory_id.id) if product.subsubcategory_id else None,
        },
        'brand': {
            'name': product.brand_id.name if product.brand_id else None,
            'id': str(product.brand_id.id) if product.brand_id else None,
        }
    }

    return render_template('admin/products/product_edit.html', product=product_dict, local_ip=local_ip)
