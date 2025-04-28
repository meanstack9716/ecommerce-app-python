from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, Role, Seller, Address
import cloudinary.uploader
from constants import GET_USER_PROFILE, UPDATE_PROFILE, UPDATE_PROFILE_PIC, DELETE_PROFILE_PIC, ADD_SELLER
from app.utils.validation import validate_email, validate_password, validate_required_fields


user_bp = Blueprint('user', __name__, url_prefix='/user')

# Get user profile
@user_bp.route(GET_USER_PROFILE, methods=['GET'])
@jwt_required()
def get_user_profile():
    user_id = get_jwt_identity()
    user = User.objects(id=user_id).first()

    if not user:
        return jsonify({'message': 'User not found'}), 404

    profile = {
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "mobile": user.phone_number,
        "profile_pic": user.profile_pic,
        "id": str(user.id),
        "role": {
            "name": user.role.name if user.role else None,
            "id": str(user.role.id) if user.role else None
        }
    }

    return jsonify({"data": profile}), 200


# Update user profile
@user_bp.route(UPDATE_PROFILE, methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    user = User.objects(id=user_id).first()

    if not user:
        return jsonify({'message': 'User not found'}), 404

    data = request.get_json()
    user.first_name = data.get('first_name', user.first_name)
    user.last_name = data.get('last_name', user.last_name)
    user.phone_number = data.get('mobile', user.phone_number)
    user.gender = data.get('gender', user.gender)
    user.save()

    return jsonify({'message': 'Profile updated successfully'}), 200

# Update profile picture
@user_bp.route(UPDATE_PROFILE_PIC, methods=['POST'])
@jwt_required()
def update_profile_picture():
    user_id = get_jwt_identity()
    user = User.objects(id=user_id).first()
    
    if not user:
        return {"message": "User not found"}, 404

    if 'image' not in request.files:
        return {"message": "No file part"}, 400

    file = request.files['image']
    if file.filename == '':
        return {"message": "No selected file"}, 400

    try:
        if user.cloudinary_id:
            cloudinary.uploader.destroy(user.cloudinary_id)

        upload_result = cloudinary.uploader.upload(file.stream)
        user.profile_pic = upload_result['secure_url']
        user.cloudinary_id = upload_result['public_id']
        user.save()

        return {
            "message": "Profile picture updated",
            "profile_pic": user.profile_pic
        }, 200

    except Exception as e:
        return {"message": "Upload failed", "error": str(e)}, 500

# Delete profile picture
@user_bp.route(DELETE_PROFILE_PIC, methods=['DELETE'])
@jwt_required()
def delete_profile_picture():
    user_id = get_jwt_identity()
    user = User.objects(id=user_id).first()

    if not user:
        return jsonify({'message': 'User not found'}), 404

    if not user.cloudinary_id:
        return jsonify({'message': 'No profile picture found'}), 404

    try:
        cloudinary.uploader.destroy(user.cloudinary_id)
        user.profile_picture = None
        user.cloudinary_id = None
        user.save()

        return jsonify({'message': 'Profile picture deleted successfully'}), 200

    except Exception as e:
        return jsonify({'message': 'Deletion failed', 'error': str(e)}), 500

# Add seller api
from app import db
from mongoengine import ValidationError
from flask import jsonify

@user_bp.route(ADD_SELLER, methods=['POST'])
def add_seller():
    data = request.get_json()

    required_fields = ['email', 'password', 'first_name', 'last_name', 'phone_number', 'store_name', 'line1', 'city', 'state', 'country', 'pincode', 'gst_number', 'address_type']
    is_valid, errors = validate_required_fields(data, required_fields)
    if not is_valid:
        return jsonify({"errors": errors}), 400

    is_valid, email_error = validate_email(data.get('email'))
    if not is_valid:
        return jsonify({"error": email_error}), 400

    is_valid, password_error = validate_password(data.get('password'))
    if not is_valid:
        return jsonify({"error": password_error}), 400

    if User.objects(email=data.get('email')).first():
        return jsonify({"error": "User with this email already exists"}), 400

    default_role = Role.objects(name='user').first()
    if not default_role:
        return jsonify({"error": "Default role not found"}), 500

    with db.connection.start_session() as session:
        session.start_transaction()

        try:
            user = User(
                email=data.get('email'),
                password=data.get('password'),
                first_name=data.get('first_name'),
                last_name=data.get('last_name'),
                phone_number=data.get('phone_number'),
                role=default_role
            )
            user.hash_password()
            user.save(session=session)

            address = Address(
                user_id=user,
                line1=data.get('line1'),
                line2=data.get('line2'),
                city=data.get('city'),
                state=data.get('state'),
                postal_code=data.get('pincode'),
                country=data.get('country'),
                type=data.get('address_type')
            )
            address.save(session=session)

            seller = Seller(
                user_id=user,
                store_name=data.get('store_name'),
                store_logo=data.get('store_logo'),
                address=address,
                gst_number=data.get('gst_number'),
                is_approved='pending'
            )
            seller.save(session=session)

            session.commit_transaction()

            return jsonify({
                "message": "Seller registered successfully. Awaiting approval.",
                "user_id": str(user.id),
                "seller_id": str(seller.id)
            }), 200

        except ValidationError as e:
            session.abort_transaction()
            return jsonify({"error": "Validation error: " + str(e)}), 400

        except Exception as e:
            session.abort_transaction()
            return jsonify({"error": "Error occurred: " + str(e)}), 500
