from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from flask_mail import Message
from app import bcrypt, mail
import random
from datetime import datetime, timedelta
from app.routes.auth_decorator import role_required
import cloudinary
import cloudinary.uploader
from app.models.user import User
from app.models.role import Role
from app.utils.validation import validate_email, validate_password, validate_required_fields
from app.utils.utils import create_error_response
from constants import OTP_EXPIRY_MINUTES, REGISTER, LOGIN, FORGOT_PASSWORD, VERIFY_OTP, RESET_PASSWORD, LOGOUT

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route(REGISTER, methods=['POST'])
def register():
    data = request.get_json()

    is_valid, errors = validate_required_fields(data, ['email', 'password', 'password_confirmation'])
    if not is_valid:
        return create_error_response(errors, 400)

    is_valid_email, email_error = validate_email(data.get('email', ''))
    if not is_valid_email:
        return create_error_response({"email": email_error}, 400)

    is_valid_password, password_error = validate_password(data.get('password', ''))
    if not is_valid_password:
        return create_error_response({"password": password_error}, 400)

    if data.get('password') != data.get('password_confirmation'):
        return create_error_response({"password_confirmation": "Password and confirmation do not match."}, 400)

    if User.objects(email=data.get('email')).first():
        return create_error_response({"email": "Email already exists"}, 409)

    role_name = data.get('role', 'user')
    role = Role.objects(name=role_name).first()

    if not role:
        return create_error_response({"role": "Invalid role"}, 400)

    user = User(
        email=data.get('email'),
        password=data.get('password'),
        role=role
    )
    user.hash_password()
    user.save()

    access_token = create_access_token(identity=str(user.id), additional_claims={'role': role_name})

    user_data = {
        'id': str(user.id),
        'email': user.email,
        'role': {
            'id': str(role.id),
            'name': role.name
        }
    }

    return jsonify({
        'message': 'User registered successfully',
        'user': user_data,
        'access_token': access_token
    }), 200


# Login API
from flask import session

@auth_bp.route(LOGIN, methods=['POST'])
def login():
    data = request.get_json()

    is_valid, errors = validate_required_fields(data, ['email', 'password'])
    if not is_valid:
        return create_error_response(errors, 400)

    is_valid_email, email_error = validate_email(data.get('email'))
    if not is_valid_email:
        return create_error_response({"email": email_error}, 400)

    user = User.objects(email=data.get('email')).first()

    if not user:
        return create_error_response({"email": "User with this email does not exist"}, 404)

    if not user.check_password(data.get('password')):
        return create_error_response({"password": "Invalid password"}, 401)

    access_token = create_access_token(identity=str(user.id), additional_claims={'role': user.role.name})

    session['user_id'] = str(user.id)
    session['user_role'] = user.role.name

    return jsonify({
        'message': 'Login successful',
        'access_token': access_token
    }), 200



# Forgot Password API (Send OTP)
@auth_bp.route(FORGOT_PASSWORD, methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'message': 'Email is required'}), 400

    user = User.objects(email=email).first()
    if not user:
        return jsonify({'errors': 'No account associated with this email address'}), 400

    otp = ''.join(random.choices('0123456789', k=6))
    expiry_time = datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)

    user.reset_otp = otp
    user.otp_expiry = expiry_time
    user.save()

    msg = Message(
        subject='Your OTP for Password Reset',
        recipients=[user.email],
        body=f"Your OTP is {otp}. It will expire in 10 minutes."
    )

    try:
        mail.send(msg)
        print(f"OTP email sent successfully to: {user.email}")
        return jsonify({'message': 'OTP sent successfully'}), 200
    except Exception as e:
        print(f"Error sending email: {e}")
        return jsonify({'message': 'Failed to send OTP email'}), 500

# Verify OTP API
@auth_bp.route(VERIFY_OTP, methods=['POST'])
def verify_email_code():
    data = request.get_json()
    email = data.get('email')
    otp = data.get('code')

    if not email or not otp:
        return jsonify({'errors': 'Email and OTP are required'}), 400

    user = User.objects(email=email).first()
    if not user:
        return jsonify({'errors': 'Invalid email or OTP'}), 400

    if not user.reset_otp or not user.otp_expiry:
        return jsonify({'errors': 'No OTP requested for this email'}), 400

    current_time = datetime.utcnow()
    if user.reset_otp != otp:
        return jsonify({'message': 'Invalid OTP'}), 400
    if current_time > user.otp_expiry:
        return jsonify({'message': 'OTP has expired'}), 400

    user.save()

    return jsonify({'message': 'OTP verified successfully'}), 200

# Reset Password API
@auth_bp.route(RESET_PASSWORD, methods=['POST'])
def reset_password():
    data = request.get_json()
    email = data.get('email')
    otp = data.get('code')
    new_password = data.get('password')

    if not email or not otp or not new_password:
        return jsonify({'errors': 'Email, OTP, and new password are required'}), 400

    user = User.objects(email=email).first()
    if not user:
        return jsonify({'message': 'User not found'}), 404

    if user.reset_otp != otp:
        return jsonify({'message': 'Invalid OTP'}), 400

    if user.otp_expiry and user.otp_expiry < datetime.utcnow():
        return jsonify({'message': 'OTP has expired'}), 400

    user.password = new_password
    user.hash_password()
    user.reset_otp = None
    user.otp_expiry = None
    user.save()

    return jsonify({'message': 'Password reset successfully'}), 200

@auth_bp.route(LOGOUT, methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logout successful'}), 200


