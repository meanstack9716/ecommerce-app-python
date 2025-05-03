from app.extensions import db
from datetime import datetime
from app.models import Category, SubCategory, SubSubCategory
from app.models.brands import ProductBrands
from constants import ALLOWED_SIZES, ALLOWED_GENDERS

class AddProducts(db.Document):
    title = db.StringField(required=True, max_length=255)
    description = db.StringField()
    price = db.FloatField(required=True)
    discount_percent = db.FloatField(default=0)
    final_price = db.FloatField()
    
    sku = db.StringField(unique=True, required=True)
    brand_id = db.ReferenceField(ProductBrands)
    color = db.ListField(db.StringField())
    size = db.ListField(db.StringField(choices=ALLOWED_SIZES))
    material = db.StringField()
    gender = db.StringField(choices=ALLOWED_GENDERS)
    
    stock = db.IntField(default=0)
    images = db.ListField(db.StringField())
    tags = db.ListField(db.StringField())
    
    category_id = db.ReferenceField(Category, required=True)
    sub_category_id = db.ReferenceField(SubCategory, required=True)
    product_type_id = db.ReferenceField(SubSubCategory, required=True)
    
    rating = db.FloatField(default=0)
    num_reviews = db.IntField(default=0)
    
    is_active = db.BooleanField(default=True)
    created_at = db.DateTimeField(default=datetime.utcnow)
    updated_at = db.DateTimeField(default=datetime.utcnow)

    def __repr__(self):
        return f'<AddProducts {self.title}>'
