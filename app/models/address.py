from app import db
from mongoengine import EmbeddedDocument, StringField, EmbeddedDocumentField

class AddressDetail(db.EmbeddedDocument):
    line1 = db.StringField(required=True)
    line2 = db.StringField()
    city = db.StringField(required=True)
    state = db.StringField(required=True)
    postal_code = db.StringField(required=True)
    country = db.StringField(required=True)
    type = db.StringField(choices=['Office', 'Home', 'Work', 'Store', 'Other', 'Business'], required=False)

class Address(db.Document):
    user_id = db.ReferenceField('User', required=True)
    personal_address = db.EmbeddedDocumentField(AddressDetail, required=True)
    business_address = db.EmbeddedDocumentField(AddressDetail, required=False)

    def clean(self):
        if self.business_address and not self.business_address.type:
            raise ValidationError("Business address must include a 'type' field.")
