from flask import Blueprint, request, jsonify, session
from app.models.address import Address, AddressDetail
from datetime import datetime
from bson import ObjectId
from mongoengine.errors import ValidationError, DoesNotExist
from constants import ADDRESS_ADD, ADDRESS_UPDATE, ADDRESS_REMOVE, ADDRESS_LIST
from app.utils.utils import create_error_response

address_bp = Blueprint('address', __name__)

def get_user_id():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    return session['user_id']

@address_bp.route(ADDRESS_ADD, methods=['POST'])
def create_address():
    if not request.is_json:
        return create_error_response({"error": "Request must be JSON"}, 401)
    try:
        data = request.get_json()
    except Exception:
        return create_error_response({"error": "Invalid JSON data"}, 400)

    user_id = get_user_id()
    if isinstance(user_id, tuple):
        return user_id

    if 'address' not in data:
        return create_error_response({"error": "address is required"}, 400)
    if 'addressType' not in data:
        return create_error_response({"error": "addressType is required"}, 400)

    address_data = data['address']
    address_type = data['addressType']
    
    required_fields = ['line1', 'city', 'state', 'postal_code', 'country']
    for field in required_fields:
        if field not in address_data:
            return create_error_response({"error": f"{field} is required in address"}, 400)

    valid_types = ['Home', 'Office', 'Work', 'Store', 'Business', 'Other']
    if address_type not in valid_types:
        return create_error_response({"error": f"Invalid addressType. Must be one of {valid_types}"}, 400)

    try:
        # Set the address type in the address data
        address_data['type'] = address_type
        
        # Create the address detail
        address_detail = AddressDetail(**address_data)
        
        address = Address(
            user_id=user_id,
            address=address_detail,
            address_type=address_type,
            is_primary=False
        )
        
        address.save()
        
        return jsonify({
            "message": "Address created successfully",
            "address": {
                "id": str(address.id),
                "user_id": str(address.user_id.id),
                "addressType": address_type,
                "address": address_detail.to_mongo().to_dict(),
                "is_primary": address.is_primary
            }
        }), 201

    except ValidationError as e:
        return create_error_response({"error": str(e)}, 400)
    except Exception as e:
        return create_error_response({"error": str(e)}, 500)

        
@address_bp.route(ADDRESS_UPDATE, methods=['PUT'])
def update_address(address_id):
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    user_id = get_user_id()
    if isinstance(user_id, tuple):
        return user_id

    try:
        address = Address.objects.get(id=ObjectId(address_id), user_id=user_id)
    except DoesNotExist:
        return jsonify({"error": "Address not found"}), 404

    data = request.get_json()
    
    if 'addressType' not in data:
        return jsonify({"error": "addressType is required for update"}), 400
    if 'address' not in data:
        return jsonify({"error": "address is required for update"}), 400

    address_data = data['address']
    address_type = data['addressType']

    required_fields = ['line1', 'city', 'state', 'postal_code', 'country']
    for field in required_fields:
        if field not in address_data:
            return jsonify({"error": f"{field} is required in address"}), 400

    try:
        address_detail = AddressDetail(**address_data)
        
        if address_type in ['Home', 'Other']:
            address.personal_address = address_detail
            address.business_address = None
        else:
            if 'type' not in address_data:
                address_detail.type = address_type
            address.business_address = address_detail
            address.personal_address = None

        address.save()
        
        return jsonify({
            "message": "Address updated successfully",
            "address": {
                "id": str(address.id),
                "user_id": str(address.user_id.id),
                "addressType": address_type,
                "address": address_detail.to_mongo().to_dict()
            }
        }), 200

    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@address_bp.route(ADDRESS_REMOVE, methods=['DELETE'])
def delete_address(address_id):
    user_id = get_user_id()
    if isinstance(user_id, tuple):
        return user_id

    try:
        address = Address.objects.get(id=ObjectId(address_id), user_id=user_id)
        address.delete()
        return jsonify({"message": "Address deleted successfully"}), 200
    except DoesNotExist:
        return jsonify({"error": "Address not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@address_bp.route(ADDRESS_LIST, methods=['GET'])
def get_addresses():
    user_id = get_user_id()
    if isinstance(user_id, tuple):
        return user_id

    addresses = Address.objects(user_id=user_id)
    
    result = []
    for address in addresses:
        if address.personal_address:
            address_type = address.personal_address.type if address.personal_address.type else 'Home'
            address_data = address.personal_address.to_mongo().to_dict()
        else:
            address_type = address.business_address.type
            address_data = address.business_address.to_mongo().to_dict()
        
        result.append({
            "id": str(address.id),
            "user_id": str(address.user_id.id),
            "addressType": address_type,
            "address": address_data,
            "created_at": address.created_at.isoformat(),
            "updated_at": address.updated_at.isoformat()
        })

    return jsonify({"addresses": result}), 200