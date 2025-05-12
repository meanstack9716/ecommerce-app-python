from flask import Blueprint, request, jsonify, current_app
from app.models import User, Role, Seller, Address, Identification, AddressDetail
from app.utils.validation import validate_email, validate_required_fields
from app.utils.utils import generate_random_password, create_error_response
from app import db
from mongoengine import ValidationError
from app.utils.image_upload import upload_image, validate_fields
from constants import ADD_SELLER, GET_SELLER_API

seller_bp = Blueprint('seller', __name__, url_prefix='/user')

@seller_bp.route(ADD_SELLER, methods=['POST'])
def add_seller():
    data = request.form
    files = request.files

    required_fields = [
        'email', 'first_name', 'last_name', 'phoneNumber',
        'address[streetLine1]', 'address[city]', 'address[state]', 'address[country]', 'address[pincode]',
        'businessName', 'businessType', 'businessEmail', 'businessMobile',
        'gstNumber', 'businessAddress[streetLine1]', 'businessAddress[city]', 'businessAddress[state]', 'businessAddress[country]', 'businessAddress[pincode]', 'businessAddress[type]',
        'panNumber', 'addressProofIdType', 'idNumber'
    ]

    is_valid, errors = validate_required_fields(data, required_fields)
    if not is_valid:
        return create_error_response(errors)

    required_files = ['panCardFront', 'panCardBack', 'addressProofFront']
    missing_files = {}
    for file_key in required_files:
        if file_key not in files or files.get(file_key).filename == '':
            missing_files[file_key] = f"The {file_key} file is required."
    if missing_files:
        return create_error_response(missing_files)

    is_valid, email_error = validate_email(data.get('email'))
    if not is_valid:
        return create_error_response({"email": email_error}, 400)

    if User.objects(email=data.get('email')).first():
        return create_error_response({"email": "User with this email already exists"}, 409)


    role = Role.objects(name='user').first()
    if not role:
        return create_error_response("Default role not found", status_code=500)

    with db.connection.start_session() as session:
        session.start_transaction()

        try:
            # ✅ Create user
            user = User(
                email=data.get('email'),
                first_name=data.get('first_name'),
                last_name=data.get('last_name'),
                phone_number=data.get('phoneNumber'),
                role=role,
                password=generate_random_password()
            )
            user.save(session=session)

            # ✅ Create Address
            address = Address(
                user_id=user,
                personal_address=AddressDetail(
                    line1=data['address[streetLine1]'],
                    line2=data.get('address[streetLine2]', ''),
                    city=data['address[city]'],
                    state=data['address[state]'],
                    postal_code=data['address[pincode]'],
                    country=data['address[country]']
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
            address.save(session=session)

            # ✅ Create Seller
            seller = Seller(
                user_id=user,
                businessName=data.get('businessName'),
                businessType=data.get('businessType'),
                businessEmail=data.get('businessEmail'),
                businessMobile=data.get('businessMobile'),
                address=address,
                gst_number=data.get('gstNumber'),
                is_approved='pending'
            )
            seller.save(session=session)

            # ✅ Upload images (single file per key)
            pan_card_front_url, err = upload_image(files.get('panCardFront'))
            if err: raise Exception(err)
            pan_card_back_url, err = upload_image(files.get('panCardBack'))
            if err: raise Exception(err)
            address_proof_front_url, err = upload_image(files.get('addressProofFront'))
            if err: raise Exception(err)
        
            # ✅ Create Identification
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
            return create_error_response(f"Validation error: {e}")

        except Exception as e:
            session.abort_transaction()
            return create_error_response(f"Error occurred: {e}", status_code=500)

@seller_bp.route(GET_SELLER_API, methods=['GET'])
def get_sellers():
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        approval_status = request.args.get('is_approved')
        search_query = request.args.get('search', '').lower()

        query = {}
        if approval_status:
            query['is_approved'] = approval_status

        # Fetch all sellers matching query
        sellers_query = Seller.objects(**query)

        # Filter by user fields in Python (since MongoDB can't join user_id.email)
        filtered_sellers = []
        for seller in sellers_query:
            user = seller.user_id
            if user:
                if search_query:
                    if (search_query in seller.businessName.lower() or
                        search_query in user.email.lower() or
                        search_query in user.phone_number.lower()):
                        filtered_sellers.append(seller)
                else:
                    filtered_sellers.append(seller)

        # Pagination
        total = len(filtered_sellers)
        start = (page - 1) * limit
        end = start + limit
        paginated_sellers = filtered_sellers[start:end]

        seller_list = []
        for seller in paginated_sellers:
            user = seller.user_id
            address = seller.address
            seller_data = {
                'seller_id': str(seller.id),
                'businessName': seller.businessName,
                'businessType': seller.businessType,
                'businessEmail': seller.businessEmail,
                'businessMobile': seller.businessMobile,
                'gstNumber': seller.gst_number,
                'isApproved': seller.is_approved,
                'user': {
                    'user_id': str(user.id) if user else None,
                    'email': user.email if user else None,
                    'firstName': user.first_name if user else None,
                    'lastName': user.last_name if user else None,
                    'phoneNumber': user.phone_number if user else None
                },
                'address': {
                    'personalAddress': {
                        'line1': address.personal_address.line1 if address and address.personal_address else None,
                        'line2': address.personal_address.line2 if address and address.personal_address else None,
                        'city': address.personal_address.city if address and address.personal_address else None,
                        'state': address.personal_address.state if address and address.personal_address else None,
                        'postalCode': address.personal_address.postal_code if address and address.personal_address else None,
                        'country': address.personal_address.country if address and address.personal_address else None
                    },
                    'businessAddress': {
                        'line1': address.business_address.line1 if address and address.business_address else None,
                        'line2': address.business_address.line2 if address and address.business_address else None,
                        'city': address.business_address.city if address and address.business_address else None,
                        'state': address.business_address.state if address and address.business_address else None,
                        'postalCode': address.business_address.postal_code if address and address.business_address else None,
                        'country': address.business_address.country if address and address.business_address else None,
                        'type': address.business_address.type if address and address.business_address else None
                    }
                }
            }
            seller_list.append(seller_data)

        return jsonify({
            'total': total,
            'page': page,
            'limit': limit,
            'sellers': seller_list
        }), 200

    except Exception as e:
        return create_error_response(f"Error retrieving seller list: {e}", status_code=500)
