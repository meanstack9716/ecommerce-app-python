from app.extensions import db
from datetime import datetime

# Category Model
class Category(db.Document):
    name = db.StringField(required=True, max_length=255)
    description = db.StringField()
    image_path = db.StringField()
    created_at = db.DateTimeField(default=datetime.utcnow)

    def __repr__(self):
        return f'<Category {self.name}>'

# SubCategory Model (Same file)
class SubCategory(db.Document):
    name = db.StringField(required=True, max_length=255)
    description = db.StringField()
    category = db.ReferenceField(Category, required=True)
    image_path = db.StringField()
    created_at = db.DateTimeField(default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SubCategory {self.name}>'
