from app import db

class Address(db.Document):
    user_id = db.ReferenceField('User', required=True)
    line1 = db.StringField(required=True)
    line2 = db.StringField()
    city = db.StringField(required=True)
    state = db.StringField(required=True)
    postal_code = db.StringField(required=True)
    country = db.StringField(required=True)
    type = db.StringField(choices=['Office', 'Home', 'Work', 'Store', 'Other'], required=True)
