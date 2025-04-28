import os
from app import db
from flask_bcrypt import generate_password_hash, check_password_hash
from datetime import datetime
from constants import GENDER_CHOICES, ROLE_ADMIN
from app.models.role import Role

class User(db.Document):
    email = db.StringField(required=True, unique=True)
    password = db.StringField(required=True, min_length=6)
    first_name = db.StringField()
    last_name = db.StringField()
    phone_number = db.StringField()
    gender = db.StringField(choices=["male", "female", "other"])
    role = db.ReferenceField('Role', required=True)
    created_at = db.DateTimeField(default=datetime.utcnow)
    reset_token = db.StringField()
    reset_otp = db.StringField()
    otp_expiry = db.DateTimeField()
    profile_pic = db.StringField()
    cloudinary_id = db.StringField()
    is_admin = db.BooleanField(default=False)

    def hash_password(self):
        self.password = generate_password_hash(self.password).decode('utf8')

    def check_password(self, password):
        return check_password_hash(self.password, password)

    @staticmethod
    def create_default_admin():
        role = Role.objects(name='admin').first()
        if not role:
            print("Admin role not found. Cannot create default admin.")
            return

        if not User.objects(email=os.getenv("DEFAULT_ADMIN_EMAIL")).first():
            admin = User(
                email=os.getenv("DEFAULT_ADMIN_EMAIL"),
                password=os.getenv("DEFAULT_ADMIN_PASSWORD"),
                role=role,
                is_admin=True
            )
            admin.hash_password()
            admin.save()
            print("Default admin user created.")
        else:
            print("Admin user already exists.")

    @staticmethod
    def validate_role(role_name):
        role = Role.objects(name=role_name).first()
        if not role:
            raise ValueError(f"Role '{role_name}' does not exist.")
        return role
