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

        required_fields = ['name', 'price', 'category_id', 'subcategory_id', 'subsubcategory_id', 'details', 'description', 'stock_quantity', 'sku_number']
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

        price = float(data['price'])
        discount_price = float(data.get('discount_price', 0))

        final_price = price

        if discount_price > 0:
            final_price = price - (price * discount_price / 100)
            
        material = data.get('material')
        description = data.get('description')
        gender = data.get('gender') if data.get('gender') in ALLOWED_GENDERS else None
        stock_quantity = data.get('stock_quantity')
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
                color_hexa_code = var.get('color_hexa_code')
                variant = ProductVariant(
                    size=size,
                    color=color,
                    color_hexa_code=color_hexa_code,
                    stock_quantity=quantity,
                    product_id=None
                )
                variants.append(variant)
            except (KeyError, ValueError) as e:
                return create_error_response({'variations': f'Invalid variation data: {str(e)}'}, 400)

        # Process color-specific images and store their URLs temporarily
        color_images = {}
        for file_key in request.files:
            if file_key.startswith('images[') and file_key.endswith(']'):
                color_name = file_key[7:-1]
                if color_name not in color_images:
                    color_images[color_name] = set()  # Use a set for unique image paths
                for file in request.files.getlist(file_key):
                    image_path, error = upload_image(file)
                    if error:
                        return create_error_response({'images': error}, 400)
                    color_images[color_name].add(image_path)

        # Save all variants
        saved_variants = []
        for variant in variants:
            variant.save()
            saved_variants.append(variant)

        # Create and associate ProductVariantImage objects
        variant_images_map = {}  # To store already created image objects by URL

        for variant in saved_variants:
            color = variant.color
            if color in color_images:
                for image_url in color_images[color]:
                    # Check if this image URL has already been processed
                    if image_url not in variant_images_map:
                        image = ProductVariantImage(
                            variant_id=variant.id,  # Initially set variant_id
                            image_url=image_url,
                            alt_text=f"{data['name']} - {color} - {variant.size}",
                            is_primary=False
                        )
                        image.save()
                        variant_images_map[image_url] = image
                    variant.images.append(variant_images_map[image_url])  # Append the reference
            variant.save()

        # Handle thumbnail (primary image - attach to first variant)
        if 'thumbnail' in request.files:
            thumbnail_file = request.files['thumbnail']
            if thumbnail_file.filename != '':
                thumbnail_path, error = upload_image(thumbnail_file)
                if error:
                    return create_error_response({'thumbnail': error}, 400)

                if saved_variants:
                    if thumbnail_path not in variant_images_map:
                        primary_image = ProductVariantImage(
                            variant_id=saved_variants[0].id,
                            image_url=thumbnail_path,
                            alt_text=f"{data['name']} - thumbnail",
                            is_primary=True
                        )
                        primary_image.save()
                        variant_images_map[thumbnail_path] = primary_image
                    saved_variants[0].images.append(variant_images_map[thumbnail_path])
                    saved_variants[0].save()

        # Create the product
        product = Products(
            user_id=user_object_id,
            name=data['name'],
            description=data.get('description'),
            details=data.get('details'),
            category_id=category,
            subcategory_id=subcategory,
            subsubcategory_id=subsubcategory,
            brand_id=brand,
            sku_number=sku_number,
            price=price,
            stock_quantity=stock_quantity,
            discount_price=discount_price,
            final_price=final_price,  # Store the calculated final price
            material=material,
            gender=gender,
            status='active',
            variants=saved_variants,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        product.save()

        # Now assign the correct product_id to the ProductVariantImage objects
        for image_obj in variant_images_map.values():
            for variant in saved_variants:
                if image_obj in variant.images:
                    image_obj.product_id = product.id
                    image_obj.save()
                    break

        # Finally, update variants with the correct product_id
        for variant in saved_variants:
            variant.product_id = product
            variant.save()

        return jsonify({
            "message": "Product created successfully",
            "id": str(product.id),
            "product": {
                "name": product.name,
                "price": float(product.price),
                "discount_price": float(product.discount_price) if product.discount_price else None,
                "final_price": float(product.final_price)
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

                for image in variant.images:
                    if variant.color not in gallery_data:
                        gallery_data[variant.color] = []
                    gallery_data[variant.color].append({
                        'color': variant.color,
                        'id': str(image.id),
                        'img_url': image.image_url
                    })

            final_price = float(product.discount_price) if product.discount_price is not None else (float(product.price) if product.price is not None else None)
            discount_percent = None
            if product.price is not None and final_price is not None and float(product.price) > 0:
                discount_percent = round(((float(product.price) - final_price) / float(product.price)) * 100)


            thumbnail_url = None
            if product.variants and product.variants[0].images:
                thumbnail_url = product.variants[0].images[0].image_url

            product_dict = {
                'user_id': str(product.user_id.id) if product.user_id else None,
                'title': product.name,
                'description': product.description,
                'details': product.details,
                'price': float(product.price) if product.price else None,
                'discount_percent': discount_percent,
                'sku': product.sku_number,
                'stock_quantity': sum(v.stock_quantity for v in product.variants) if product.variants else 0,
                'final_price': final_price,
                'id': str(product.id),
                'thumbnail_url': thumbnail_url,
                'sizes': list(sizes_data.values()),
                'gallery': [img for color_gallery in gallery_data.values() for img in color_gallery],
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
            products_data.append(product_dict)

        response = {
            'data': products_data,
        }

        return jsonify(response), 200

    except Exception as e:
        return create_error_response({"exception": str(e)}, status_code=500)


@products_bp.route('/api/products/<string:product_id>', methods=['GET'])
def get_product_by_id(product_id):
    try:
        product = Products.objects(id=product_id).first()

        if not product:
            return create_error_response({"message": "Product not found"}, status_code=404)

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

            for image in variant.images:
                if variant.color not in gallery_data:
                    gallery_data[variant.color] = []
                gallery_data[variant.color].append({
                    'color': variant.color,
                    'id': str(image.id),
                    'img_url': image.image_url
                })

        final_price = float(product.discount_price) if product.discount_price is not None else (float(product.price) if product.price is not None else None)
        discount_percent = None
        if product.price is not None and final_price is not None and float(product.price) > 0:
            discount_percent = round(((float(product.price) - final_price) / float(product.price)) * 100)

        thumbnail_url = None
        if product.variants and product.variants[0].images:
            thumbnail_url = product.variants[0].images[0].image_url

        product_data = {
            'user_id': str(product.user_id.id) if product.user_id else None,
            'title': product.name,
            'description': product.description,
            'details': product.details,
            'price': float(product.price) if product.price else None,
            'discount_percent': discount_percent,
            'sku': product.sku_number,
            'stock_quantity': sum(v.stock_quantity for v in product.variants) if product.variants else 0,
            'final_price': final_price,
            'id': str(product.id),
            'thumbnail_url': thumbnail_url,
            'sizes': list(sizes_data.values()),
            'gallery': [img for color_gallery in gallery_data.values() for img in color_gallery],
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

        response = {
            'data': product_data,
        }

        return jsonify(response), 200

    except Exception as e:
        return create_error_response({"exception": str(e)}, status_code=500)