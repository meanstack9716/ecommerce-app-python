from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.products import Products
from app.models.category_modal import Category, SubCategory, SubSubCategory
from app.models.brands import ProductBrands
from mongoengine.queryset.visitor import Q
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

search_bp = Blueprint('search', __name__)

@search_bp.route('/api/search', methods=['GET'])
def search_products():
    try:
        keyword = request.args.get('keyword', '').strip()
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))

        if not keyword:
            return jsonify({
                'status': 'error',
                'message': 'Keyword is required'
            }), 400

        if page < 1:
            page = 1
        if per_page < 1 or per_page > 50:
            per_page = 10

        search_query = Q(name__icontains=keyword) | \
                      Q(description__icontains=keyword) | \
                      Q(details__icontains=keyword) | \
                      Q(material__icontains=keyword)

        category_ids = [str(cat.id) for cat in Category.objects(name__icontains=keyword).only('id')]
        subcategory_ids = [str(subcat.id) for subcat in SubCategory.objects(name__icontains=keyword).only('id')]
        subsubcategory_ids = [str(subsubcat.id) for subsubcat in SubSubCategory.objects(name__icontains=keyword).only('id')]
        brand_ids = [str(brand.id) for brand in ProductBrands.objects(name__icontains=keyword).only('id')]

        if category_ids:
            search_query |= Q(category_id__in=category_ids)
        if subcategory_ids:
            search_query |= Q(subcategory_id__in=subcategory_ids)
        if subsubcategory_ids:
            search_query |= Q(subsubcategory_id__in=subsubcategory_ids)
        if brand_ids:
            search_query |= Q(brand_id__in=brand_ids)

        product_queryset = Products.objects(search_query & Q(status='active'))
        logger.debug(f"QuerySet type: {type(product_queryset)}")

        total_results = product_queryset.count()
        products = product_queryset.skip((page - 1) * per_page).limit(per_page)

        product_data = []
        for product in products:
            product_dict = {
                'id': str(product.id),
                'name': product.name,
                'sku_number': product.sku_number,
                'price': float(product.price),
                'final_price': float(product.final_price),
                'discount_price': float(product.discount_price) if product.discount_price else None,
                'category': {
                    'id': str(product.category_id.id),
                    'name': product.category_id.name
                },
                'subcategory': {
                    'id': str(product.subcategory_id.id),
                    'name': product.subcategory_id.name
                },
                'subsubcategory': {
                    'id': str(product.subsubcategory_id.id),
                    'name': product.subsubcategory_id.name
                },
                'brand': {
                    'id': str(product.brand_id.id),
                    'name': product.brand_id.name,
                    'logo_path': product.brand_id.logo_path,
                    'description': product.brand_id.description
                },
                'stock_quantity': product.stock_quantity,
                'material': product.material,
                'gender': product.gender,
                'status': product.status,
                'created_at': product.created_at.isoformat(),
                'variants': [{
                    'id': str(variant.id),
                    'size': variant.size,
                    'color': variant.color,
                    'color_hexa_code': variant.color_hexa_code,
                    'stock_quantity': variant.stock_quantity,
                    'images': [{
                        'image_url': image.image_url,
                        'alt_text': image.alt_text
                    } for image in variant.images]
                } for variant in product.variants]
            }
            product_data.append(product_dict)

        pagination = {
            'page': page,
            'per_page': per_page,
            'total_pages': (total_results + per_page - 1) // per_page,
            'total_results': total_results
        }

        return jsonify({
            'status': 'success',
            'data': product_data,
            'pagination': pagination
        }), 200

    except ValueError:
        return jsonify({
            'status': 'error',
            'message': 'Invalid page or per_page parameters'
        }), 400
    except Exception as e:
        logger.error(f"Error in search_products: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'An error occurred: {str(e)}'
        }), 500