from app.extensions import db
from datetime import datetime
from constants import ALLOWED_SIZES

class CartItem(db.EmbeddedDocument):
    product_id = db.StringField(required=True)
    variant_id = db.StringField()
    size = db.StringField(choices=ALLOWED_SIZES)
    color = db.StringField()
    quantity = db.IntField(required=True, min_value=1)
    price = db.FloatField(required=True)
    original_price = db.FloatField()
    discount = db.FloatField(default=0.0)

    def validate_stock(self, product_model):
        product = product_model.objects(id=self.product_id).first()
        if not product:
            raise ValueError(f"Product {self.product_id} not found")

        if not self.variant_id:
            available_stock = product.stock_quantity
        else:
            variant = None
            for v in product.variants:
                if str(v.id) == self.variant_id:
                    variant = v
                    break
            if not variant:
                raise ValueError(f"Variant {self.variant_id} not found")
            available_stock = variant.stock_quantity

        if self.quantity > available_stock:
            raise ValueError(f"Insufficient stock for product {self.product_id}")

class Cart(db.Document):
    user_id = db.StringField(required=True, unique=True)
    items = db.EmbeddedDocumentListField(CartItem)
    total_price = db.FloatField(default=0.0)
    currency = db.StringField(default='INR')
    created_at = db.DateTimeField(default=datetime.utcnow)
    updated_at = db.DateTimeField(default=datetime.utcnow)
    shipping_address = db.DictField()
    shipping_method = db.StringField()
    status = db.StringField(default='active')
    meta = {
        'indexes': [
            {'fields': ['user_id'], 'unique': True},
            'created_at',
        ]
    }

    def calculate_total(self):
        self.total_price = sum((item.price - item.discount) * item.quantity for item in self.items)
        return self.total_price

    def validate_cart(self, product_model):
        for item in self.items:
            item.validate_stock(product_model)

    def save(self, *args, **kwargs):
        self.calculate_total()
        return super().save(*args, **kwargs)

    def __repr__(self):
        return f'<Cart for User {self.user_id}>'