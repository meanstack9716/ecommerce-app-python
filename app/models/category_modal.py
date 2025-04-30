from app.extensions import db
from datetime import datetime

class Category(db.Document):
    name = db.StringField(required=True, max_length=255)
    description = db.StringField()
    img_path = db.StringField()
    created_at = db.DateTimeField(default=datetime.utcnow)

    def __repr__(self):
        return f'<Category {self.name}>'

class SubCategory(db.Document):
    name = db.StringField(required=True, max_length=255)
    description = db.StringField()
    category = db.ReferenceField(Category, required=True)
    img_path = db.StringField()
    created_at = db.DateTimeField(default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SubCategory {self.name}>'

class ProductType(db.Document):
    name = db.StringField(required=True, max_length=255)
    description = db.StringField()
    category_id = db.ReferenceField(Category, required=True)
    sub_category_id = db.ReferenceField(SubCategory, required=True)
    img_path = db.StringField()
    created_at = db.DateTimeField(default=datetime.utcnow)

    def __repr__(self):
        return f'<ProductType {self.name}>'
