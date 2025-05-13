from app.extensions import db
from datetime import datetime
from constants import ALLOWED_SIZES

class WishlistItem(db.EmbeddedDocument):
    product_id = db.StringField(required=True)
    variant_id = db.StringField()
    size = db.StringField(choices=ALLOWED_SIZES)
    added_at = db.DateTimeField(default=datetime.utcnow)

    def validate_product(self, product_model):
        product = product_model.objects(id=self.product_id).first()
        if not product:
            raise ValueError(f"Product {self.product_id} not found")
        if self.variant_id:
            variant = None
            for v in product.variants:
                if str(v.id) == self.variant_id:
                    variant = v
                    break
            if not variant:
                raise ValueError(f"Variant {self.variant_id} not found")

    def __repr__(self):
        return f"<WishlistItem {self.product_id}>"

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