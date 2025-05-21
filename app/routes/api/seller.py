from flask import Blueprint, request, jsonify, current_app
from app.models import User, Role, Seller, Address, Identification
from app.utils.validation import validate_email, validate_required_fields
from app.utils.utils import generate_random_password, create_error_response
from app import db
from mongoengine import ValidationError
from app.utils.image_upload import upload_image, validate_fields
from constants import ADD_SELLER, ADDRESS_TYPES

seller_bp = Blueprint('seller', __name__, url_prefix='/user')


@seller_bp.route(ADD_SELLER, methods=['POST'])
def add_seller():
    data = request.form
    files = request.files

    required_fields = [
        'email', 'first_name', 'last_name', 'phoneNumber',
        'address[line1]', 'address[city]', 'address[state]',
        'address[country]', 'address[postal_code]',
        'businessName', 'businessType', 'businessEmail', 'businessMobile',
        'gstNumber', 'panNumber', 'addressProofIdType', 'idNumber'
    ]

    is_valid, errors = validate_required_fields(data, required_fields)
    if not is_valid:
        return create_error_response(errors, 400)

    required_files = ['panCardFront', 'addressProofFront']
    missing_files = {}
    for file_key in required_files:
        if file_key not in files or files.get(file_key).filename == '':
            missing_files[file_key] = f"The {file_key} file is required."
    if missing_files:
        return create_error_response(missing_files, 400)

    is_valid, email_error = validate_email(data.get('email'))
    if not is_valid:
        return create_error_response({"email": email_error}, 400)

    if User.objects(email=data.get('email')).first():
        return create_error_response({"email": "User with this email already exists"}, 409)

    role = Role.objects(name='user').first()
    if not role:
        return create_error_response({"message": "Default role not found"}, 500)

    with db.connection.start_session() as session:
        session.start_transaction()
        try:
            # Create user
            user = User(
                email=data.get('email'),
                first_name=data.get('first_name'),
                last_name=data.get('last_name'),
                phone_number=data.get('phoneNumber'),
                role=role,
                password=generate_random_password()
            )
            user.save(session=session)

            # Process personal address
            personal_address_type = data.get('address[type]', 'Home')
            if personal_address_type not in ADDRESS_TYPES:
                raise ValidationError(f"Invalid personal address type: {personal_address_type}")

            personal_address = Address(
                user_id=user,
                line1=data.get('address[line1]'),
                line2=data.get('address[streetLine2]', ''),
                city=data.get('address[city]'),
                state=data.get('address[state]'),
                postal_code=data.get('address[postal_code]'),
                country=data.get('address[country]'),
                type=personal_address_type,
                is_primary=True
            )
            personal_address.save(session=session)

            business_address = None
            if data.get('businessAddress[line1]'):
                business_address_type = data.get('businessAddress[type]', 'Business')
                if business_address_type not in ADDRESS_TYPES:
                    raise ValidationError(f"Invalid business address type: {business_address_type}")

                business_address = Address(
                    user_id=user,
                    line1=data.get('businessAddress[line1]'),
                    line2=data.get('businessAddress[streetLine2]', ''),
                    city=data.get('businessAddress[city]'),
                    state=data.get('businessAddress[state]'),
                    postal_code=data.get('businessAddress[postal_code]'),
                    country=data.get('businessAddress[country]'),
                    type=business_address_type,
                    is_primary=False
                )
                business_address.save(session=session)

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

            pan_card_front_url, err = upload_image(files.get('panCardFront'))
            if err:
                raise Exception(err)

            address_proof_front_url, err = upload_image(files.get('addressProofFront'))
            if err:
                raise Exception(err)

            identification = Identification(
                user_id=user,
                address_proof_id_type=data.get('addressProofIdType'),
                address_proof_front=address_proof_front_url,
                pan_number=data.get('panNumber'),
                pan_card_front=pan_card_front_url,
                id_number=data.get('idNumber')
            )
            identification.save(session=session)

            session.commit_transaction()

            return jsonify({
                "message": "Seller registered successfully. Awaiting approval.",
                "user_id": str(user.id),
                "seller_id": str(seller.id),
                "address_id": str(personal_address.id),
                "business_address_id": str(business_address.id) if business_address else None
            }), 200

        except ValidationError as e:
            session.abort_transaction()
            return create_error_response({"message": f"Validation error: {str(e)}"}, 400)
        except Exception as e:
            session.abort_transaction()
            import traceback
            traceback.print_exc()
            return create_error_response({"message": f"Internal server error: {str(e)}"}, 500)