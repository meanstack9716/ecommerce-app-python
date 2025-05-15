from app.extensions import db
from datetime import datetime
from mongoengine import EmbeddedDocument, EmbeddedDocumentField

class OrderItem(EmbeddedDocument):
    product_id = db.ReferenceField('Products', required=True)
    selected_size = db.StringField()
    selected_color = db.StringField()
    selected_color_name = db.StringField()
    quantity = db.IntField(required=True, min_value=1)
    price = db.DecimalField(required=True, precision=2)
    discount_percent = db.DecimalField(precision=2)
    final_price = db.IntField(required=True, min_value=1)

class Order(db.Document):
    user_id = db.ReferenceField('User', required=True)
    seller_id = db.ReferenceField('Seller')
    order_number = db.StringField(required=True, unique=True)
    items = db.ListField(EmbeddedDocumentField(OrderItem), required=True)
    total_amount = db.DecimalField(required=True, precision=2)
    status = db.StringField(choices=[
        'pending', 'confirmed' ,'processing', 'shipped', 'outOfDelivery', 'delivered', 'cancelled', 'return', 'refund'
    ], default='pending')
    shipping_address = db.DictField(required=True)
    payment_method = db.StringField(required=True)
    payment_status = db.StringField(
        choices=['pending', 'paid', 'failed', 'refunded'],
        default='pending'
    )
    created_at = db.DateTimeField(default=datetime.utcnow)
    updated_at = db.DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'orders',
        'indexes': [
            'user_id',
            'seller_id',
            'order_number',
            'status',
            'payment_status',
            'created_at'
        ]
    }

    def update_status(self, new_status):
        if new_status not in ['pending', 'confirmed' ,'processing', 'shipped', 'outOfDelivery', 'delivered', 'cancelled', 'return', 'refund']:
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