from flask import Blueprint, request, jsonify
from app.models import AdsProduct, Category, SubCategory, ProductType

ads_product_bp = Blueprint('ads_product_bp', __name__)

@ads_product_bp.route('/api/ads', methods=['POST'])
def create_ad():
    try:
        data = request.json

        required_fields = ['title', 'price', 'category_id', 'sub_category_id', 'product_type_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400

        category = Category.objects(id=data['category_id']).first()
        sub_category = SubCategory.objects(id=data['sub_category_id']).first()
        product_type = ProductType.objects(id=data['product_type_id']).first()

        if not category or not sub_category or not product_type:
            return jsonify({'error': 'Invalid category, sub-category or product type ID'}), 400

        ad = AdsProduct(
            title=data['title'],
            description=data.get('description'),
            price=data['price'],
            images=data.get('images', []),
            category_id=category,
            sub_category_id=sub_category,
            product_type_id=product_type,
            location=data.get('location'),
            contact_info=data.get('contact_info')
        )
        ad.save()

        return jsonify({'message': 'Ad created successfully', 'id': str(ad.id)}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500
