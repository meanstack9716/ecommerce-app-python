from flask import Blueprint, request, jsonify, session
from app.models.address import Address
from datetime import datetime
from bson import ObjectId
from mongoengine.errors import ValidationError, DoesNotExist
from constants import ADDRESS_ADD, ADDRESS_UPDATE, ADDRESS_REMOVE, ADDRESS_LIST, ADDRESS_TYPES, ADDRESS_TYPES_API
from app.utils.utils import create_error_response

address_bp = Blueprint('address', __name__)

def get_user_id():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    return session['user_id']

@address_bp.route(ADDRESS_ADD, methods=['POST'])
def create_address():
    if not request.is_json:
        return create_error_response({"error": "Request must be JSON"}, 400)

    try:
        data = request.get_json()
    except Exception:
        return create_error_response({"error": "Invalid JSON data"}, 400)

    user_id = get_user_id()
    if isinstance(user_id, tuple):
        return user_id

    required_fields = ['line1', 'city', 'state', 'postal_code', 'country', 'addressType']
    for field in required_fields:
        if field not in data:
            return create_error_response({"error": f"{field} is required"}, 400)

    address_type = data['addressType']
    valid_types = ADDRESS_TYPES
    if address_type not in valid_types:
        return create_error_response({"error": f"Invalid addressType. Must be one of {valid_types}"}, 400)

    try:
        address = Address(
            user_id=user_id,
            line1=data['line1'],
            line2=data.get('line2', ''),
            city=data['city'],
            state=data['state'],
            postal_code=data['postal_code'],
            country=data['country'],
            contact_name=data.get('contact_name'),
            contact_number=data.get('contact_number'),
            address_type=address_type,
            is_primary=data.get('is_primary', False)
        )

        address.save()

        return jsonify({
            "message": "Address created successfully",
            "data": {
                "id": str(address.id),
                "user_id": str(address.user_id.id),
                "type": address.address_type,
                "line1": address.line1,
                "line2": address.line2,
                "city": address.city,
                "state": address.state,
                "postal_code": address.postal_code,
                "country": address.country,
                "contact_name": address.contact_name,
                "contact_number": address.contact_number,
                "is_primary": address.is_primary,
                "created_at": address.created_at.isoformat() if address.created_at else None
            }
        }), 201

    except ValidationError as e:
        return create_error_response({"error": str(e)}, 400)
    except Exception as e:
        return create_error_response({"error": "Internal server error"}, 500)


@address_bp.route(ADDRESS_UPDATE, methods=['PUT'])
def update_address():
    if not request.is_json:
        return create_error_response({"error": "Request must be JSON"}, 400)

    try:
        data = request.get_json()
    except Exception:
        return create_error_response({"error": "Invalid JSON data"}, 400)

    address_id = data.get('address_id')
    if not address_id:
        return create_error_response({"error": "address_id is required"}, 400)

    user_id = get_user_id()
    if isinstance(user_id, tuple):
        return user_id

    try:
        address = Address.objects.get(id=ObjectId(address_id), user_id=user_id)
    except DoesNotExist:
        return create_error_response({"error": "Address not found"}, 404)
    except Exception:
        return create_error_response({"error": "Invalid address ID"}, 400)

    required_fields = ['line1', 'city', 'state', 'postal_code', 'country', 'type']
    for field in required_fields:
        if field not in data:
            return create_error_response({"error": f"{field} is required"}, 400)

    valid_types = ADDRESS_TYPES
    if data['type'] not in valid_types:
        return create_error_response({"error": f"Invalid addressType. Must be one of {valid_types}"}, 400)

    try:
        address.line1 = data['line1']
        address.line2 = data.get('line2', address.line2)
        address.city = data['city']
        address.state = data['state']
        address.postal_code = data['postal_code']
        address.country = data['country']
        address.address_type = data['type']
        address.is_primary = data.get('is_primary', address.is_primary)
        
        # Optional fields
        if 'contact_name' in data:
            address.contact_name = data['contact_name']
        if 'contact_number' in data:
            address.contact_number = data['contact_number']

        address.save()

        return jsonify({
            "message": "Address updated successfully",
            "data": {
                "id": str(address.id),
                "user_id": str(address.user_id.id),
                "type": address.address_type,
                "is_primary": address.is_primary,
                "line1": address.line1,
                "line2": address.line2,
                "city": address.city,
                "state": address.state,
                "postal_code": address.postal_code,
                "country": address.country,
                "contact_name": address.contact_name,
                "contact_number": address.contact_number,
                "created_at": address.created_at.isoformat() if address.created_at else None,
                "updated_at": datetime.utcnow().isoformat()
            }
        }), 200
    except ValidationError as e:
        return create_error_response({"error": str(e)}, 400)
    except Exception as e:
        return create_error_response({"error": "Internal server error"}, 500)



@address_bp.route(ADDRESS_REMOVE, methods=['DELETE'])
def delete_address(address_id):
    payload = {}
    if request.is_json:
        try:
            payload = request.get_json()
        except Exception as e:
            return create_error_response({"error": "Invalid JSON payload"}, 400)

    if not address_id or not ObjectId.is_valid(address_id):
        return create_error_response({"error": "Invalid address ID format"}, 400)

    user_id = get_user_id()
    if isinstance(user_id, tuple):
        return user_id

    try:
        address = Address.objects.get(id=ObjectId(address_id), user_id=user_id)

        if payload.get("force") != True and address.is_primary:
            return create_error_response(
                {"error": "Cannot delete primary address. Use 'force': true to override."},
                400
            )

        address.delete()

        return jsonify({
            "message": "Address deleted successfully",
            "data": {
                "deleted_id": address_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        }), 200

    except DoesNotExist:
        return create_error_response({"error": "Address not found or not owned by user"}, 404)
    except Exception as e:
        return create_error_response({"error": "Internal server error"}, 500)

@address_bp.route(ADDRESS_LIST, methods=['GET'])
def get_addresses():
    user_id = get_user_id()
    if isinstance(user_id, tuple):
        return user_id

    try:
        addresses = Address.objects(user_id=user_id).order_by('-created_at')

        result = []
        for address in addresses:
            result.append({
                "id": str(address.id),
                "user_id": str(address.user_id.id),
                "contact_name": address.contact_name,
                "contact_number": address.contact_number,
                "type": address.address_type,
                "line1": address.line1,
                "line2": address.line2,
                "city": address.city,
                "state": address.state,
                "postal_code": address.postal_code,
                "country": address.country,
                "is_primary": address.is_primary,
                "created_at": address.created_at.isoformat() if address.created_at else None,
            })

        return jsonify({
            "message": "Addresses retrieved successfully",
            "count": len(result),
            "data": result
        }), 200

    except Exception as e:
        return create_error_response({"error": "Internal server error"}, 500)


@address_bp.route(ADDRESS_TYPES_API, methods=['GET'])
def get_addresses_types():
    user_id = get_user_id()
    if isinstance(user_id, tuple):
        return user_id

    try:
        address_types = ADDRESS_TYPES
        return jsonify({
            "message": "Address types retrieved successfully",
            "data": address_types
        }), 200

    except Exception as e:
        return create_error_response({"error": "Internal server error"}, 500)
