from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, Role, Seller, Address, Identification, AddressDetail
import cloudinary.uploader
from constants import GET_USER_PROFILE, UPDATE_PROFILE, UPDATE_PROFILE_PIC, DELETE_PROFILE_PIC, ADD_SELLER
from app.utils.validation import validate_email, validate_password, validate_required_fields
from app.utils.utils import generate_random_password
from app import db
from mongoengine import ValidationError
from werkzeug.utils import secure_filename
import os


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

@user_bp.route(ADD_SELLER, methods=['POST'])
def add_seller():
    # Get form data
    data = request.form  # This will contain the text form fields
    files = request.files  # This will contain the files uploaded
    
    required_fields = [
        'email', 'first_name', 'last_name', 'phoneNumber',
        'address[streetLine1]', 'address[city]', 'address[state]', 'address[country]', 'address[pincode]',
        'businessName', 'businessType', 'businessEmail', 'businessMobile',
        'gstNumber', 'businessAddress[streetLine1]', 'businessAddress[city]', 'businessAddress[state]', 'businessAddress[country]', 'businessAddress[pincode]', 'businessAddress[type]',
        'panNumber', 'panCardFront', 'panCardBack',
        'addressProofIdType', 'idNumber', 'addressProofFront', 'addressProofBack'
    ]
    
    # Validate required fields
    is_valid, errors = validate_required_fields(data, required_fields)
    if not is_valid:
        return jsonify({"errors": errors}), 400

    # Validate email format
    is_valid, email_error = validate_email(data.get('email'))
    if not is_valid:
        return jsonify({"error": email_error}), 400

    if User.objects(email=data.get('email')).first():
        return jsonify({"error": "User with this email already exists"}), 400

    default_role = Role.objects(name='user').first()
    if not default_role:
        return jsonify({"error": "Default role not found"}), 500

    with db.connection.start_session() as session:
        session.start_transaction()

        try:
            # Create User
            user = User(
                email=data.get('email'),
                first_name=data.get('first_name'),
                last_name=data.get('last_name'),
                phone_number=data.get('phoneNumber'),
                role=default_role,
                password=generate_random_password()
            )
            user.save(session=session)

            # Create Personal Address
            personal_address = Address(
                user_id=user,
                personal_address=AddressDetail(
                    line1=data['address[streetLine1]'],
                    line2=data.get('address[streetLine2]', ''),
                    city=data['address[city]'],
                    state=data['address[state]'],
                    postal_code=data['address[pincode]'],
                    country=data['address[country]'],
                ),
                business_address=AddressDetail(
                    line1=data['businessAddress[streetLine1]'],
                    line2=data.get('businessAddress[streetLine2]', ''),
                    city=data['businessAddress[city]'],
                    state=data['businessAddress[state]'],
                    postal_code=data['businessAddress[pincode]'],
                    country=data['businessAddress[country]'],
                    type=data['businessAddress[type]']
                )
            )

            personal_address.save(session=session)

            # Create Seller
            seller = Seller(
                user_id=user,
                businessName=data.get('businessName'),
                businessType=data.get('businessType'),
                businessEmail=data.get('businessEmail'),
                businessMobile=data.get('businessMobile'),
                address=personal_address,
                gst_number=data.get('gstNumber'),
                is_approved='pending'
            )
            seller.save(session=session)

            # Handle File Uploads
            pan_card_front_url = save_file(files.get('panCardFront'))  # Replace with your actual file upload function
            pan_card_back_url = save_file(files.get('panCardBack'))
            address_proof_front_url = save_file(files.get('addressProofFront'))
            address_proof_back_url = save_file(files.get('addressProofBack'))

            # Identification
            identification = Identification(
                user_id=user,
                address_proof_id_type=data.get('addressProofIdType'),
                address_proof_front=address_proof_front_url,
                address_proof_back=address_proof_back_url,
                pan_number=data.get('panNumber'),
                pan_card_front=pan_card_front_url,
                pan_card_back=pan_card_back_url
            )
            identification.save(session=session)

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


def save_file(file, folder_path='uploads/images'):
    # Check if the folder exists, if not create it
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    # Secure the filename to avoid issues with special characters
    filename = secure_filename(file.filename)
    
    # Define the full file path
    file_path = os.path.join(folder_path, filename)
    
    # Save the file to the defined folder
    file.save(file_path)
    
    # Return the file path (or a URL if you upload it to cloud storage)
    return file_path