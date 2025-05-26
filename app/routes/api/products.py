from flask import Blueprint, request, jsonify, session
import json
from datetime import datetime
from constants import ADD_NEW_PRODUCT_API, PRODUCT_LISTS_API, EDIT_PRODUCT_API, PRODUCT_LISTS_BY_ID_API
from app.models import Products, Category, SubCategory, SubSubCategory, Seller, User
from app.models.products import ProductVariant, ProductVariantImage
from app.utils.image_upload import upload_image, get_local_ip
from app.utils.validation import validate_required_fields
from app.utils.utils import create_error_response
from app.models.brands import ProductBrands
from bson import ObjectId
from constants import ALLOWED_SIZES, ALLOWED_GENDERS
from flask import current_app

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

        user = User.objects(id=user_object_id).first()
        if not user:
            return create_error_response({'user_id': 'User not found'}, 404)

        seller = Seller.objects(user_id=user_object_id).first()
        if not seller:
            return create_error_response({'seller': 'Seller profile not found'}, 400)

        required_fields = ['name', 'price', 'category_id', 'subcategory_id', 'subsubcategory_id', 'details', 'description', 'stock_quantity', 'sku_number']
        form_data = request.form.to_dict(flat=False)
        data = {k: v[0] if len(v) == 1 else v for k, v in form_data.items()}

        is_valid, validation_errors = validate_required_fields(data, required_fields)
        if not is_valid:
            return create_error_response({'validation': validation_errors}, 400)

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

        try:
            variations_list = json.loads(data.get('variations', '[]'))
        except json.JSONDecodeError:
            return create_error_response({'variations': 'Invalid variations format'}, 400)

        variants = []
        for var in variations_list:
            try:
                size = var['size']
                color = var['color']
                stock_quantity = int(var.get('stock_quantity', 0))
                color_hexa_code = var.get('color_hexa_code')
                variant = ProductVariant(
                    size=size,
                    color=color,
                    color_hexa_code=color_hexa_code,
                    stock_quantity=stock_quantity,
                    product_id=None
                )
                variants.append(variant)
            except (KeyError, ValueError) as e:
                return create_error_response({'variations': f'Invalid variation data: {str(e)}'}, 400)

        color_size_images = {}
        for file_key in request.files:
            if file_key.startswith('images[') and ']' in file_key:
                try:
                    parts = file_key.split('[')
                    color = parts[1].split(']')[0]
                    size = parts[2].split(']')[0]
                    
                    if color not in color_size_images:
                        color_size_images[color] = {}
                    if size not in color_size_images[color]:
                        color_size_images[color][size] = []
                        
                    for file in request.files.getlist(file_key):
                        image_path, error = upload_image(file)
                        if error:
                            return create_error_response({'images': error}, 400)
                        color_size_images[color][size].append(image_path)
                except Exception as e:
                    return create_error_response({'images': f'Invalid image key format: {str(e)}'}, 400)

        saved_variants = []
        for variant in variants:
            variant.save()
            saved_variants.append(variant)

        variant_images_map = {}

        for variant in saved_variants:
            color = variant.color
            size = variant.size
            if color in color_size_images and size in color_size_images[color]:
                for image_url in color_size_images[color][size]:
                    if image_url not in variant_images_map:
                        image = ProductVariantImage(
                            variant_id=variant.id,
                            image_url=image_url,
                            alt_text=f"{data['name']} - {color} - {size}",
                        )
                        image.save()
                        variant_images_map[image_url] = image
                    variant.images.append(variant_images_map[image_url])
            variant.save()

        product = Products(
            seller_id=seller.id,
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
            final_price=final_price,
            material=material,
            gender=gender,
            status='active',
            variants=saved_variants,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        product.save()

        for image_obj in variant_images_map.values():
            for variant in saved_variants:
                if image_obj in variant.images:
                    image_obj.product_id = product.id
                    image_obj.save()
                    break

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
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        category_id = request.args.get('category_id')
        subcategory_id = request.args.get('subcategory_id')
        subsubcategory_id = request.args.get('subsubcategory_id')
        brand_id = request.args.get('brand_id')
        status = request.args.get('status')
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        query = Products.objects()

        local_ip = get_local_ip()
        port = current_app.config.get('SERVER_PORT', 8080)

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

        if sort_order == 'desc':
            query = query.order_by(f'-{sort_by}')
        else:
            query = query.order_by(f'+{sort_by}')

        paginated_products = query.paginate(page=page, per_page=per_page)
        products_data = []

        for product in paginated_products.items:
            sizes_data = {}
            gallery_data = {}

            for variant in product.variants:
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
                        'img_url': f"http://{local_ip}:{port}/static/uploads/{image.image_url}"
                    })

            thumbnail_url = None
            if product.variants and product.variants[0].images:
                image_url = product.variants[0].images[0].image_url
                thumbnail_url =  f"http://{local_ip}:{port}/static/uploads/{image_url}"

            seller_data = None
            if product.seller_id:
                try:
                    user = User.objects(id=product.seller_id.id).first()
                    if user:
                        seller = Seller.objects(user_id=user.id).first()
                        if seller:
                            seller_data = {
                                'id': str(seller.id),
                                'businessName': seller.businessName
                            }
                        else:
                            seller_data = {'id': str(product.seller_id.id), 'businessName': 'Unknown Seller'}
                    else:
                        seller_data = {'id': str(product.seller_id.id), 'businessName': 'Unknown Seller'}
                except Exception as e:
                    print(f"Error fetching seller for product {product.id}: {str(e)}")
                    seller_data = {'id': str(product.seller_id.id), 'businessName': 'Unknown Seller'}

            product_dict = {
                'seller': seller_data,
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
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_pages': paginated_products.pages,
                'total_items': paginated_products.total
            }
        }

        return jsonify(response), 200

    except Exception as e:
        return create_error_response({"exception": str(e)}, status_code=500)

