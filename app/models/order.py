from app.extensions import db
from datetime import datetime
from mongoengine import EmbeddedDocument, EmbeddedDocumentField

class OrderItem(EmbeddedDocument):
    product_id = db.ReferenceField('Products', required=True)
    variant_id = db.ReferenceField('ProductVariant')
    quantity = db.IntField(required=True, min_value=1)
    price = db.DecimalField(required=True, precision=2)
    discount_price = db.DecimalField(precision=2)
    total_price = db.DecimalField(required=True, precision=2)

class Order(db.Document):
    user_id = db.ReferenceField('User', required=True)
    items = db.ListField(EmbeddedDocumentField(OrderItem), required=True)
    total_price = db.DecimalField(required=True, precision=2)
    currency = db.StringField(default='USD', max_length=3)
    shipping_address = db.DictField(required=True)
    billing_address = db.DictField()
    shipping_method = db.StringField(required=True)
    payment_method = db.StringField(required=True)
    payment_status = db.StringField(choices=['pending', 'paid', 'failed', 'refunded'], default='pending')
    status = db.StringField(choices=['pending', 'processing', 'shipped', 'delivered', 'cancelled'], default='pending')
    tracking_number = db.StringField()
    notes = db.StringField()
    created_at = db.DateTimeField(default=datetime.utcnow)
    updated_at = db.DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'orders',
        'indexes': [
            'user_id',
            'status',
            'payment_status',
            'created_at'
        ]
    }

    def update_status(self, new_status):
        if new_status not in ['pending', 'processing', 'shipped', 'delivered', 'cancelled']:
            raise ValueError("Invalid status")
        self.status = new_status
        self.updated_at = datetime.utcnow()
        self.save()

    def update_payment_status(self, new_status):
        if new_status not in ['pending', 'paid', 'failed', 'refunded']:
            raise ValueError("Invalid payment status")
        self.payment_status = new_status
        self.updated_at = datetime.utcnow()
        self.save()