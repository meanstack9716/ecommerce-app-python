from app.extensions import db
from datetime import datetime
from app.models import Category
from app.models import SubCategory
from app.models import ProductType

class AdsProduct(db.Document):
    title = db.StringField(required=True, max_length=255)
    description = db.StringField()
    price = db.FloatField(required=True)
    images = db.ListField(db.StringField())

    category_id = db.ReferenceField(Category, required=True)
    sub_category_id = db.ReferenceField(SubCategory, required=True)
    product_type_id = db.ReferenceField(ProductType, required=True)

    location = db.StringField()
    contact_info = db.StringField()  # email or phone
    is_active = db.BooleanField(default=True)
    created_at = db.DateTimeField(default=datetime.utcnow)

    def __repr__(self):
        return f'<AdsProduct {self.title}>'
