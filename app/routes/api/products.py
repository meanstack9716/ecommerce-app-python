from flask import Blueprint, request, jsonify, session
import json
from datetime import datetime
from constants import ADD_NEW_PRODUCT_API, PRODUCT_LISTS_API
from app.models import Products, Category, SubCategory, SubSubCategory
from app.models.products import ProductVariant, ProductVariantImage
from app.utils.image_upload import upload_image
from app.utils.validation import validate_required_fields
from app.utils.utils import create_error_response
from app.models.brands import ProductBrands
from bson import ObjectId
from constants import ALLOWED_SIZES, ALLOWED_GENDERS

from app.extensions import db

products_bp = Blueprint('products_bp', __name__)


@products_bp.route(ADD_NEW_PRODUCT_API, methods=['POST'])
def create_ad():
    try:
        user_id = session.get('user_id')
        if not user_id:
            return create_error_response({'user_id': 'User not logged in'}, 401)
        try:
            user_object_id = ObjectId(user_id)
        except Exception:
            return create_error_response({'user_id': 'Invalid user ID'}, 400)

        required_fields = ['name', 'price', 'category_id', 'subcategory_id', 'subsubcategory_id', 'description', 'total_stocks', 'sku_number']
        form_data = request.form.to_dict(flat=False)
        data = {k: v[0] if len(v) == 1 else v for k, v in form_data.items()}

        is_valid, validation_errors = validate_required_fields(data, required_fields)
        if not is_valid:
            return create_error_response({'validation': validation_errors}, 400)

        # Fetch category references
        category = Category.objects(id=data['category_id']).first()
        subcategory = SubCategory.objects(id=data['subcategory_id']).first()
        subsubcategory = SubSubCategory.objects(id=data['subsubcategory_id']).first()

        if not category or not subcategory or not subsubcategory:
            return create_error_response({
                'category_id': 'Invalid category ID',
                'subcategory_id': 'Invalid subcategory ID',
                'subsubcategory_id': 'Invalid subsubcategory ID'
            }, 400)

        # Calculate price and discount
        price = float(data['price'])
        discount_price = float(data.get('discount_price', price))
        material = data.get('material')
        gender = data.get('gender') if data.get('gender') in ALLOWED_GENDERS else None
        total_stocks = data.get('total_stocks')
        sku_number = data.get('sku_number')
        if not sku_number:
            return create_error_response({'sku_number': 'SKU number is required'}, 400)

        # Handle brand
        brand = None
        brand_value = data.get('brand_id')
        other_brand_name = data.get('other_brand')

        if brand_value and brand_value != 'other':
            brand = ProductBrands.objects(id=brand_value).first()
            if not brand:
                return create_error_response({'brand': 'Invalid brand ID'}, 400)
        elif brand_value == 'other' and other_brand_name:
            brand = ProductBrands.objects(name__iexact=other_brand_name.strip()).first()
            if not brand:
                brand = ProductBrands(
                    name=other_brand_name.strip(),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                brand.save()

        # Process variations
        try:
            variations_list = json.loads(data.get('variations', '[]'))
        except json.JSONDecodeError:
            return create_error_response({'variations': 'Invalid variations format'}, 400)

        variants = []
        for var in variations_list:
            try:
                size = var['size']
                color = var['color']
                quantity = int(var.get('quantity', 0))

                variant = ProductVariant(
                    size=size,
                    color=color,
                    stock_quantity=quantity,
                    product_id=None
                )
                variants.append(variant)
            except (KeyError, ValueError) as e:
                return create_error_response({'variations': f'Invalid variation data: {str(e)}'}, 400)

        # Process color-specific images
        color_images = {}
        for file_key in request.files:
            if file_key.startswith('images[') and file_key.endswith(']'):
                color_name = file_key[7:-1]
                if color_name not in color_images:
                    color_images[color_name] = []
                for file in request.files.getlist(file_key):
                    image_path, error = upload_image(file)
                    if error:
                        return create_error_response({'images': error}, 400)
                    color_images[color_name].append(image_path)

        # Save all variants
        saved_variants = []
        for variant in variants:
            variant.save()
            saved_variants.append(variant)

        # Associate color images with variants
        for variant in saved_variants:
            color = variant.color
            if color in color_images:
                for image_url in color_images[color]:
                    image = ProductVariantImage(
                        variant_id=variant.id,
                        image_url=image_url,
                        alt_text=f"{data['name']} - {color} - {variant.size}",
                        is_primary=False
                    )
                    image.save()
                    variant.images.append(image)
            variant.save()

        # Handle thumbnail (primary image - attach to first variant)
        thumbnail_path = None
        if 'thumbnail' in request.files:
            thumbnail_file = request.files['thumbnail']
            if thumbnail_file.filename != '':
                thumbnail_path, error = upload_image(thumbnail_file)
                if error:
                    return create_error_response({'thumbnail': error}, 400)

                if saved_variants:
                    primary_image = ProductVariantImage(
                        variant_id=saved_variants[0],
                        image_url=thumbnail_path,
                        alt_text=f"{data['name']} - thumbnail",
                        is_primary=True
                    )
                    primary_image.save()
                    saved_variants[0].images.append(primary_image)
                    saved_variants[0].save()

        # Create the product
        product = Products(
            user_id=user_object_id,
            name=data['name'],
            description=data.get('description'),
            category_id=category,
            subcategory_id=subcategory,
            subsubcategory_id=subsubcategory,
            brand_id=brand,
            sku_number=sku_number,
            price=price,
            total_stocks=total_stocks,
            discount_price=discount_price,
            material=material,
            gender=gender,
            status='active',
            variants=saved_variants,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        product.save()

        # Now assign product_id to variants
        for variant in saved_variants:
            variant.product_id = product
            variant.save()

        return jsonify({
            "message": "Product created successfully",
            "id": str(product.id),
            "product": {
                "name": product.name,
                "price": float(product.price),
                "discount_price": float(product.discount_price) if product.discount_price else None
            }
        }), 201

    except Exception as error:
        return create_error_response({'unexpected_error': str(error)}, 500)

@products_bp.route(PRODUCT_LISTS_API, methods=['GET'])
def list_products():
    try:
        # Pagination params
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))

        # Filter params
        category_id = request.args.get('category_id')
        subcategory_id = request.args.get('subcategory_id')
        subsubcategory_id = request.args.get('subsubcategory_id')
        brand_id = request.args.get('brand_id')
        status = request.args.get('status')

        # Sorting params
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')

        # Query base
        query = Products.objects()

        # Apply filters
        if category_id:
            query = query.filter(category_id=category_id)
        if subcategory_id:
            query = query.filter(subcategory_id=subcategory_id)
        if subsubcategory_id:
            query = query.filter(subsubcategory_id=subsubcategory_id)
        if brand_id:
            query = query.filter(brand_id=brand_id)
        if status:
            query = query.filter(status=status)

        # Sorting
        if sort_order == 'desc':
            query = query.order_by(f'-{sort_by}')
        else:
            query = query.order_by(f'+{sort_by}')

        # Paginate
        paginated_products = query.paginate(page=page, per_page=per_page)

        products_data = []

        for product in paginated_products.items:
            # Get variant data
            variants_data = []
            for variant in product.variants:
                variant_images_data = []
                for image in variant.images:
                    variant_images_data.append({
                        'id': str(image.id),
                        'image_url': image.image_url,
                        'alt_text': image.alt_text,
                        'is_primary': image.is_primary
                    })
                variants_data.append({
                    'id': str(variant.id),
                    'size': variant.size,
                    'color': variant.color,
                    'stock_quantity': variant.stock_quantity,
                    'images': variant_images_data
                })

            # Build product dict
            product_dict = {
                'id': str(product.id),
                'name': product.name,
                'description': product.description,
                'price': float(product.price) if product.price else None,
                'discount_price': float(product.discount_price) if product.discount_price else None,
                'total_stocks': product.total_stocks,
                'sku_number': product.sku_number,
                'material': product.material,
                'gender': product.gender,
                'status': product.status,
                'category': {
                    'id': str(product.category_id.id),
                    'name': product.category_id.name
                } if product.category_id else None,
                'subcategory': {
                    'id': str(product.subcategory_id.id),
                    'name': product.subcategory_id.name
                } if product.subcategory_id else None,
                'subsubcategory': {
                    'id': str(product.subsubcategory_id.id),
                    'name': product.subsubcategory_id.name
                } if product.subsubcategory_id else None,
                'brand': {
                    'id': str(product.brand_id.id),
                    'name': product.brand_id.name
                } if product.brand_id else None,
                'variants': variants_data,
                'created_at': product.created_at.isoformat() if product.created_at else None,
                'updated_at': product.updated_at.isoformat() if product.updated_at else None
            }

            products_data.append(product_dict)

        response = {
            'data': products_data,
            # 'page': page,
            # 'per_page': per_page,
            # 'total': paginated_products.total,
            # 'pages': paginated_products.pages
        }

        return jsonify(response), 200

    except Exception as e:
        return create_error_response({"exception": str(e)}, status_code=500)
