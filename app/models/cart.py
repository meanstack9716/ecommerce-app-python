from app.extensions import db
from datetime import datetime

class CartItem(db.EmbeddedDocument):
    product_id = db.StringField(required=True)
    quantity = db.IntField(required=True, min_value=1)
    price = db.FloatField(required=True)

class Cart(db.Document):
    user_id = db.StringField(required=True, unique=True)
    items = db.EmbeddedDocumentListField(CartItem)
    created_at = db.DateTimeField(default=datetime.utcnow)
    updated_at = db.DateTimeField(default=datetime.utcnow)

    def __repr__(self):
        return f'<Cart for User {self.user_id}>'
