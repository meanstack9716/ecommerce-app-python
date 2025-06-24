from datetime import datetime
from decimal import Decimal
import random
import string
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.jwt_handlers import jwt_error_handler
from app.models import ReferralCode, ReferralReward, User
from constants import GENERATE_REFERRAL_CODE, APPLY_REFERRAL_CODE, GET_REWARDS
from app.utils.utils import create_error_response

referral_bp = Blueprint('referral_bp', __name__)

def generate_random_code(length=8):
    """Generate random alphanumeric code"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

@referral_bp.route(GENERATE_REFERRAL_CODE, methods=['POST'])
@jwt_error_handler
@jwt_required()
def generate_referral_code():
    current_user_id = get_jwt_identity()
    
    existing_code = ReferralCode.objects(user=current_user_id).first()
    if existing_code:
        return jsonify({
            "success": True,
            "code": existing_code.code,
            "message": "You already have a referral code"
        })
    
    while True:
        code = generate_random_code()
        if not ReferralCode.objects(code=code).first():
            break
    
    new_code = ReferralCode(
        user=current_user_id,
        code=code,
        created_at=datetime.utcnow()
    )
    new_code.save()
    
    return jsonify({
        "success": True,
        "code": code,
        "message": "Referral code generated successfully"
    })

@referral_bp.route(APPLY_REFERRAL_CODE, methods=['POST'])
@jwt_error_handler
@jwt_required()
def apply_referral_code():
    data = request.get_json()
    user_id = get_jwt_identity()
    code = data.get('code')
    
    if not code:
        return create_error_response({"error": {
            "success": False,
            "message": "Referral code are required"
        }}, 400)
        
    referral_code = ReferralCode.objects(code=code).first()
    if not referral_code:
        return create_error_response({'error': {
            "success": False,
            "message": "Invalid referral code"
        }}, 404)
    
    if str(referral_code.user.id) == user_id:
        return create_error_response({'error': {
            "success": False,
            "message": "You cannot use your own referral code"
        }}, 400)
    
    if ReferralReward.objects(referee=user_id).count() > 0:
        return create_error_response({'error': {
            "success": False,
            "message": "You have already used a referral code"
        }}, 400)
    
    # Create reward record
    reward = ReferralReward(
        referrer=referral_code.user,
        referee=user_id,
        code_used=code,
        amount=Decimal('100.00'),
        status='pending',
        created_at=datetime.utcnow()
    )
    reward.save()
    
    User.objects(id=user_id).update_one(set__referred_by=referral_code.user)
    
    return jsonify({
        "success": True,
        "message": "Referral code applied successfully",
        "referrer_id": str(referral_code.user.id)
    })

@referral_bp.route('/my-code', methods=['GET'])
@jwt_required()
def get_my_referral_code():
    current_user_id = get_jwt_identity()
    
    code = ReferralCode.objects(user=current_user_id).first()
    if not code:
        return jsonify({
            "success": False,
            "message": "You don't have a referral code yet"
        }), 404
    
    return jsonify({
        "success": True,
        "code": code.code,
        "created_at": code.created_at.isoformat()
    })

@referral_bp.route(GET_REWARDS, methods=['GET'])
@jwt_required()
def get_my_rewards():
    current_user_id = get_jwt_identity()
    
    rewards = ReferralReward.objects(referrer=current_user_id).order_by('-created_at')
    
    reward_list = []
    for reward in rewards:
        referee = User.objects(id=reward.referee).first()
        reward_list.append({
            "referee": {
                "id": str(reward.referee.id),
                "name": f"{referee.first_name} {referee.last_name}",
                "email": referee.email
            },
            "amount": float(reward.amount),
            "status": reward.status,
            "date": reward.created_at.strftime("%d %b %Y"),
            "code_used": reward.code_used
        })
    
    return jsonify({
        "success": True,
        "rewards": reward_list,
        "total_rewards": len(reward_list)
    })