from flask import Blueprint, request, jsonify, session
from datetime import datetime
from constants import ADD_NEW_PRODUCT_API, PRODUCT_LISTS_API
from app.models import AddProducts, Category, SubCategory, SubSubCategory
from app.utils.image_upload import upload_image
from app.utils.validation import validate_required_fields
from app.utils.utils import create_error_response
from app.models.brands import ProductBrands
from bson import ObjectId

from app.extensions import db

products_bp = Blueprint('products_bp', __name__)

@products_bp.route(ADD_NEW_PRODUCT_API, methods=['POST'])
def create_ad():
    user_id = session.get('user_id')
    if not user_id:
        return create_error_response({'user_id': 'User not logged in'})
    
    try:
        try:
            user_object_id = ObjectId(user_id)
        except Exception:
            return create_error_response({'user_id': 'Invalid user ID'})

        required_fields = ['title', 'price', 'sku', 'category_id', 'sub_category_id', 'product_type_id', 'description', 'stock']
        
        form_data = request.form.to_dict(flat=False)
        data = {k: v[0] if len(v) == 1 else v for k, v in form_data.items()}
        
        is_valid, validation_errors = validate_required_fields(data, required_fields)
        if not is_valid:
            return create_error_response(validation_errors)
        
        category = Category.objects(id=data['category_id']).first()
        sub_category = SubCategory.objects(id=data['sub_category_id']).first()
        product_type = SubSubCategory.objects(id=data['product_type_id']).first()
        
        if not category or not sub_category or not product_type:
            id_errors = {}
            if not category:
                id_errors['category_id'] = 'Invalid category ID'
            if not sub_category:
                id_errors['sub_category_id'] = 'Invalid sub_category ID'
            if not product_type:
                id_errors['product_type_id'] = 'Invalid product_type ID'
            return create_error_response(id_errors)
        
        if 'images' not in request.files or len(request.files.getlist('images')) == 0:
            return create_error_response({'images': 'No images uploaded'})

        uploaded_files = request.files.getlist('images')
        images = []
        for image in uploaded_files:
            image_path, error = upload_image(image)
            if error:
                return create_error_response({'images': error})
            if image_path:
                images.append(image_path)
        
        price = float(data['price'])
        discount_percent = float(data.get('discount_percent', 0))
        final_price = price - (price * discount_percent / 100)

        brand_id = None
        brand_value = data.get('brand')
        other_brand_name = data.get('other_brand')

        if brand_value and brand_value != 'other':
            existing_brand = ProductBrands.objects(id=brand_value).first()
            if not existing_brand:
                return create_error_response({'brand': 'Invalid brand ID'})
            brand_id = existing_brand
        elif brand_value == 'other' and other_brand_name:
            existing_brand = ProductBrands.objects(name__iexact=other_brand_name.strip()).first()
            if existing_brand:
                brand_id = existing_brand
            else:
                new_brand = ProductBrands(
                    name=other_brand_name.strip(),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                new_brand.save()
                brand_id = new_brand
        else:
            brand_id = None
        
        color = request.form.getlist('color')
        size = request.form.getlist('size')
        tags = request.form.getlist('tags')
        
        ad = AddProducts(
            title=data['title'],
            description=data.get('description'),
            price=price,
            discount_percent=discount_percent,
            final_price=final_price,
            sku=data['sku'],
            brand_id=brand_id,
            color=color,
            size=size,
            material=data.get('material'),
            gender=data.get('gender'),
            stock=int(data.get('stock', 0)),
            images=images,
            tags=tags,
            user_id=user_object_id,
            category_id=category,
            sub_category_id=sub_category,
            product_type_id=product_type,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        ad.save()
        
        return jsonify({"message": "Ad created successfully", "id": str(ad.id)}), 201
    
    except Exception as e:
        return create_error_response({"exception": str(e)}, status_code=500)


@products_bp.route(PRODUCT_LISTS_API, methods=['GET'])
def list_products():
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        category_id = request.args.get('category_id')
        sub_category_id = request.args.get('sub_category_id')
        product_type_id = request.args.get('product_type_id')
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        query = AddProducts.objects()
        
        if category_id:
            query = query.filter(category_id=category_id)
        if sub_category_id:
            query = query.filter(sub_category_id=sub_category_id)
        if product_type_id:
            query = query.filter(product_type_id=product_type_id)
        
        if sort_order == 'desc':
            query = query.order_by(f'-{sort_by}')
        else:
            query = query.order_by(f'+{sort_by}')
        
        paginated_products = query.paginate(page=page, per_page=per_page)
        
        products_data = []
        for product in paginated_products.items:
            products_data.append({
                'id': str(product.id),
                'title': product.title,
                'price': product.price,
                'final_price': product.final_price,
                'discount_percent': product.discount_percent,
                'images': product.images,
                'category': {
                    'id': str(product.category_id.id),
                    'name': product.category_id.name
                } if product.category_id else None,
                'sub_category': {
                    'id': str(product.sub_category_id.id),
                    'name': product.sub_category_id.name
                } if product.sub_category_id else None,
                'product_type': {
                    'id': str(product.product_type_id.id),
                    'name': product.product_type_id.name
                } if product.product_type_id else None,
                'created_at': product.created_at.isoformat() if product.created_at else None
            })
        
        response = {
            'data': products_data,
            # 'total': paginated_products.total,
            # 'pages': paginated_products.pages,
            # 'current_page': paginated_products.page,
            # 'per_page': paginated_products.per_page
        }
        
        return jsonify(response), 200
    
    except Exception as e:
        return create_error_response({"exception": str(e)}, status_code=500)