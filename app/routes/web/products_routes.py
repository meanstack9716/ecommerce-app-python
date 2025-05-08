from flask import render_template, redirect, url_for, session, request
from constants import ADD_NEW_PRODUCT_WEB_URL, GET_PRODUCT_LIST_WEB_URL
from . import admin_api
from app.models import Category, SubCategory, SubSubCategory, Products


@admin_api.route(ADD_NEW_PRODUCT_WEB_URL, methods=['GET'])
def add_products_page():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))

    categories = Category.objects.all()

    return render_template(
        'admin/products/add_new_product.html',
        categories=categories,
    )

@admin_api.route(GET_PRODUCT_LIST_WEB_URL, methods=['GET'])
def get_product_lists():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('limit', 10, type=int)

    category = request.args.get('category')
    status = request.args.get('status')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)

    query = {}

    if category:
        category_obj = Category.objects(name=category).first()
        if category_obj:
            query['category_id'] = category_obj.id

    if status:
        query['status'] = status

    if min_price is not None:
        query['final_price__gte'] = min_price

    if max_price is not None:
        query['final_price__lte'] = max_price

    products = Products.objects(**query).order_by('-created_at').paginate(page=page, per_page=per_page)
    categories = Category.objects.all()

    return render_template(
        'admin/products/product_lists.html',
        products=products,
        categories=categories,
    )

@admin_api.route('/products/<product_id>', methods=['GET'])
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
        'user_id': str(product.user_id.id) if product.user_id else None,
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
        'gallery': gallery,  # Use the processed unique gallery list
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

    return render_template('admin/products/product_details.html', product=product_dict)