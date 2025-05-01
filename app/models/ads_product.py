from app.extensions import db
from datetime import datetime
from app.models import Category, SubCategory, ProductType

class AdsProduct(db.Document):
    title = db.StringField(required=True, max_length=255)
    description = db.StringField()
    price = db.FloatField(required=True)
    discount_percent = db.FloatField(default=0)
    final_price = db.FloatField()
    
    sku = db.StringField(unique=True, required=True)
    brand = db.StringField()
    color = db.ListField(db.StringField())
    size = db.ListField(db.StringField())
    material = db.StringField()
    gender = db.StringField(choices=['Men', 'Women', 'Unisex', 'Kids'])
    
    stock = db.IntField(default=0)
    images = db.ListField(db.StringField())
    tags = db.ListField(db.StringField())
    
    category_id = db.ReferenceField(Category, required=True)
    sub_category_id = db.ReferenceField(SubCategory, required=True)
    product_type_id = db.ReferenceField(ProductType, required=True)
    
    rating = db.FloatField(default=0)
    num_reviews = db.IntField(default=0)
    
    is_active = db.BooleanField(default=True)
    created_at = db.DateTimeField(default=datetime.utcnow)
    updated_at = db.DateTimeField(default=datetime.utcnow)

    def __repr__(self):
        return f'<AdsProduct {self.title}>'
