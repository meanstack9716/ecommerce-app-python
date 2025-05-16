from app import db
from mongoengine import EmbeddedDocument, Document, StringField, EmbeddedDocumentField, ReferenceField, BooleanField
from datetime import datetime

class AddressDetail(db.EmbeddedDocument):
    line1 = db.StringField(required=True)
    line2 = db.StringField()
    city = db.StringField(required=True)
    state = db.StringField(required=True)
    postal_code = db.StringField(required=True)
    country = db.StringField(required=True)
    type = db.StringField(choices=['Office', 'Home', 'Work', 'Store', 'Other', 'Business'], required=True)

class Address(db.Document):
    user_id = db.ReferenceField('User', required=True)
    address = db.EmbeddedDocumentField(AddressDetail, required=True)
    address_type = db.StringField(choices=['Home', 'Office', 'Work', 'Store', 'Business', 'Other'], required=True)
    is_primary = db.BooleanField(default=False)
    created_at = db.DateTimeField(default=datetime.utcnow)
    
    meta = {
        'indexes': [
            'user_id',
            'address_type',
            'is_primary'
        ]
    }

    def clean(self):
        if self.is_primary:
            existing_primary = Address.objects(
                user_id=self.user_id,
                address_type=self.address_type,
                is_primary=True
            ).first()
            
            if existing_primary and existing_primary.id != self.id:
                existing_primary.update(set__is_primary=False)