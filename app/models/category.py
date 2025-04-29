from app.extensions import db
from datetime import datetime

class Category(db.Document):
    title = db.StringField(required=True, max_length=255)
    description = db.StringField()
    image_path = db.StringField()
    created_at = db.DateTimeField(default=datetime.utcnow)

    def __repr__(self):
        return f'<Category {self.title}>'