@products_bp.route(PRODUCT_LISTS_BY_ID_API, methods=['GET'])
def get_product_by_id(product_id):
    try:
        product = Products.objects(id=product_id).first()

        if not product:
            return create_error_response({"message": "Product not found"}, status_code=404)
        
        local_ip = get_local_ip()
        port = current_app.config.get('SERVER_PORT', 8080)

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
                    'img_url': f"http://{local_ip}:{port}/static/uploads/{image.image_url}"
                })

        thumbnail_url = None
        if product.variants and product.variants[0].images:
            thumbnail_url = f"http://{local_ip}:{port}/static/uploads/{product.variants[0].images[0].image_url}"

        product_data = {
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


@products_bp.route(EDIT_PRODUCT_API, methods=['PUT'])
def edit_product():
    try:
        user_id = session.get('user_id')
        if not user_id:
            return create_error_response({'user_id': 'User not logged in'}, 401)
        
        # Validate IDs
        try:
            user_object_id = ObjectId(user_id)
            product_id = ObjectId(request.form.get('product_id'))
        except Exception:
            return create_error_response({'id': 'Invalid ID format'}, 400)

        # Find the product
        product = Products.objects(id=product_id).first()
        if not product:
            return create_error_response({'product': 'Product not found or unauthorized'}, 404)

        # Prepare update fields
        data = request.form.to_dict()
        update_fields = {
            'name': data.get('name'),
            'description': data.get('description'),
            'details': data.get('details'),
            'price': float(data.get('price', 0)),
            'discount_price': float(data.get('discount_price', 0)),
            'stock_quantity': int(data.get('stock_quantity', 0)),
            'sku_number': data.get('sku_number'),
            'category_id': ObjectId(data.get('category_id')),
            'subcategory_id': ObjectId(data.get('subcategory_id')),
            'subsubcategory_id': ObjectId(data.get('subsubcategory_id')),
            'updated_at': datetime.utcnow()
        }

        # Handle brand
        brand_value = data.get('brand_id')
        other_brand_name = data.get('other_brand')
        
        if brand_value and brand_value != 'other':
            brand = ProductBrands.objects(id=brand_value).first()
            if not brand:
                return create_error_response({'brand': 'Invalid brand ID'}, 400)
            update_fields['brand_id'] = brand
        elif brand_value == 'other' and other_brand_name:
            brand = ProductBrands.objects(name__iexact=other_brand_name.strip()).first()
            if not brand:
                brand = ProductBrands(
                    name=other_brand_name.strip(),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                brand.save()
            update_fields['brand_id'] = brand

        # Parse variations
        try:
            variations_list = json.loads(data.get('variations', '[]'))
        except json.JSONDecodeError:
            return create_error_response({'variations': 'Invalid variations format'}, 400)

        # Process uploaded images
        color_size_images = {}
        for file_key in request.files:
            if file_key.startswith('images[') and ']' in file_key:
                try:
                    # Parse color and size from field name (format: images[color][size])
                    parts = file_key.split('[')
                    color = parts[1].split(']')[0].strip()
                    size = parts[2].split(']')[0].strip()
                    
                    if color not in color_size_images:
                        color_size_images[color] = {}
                    if size not in color_size_images[color]:
                        color_size_images[color][size] = []
                        
                    for file in request.files.getlist(file_key):
                        image_path, error = upload_image(file)
                        if error:
                            return create_error_response({'images': error}, 400)
                        color_size_images[color][size].append(image_path)
                except Exception as e:
                    return create_error_response({'images': f'Invalid image key format: {str(e)}'}, 400)

        # Process variants
        existing_variants = {f"{v.color}_{v.size}": v for v in product.variants}
        new_variant_keys = {f"{v['color']}_{v['size']}" for v in variations_list}
        
        for var in variations_list:
            try:
                color = var['color']
                size = var['size']
                variant_key = f"{color}_{size}"
                
                if variant_key in existing_variants:
                    # Update existing variant
                    variant = existing_variants[variant_key]
                    variant.stock_quantity = int(var.get('stock_quantity', 0))
                    variant.color_hexa_code = var.get('color_hexa_code')
                    variant.updated_at = datetime.utcnow()
                    
                    # Handle images for existing variant
                    if color in color_size_images and size in color_size_images[color]:
                        # Clear existing images if you want to replace them
                        ProductVariantImage.objects(variant_id=variant.id).delete()
                        variant.images = []
                        
                        # Add new images
                        for image_url in color_size_images[color][size]:
                            image = ProductVariantImage(
                                variant_id=variant.id,
                                image_url=image_url,
                                alt_text=f"{update_fields['name']} - {color} - {size}",
                            )
                            image.save()
                            variant.images.append(image)
                    
                    variant.save()
                else:
                    # Create new variant
                    variant = ProductVariant(
                        size=size,
                        color=color,
                        color_hexa_code=var.get('color_hexa_code'),
                        stock_quantity=int(var.get('stock_quantity', 0)),
                        product_id=product.id
                    )
                    variant.save()
                    
                    # Add images if they exist for this new variant
                    if color in color_size_images and size in color_size_images[color]:
                        variant.images = []
                        for image_url in color_size_images[color][size]:
                            image = ProductVariantImage(
                                variant_id=variant.id,
                                image_url=image_url,
                                alt_text=f"{update_fields['name']} - {color} - {size}",
                            )
                            image.save()
                            variant.images.append(image)
                    
                    variant.save()
                    product.variants.append(variant)
                    
            except (KeyError, ValueError) as e:
                return create_error_response({'variations': f'Invalid variation data: {str(e)}'}, 400)

        # Remove variants that are no longer present
        for variant_key, variant in existing_variants.items():
            if variant_key not in new_variant_keys:
                ProductVariantImage.objects(variant_id=variant.id).delete()
                product.variants.remove(variant)
                variant.delete()

        # Update product fields
        product.update(**update_fields)
        product.save()

        return jsonify({
            "message": "Product updated successfully",
            "id": str(product.id),
            "product": {
                "name": product.name,
                "price": float(product.price),
                "discount_price": float(product.discount_price) if product.discount_price else None,
                "final_price": float(product.final_price)
            }
        }), 200

    except Exception as error:
        return create_error_response({'unexpected_error': str(error)}, 500)