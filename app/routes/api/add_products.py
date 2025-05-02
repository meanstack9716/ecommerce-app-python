from flask import Blueprint, request, jsonify
from datetime import datetime
from constants import ADD_NEW_PRODUCT
from app.models import AdsProduct, Category, SubCategory, SubSubCategory
from app.utils.image_upload import upload_image
from app.utils.validation import validate_required_fields
from app.utils.utils import create_error_response

from app.extensions import db

add_products_bp = Blueprint('add_products_bp', __name__)

@add_products_bp.route(ADD_NEW_PRODUCT, methods=['POST'])
def create_ad():
    try:
        required_fields = ['title', 'price', 'sku', 'category_id', 'sub_category_id', 'product_type_id']
        
        form_data = request.form.to_dict(flat=False)
        # Flatten single values
        data = {k: v[0] if len(v) == 1 else v for k, v in form_data.items()}
        
        # Validate required fields
        is_valid, validation_errors = validate_required_fields(data, required_fields)
        if not is_valid:
            return create_error_response(validation_errors)
        
        # Validate related IDs
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
        if 'images' in request.files:
            for image in uploaded_files:
                image_path, error = upload_image(image)
                if error:
                    return create_error_response({'images': error})
                if image_path:
                    images.append(image_path)
        
        price = float(data['price'])
        discount_percent = float(data.get('discount_percent', 0))
        final_price = price - (price * discount_percent / 100)
        
        # Handle lists for color, size, tags
        color = request.form.getlist('color')
        size = request.form.getlist('size')
        tags = request.form.getlist('tags')
        
        ad = AdsProduct(
            title=data['title'],
            description=data.get('description'),
            price=price,
            discount_percent=discount_percent,
            final_price=final_price,
            sku=data['sku'],
            brand=data.get('brand'),
            color=color,
            size=size,
            material=data.get('material'),
            gender=data.get('gender'),
            stock=int(data.get('stock', 0)),
            images=images,
            tags=tags,
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
