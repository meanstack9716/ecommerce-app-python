from app import db
from datetime import datetime

class Seller(db.Document):
    user_id = db.ReferenceField('User', required=True)
    businessName = db.StringField(required=True)
    businessType = db.StringField()
    businessEmail = db.StringField()
    businessMobile = db.StringField()
    address = db.ReferenceField('Address', required=True)
    businessAddress = db.ReferenceField('Address', required=False)
    gst_number = db.StringField()
    is_approved = db.StringField(choices=['pending', 'approved', 'cancelled'], default='pending')
    approved_by = db.ReferenceField('User', required=False)
    created_at = db.DateTimeField(default=datetime.utcnow)
