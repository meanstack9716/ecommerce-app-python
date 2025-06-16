from app.extensions import db
from datetime import datetime
from constants import ALLOWED_SIZES

class WishlistItem(db.EmbeddedDocument):
    product_id = db.StringField(required=True)
    size = db.StringField(choices=ALLOWED_SIZES)
    color = db.StringField()
    color_hexa_code = db.StringField()
    quantity = db.IntField(default=1)
    added_at = db.DateTimeField(default=datetime.utcnow)

    def validate_product(self, product_model):
        product = product_model.objects(id=self.product_id).first()
        if not product:
            raise ValueError(f"Product {self.product_id} not found")
        
        if hasattr(product, 'variants'):
            variant_exists = any(
                v for v in product.variants 
                if v.size == self.size and v.color == self.color
            )
            if not variant_exists:
                raise ValueError(f"Variant with size {self.size} and color {self.color} not found")

class Wishlist(db.Document):
    user_id = db.StringField(required=True, unique=True)
    items = db.EmbeddedDocumentListField(WishlistItem)
    created_at = db.DateTimeField(default=datetime.utcnow)
    updated_at = db.DateTimeField(default=datetime.utcnow)

    meta = {
        'indexes': [
            {'fields': ['user_id'], 'unique': True},
            'created_at',
        ]
    }

    def validate_wishlist(self, product_model):
        for item in self.items:
            item.validate_product(product_model)

    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)

    def __repr__(self):
        return f"<Wishlist for User {self.user_id}>"