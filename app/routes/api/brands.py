from flask import Blueprint, request, jsonify, session
from app.models import ProductBrands
from constants import GET_BRANDS_API, ADD_BRAND_API, UPDATE_BRAND_API
from app.utils.utils import create_error_response
from app.utils.image_upload import upload_image
from app.utils.validation import validate_required_fields

from datetime import datetime

brand_bp = Blueprint('brand_bp', __name__)

@brand_bp.route(GET_BRANDS_API, methods=['GET'])
def get_brands():
    try:
        brands = ProductBrands.objects()
        data = [
            {"id": str(brand.id), "name": brand.name, "logo_path": brand.logo_path}
            for brand in brands
        ]
        return jsonify({"data": data}), 200
    except Exception as e:
        return create_error_response(str(e), 500)

@brand_bp.route(ADD_BRAND_API, methods=['POST'])
def add_new_brand():
    if 'user_id' not in session:
        return create_error_response('Unauthorized', 401)

    name = request.form.get('name')
    description = request.form.get('description')
    logo = request.files.get('logo')

    is_valid, validation_errors = validate_required_fields({'name': name, 'description': description}, ['name', 'description'])
    if not is_valid:
        return create_error_response(validation_errors, 400)

    if not name:
        return create_error_response('Brand name is required', 400)
    
    if not description:
        return create_error_response('Description is required', 400)

    logo_path, logo_error = upload_image(logo)
    if logo_error:
        return create_error_response(logo_error, 400)

    existing = ProductBrands.objects(name__iexact=name).first()
    if existing:
        return create_error_response('Brand already exists', 409)

    brand = ProductBrands(name=name, description=description, logo_path=logo_path)
    brand.save()

    return jsonify({"message": "Brand created successfully", "id": str(brand.id), "logo_path": brand.logo_path, "description": brand.description}), 200


@brand_bp.route(UPDATE_BRAND_API, methods=['POST'])
def update_brand():
    brand_id = request.args.get('brandId')
    if not brand_id:
        return create_error_response('Brand ID is required', 400)

    name = request.form.get('name')
    description = request.form.get('description')
    logo = request.files.get('logo')

    is_valid, validation_errors = validate_required_fields({'name': name, 'description': description}, ['name', 'description'])
    if not is_valid:
        return create_error_response(validation_errors, 400)

    brand = ProductBrands.objects(id=brand_id).first()
    if not brand:
        return create_error_response('Brand not found', 404)

    if logo:
        logo_path, logo_error = upload_image(logo)
        if logo_error:
            return create_error_response(logo_error, 400)
        brand.logo_path = logo_path

    existing = ProductBrands.objects(name__iexact=name).first()
    if existing and str(existing.id) != brand_id:
        return create_error_response('Another brand with the same name already exists', 409)

    brand.name = name
    brand.description = description
    brand.updated_at = datetime.utcnow()
    brand.save()

    return jsonify({"message": "Brand updated successfully", "id": str(brand.id), "logo_path": brand.logo_path}), 200
