from datetime import datetime
from decimal import Decimal
from app import db
from mongoengine import ReferenceField, StringField, DecimalField, DateTimeField

class ReferralCode(db.Document):
    user = ReferenceField('User', required=True, unique=True)
    code = StringField(required=True, unique=True, max_length=8)
    created_at = DateTimeField(default=datetime.utcnow)
    meta = {
        'collection': 'referral_codes',
        'indexes': ['user', 'code']
    }

class ReferralReward(db.Document):
    referrer = ReferenceField('User', required=True)
    referee = ReferenceField('User', required=True, unique_with='referrer')
    code_used = StringField(required=True)
    amount = DecimalField(precision=2, default=Decimal('100.00'))
    status = StringField(
        choices=['pending', 'paid', 'failed'],
        default='pending'
    )
    created_at = DateTimeField(default=datetime.utcnow)
    paid_at = DateTimeField()
    meta = {
        'collection': 'referral_rewards',
        'indexes': [
            'referrer',
            'referee',
            'status',
            {'fields': ['created_at'], 'expireAfterSeconds': 2592000}  # 30 days TTL
        ]
    }