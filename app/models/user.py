import os
from app import db
from flask_bcrypt import generate_password_hash, check_password_hash
from datetime import datetime
from constants import GENDER_CHOICES, ROLE_ADMIN
from app.models.role import Role
from app.models.seller import Seller
from app.models.address import Address

class User(db.Document):
    email = db.StringField(required=True, unique=True)
    password = db.StringField(required=True, min_length=6)
    first_name = db.StringField()
    last_name = db.StringField()
    phone_number = db.StringField()
    gender = db.StringField(choices=GENDER_CHOICES)
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

    def save(self, *args, **kwargs):
        is_new = not bool(self.id)
        super(User, self).save(*args, **kwargs)
        if is_new and self.is_admin:
            self._create_admin_seller_profile()
    
    def _create_admin_seller_profile(self):
        if not Seller.objects(user_id=self).first():
            address = Address(
                user_id=self,
                line1=os.getenv("DEFAULT_ADMIN_ADDRESS_LINE1", "Corporate Office"),
                line2=os.getenv("DEFAULT_ADMIN_ADDRESS_LINE2", "Administration Department"),
                city=os.getenv("DEFAULT_ADMIN_ADDRESS_CITY", "Headquarters"),
                state=os.getenv("DEFAULT_ADMIN_ADDRESS_STATE", "Main State"),
                postal_code=os.getenv("DEFAULT_ADMIN_ADDRESS_POSTAL_CODE", "100001"),
                country=os.getenv("DEFAULT_ADMIN_ADDRESS_COUNTRY", "Business Country"),
                contact_name=f"{self.first_name} {self.last_name}",
                contact_number=int(self.phone_number) if self.phone_number and self.phone_number.isdigit() else 9999999999,
                address_type="Business",
                is_primary=True
            )
            address.save()
            
            seller = Seller(
                user_id=self,
                businessName=os.getenv("DEFAULT_ADMIN_BUSINESS_NAME", f"{self.first_name} {self.last_name} Administration"),
                businessType=os.getenv("DEFAULT_ADMIN_BUSINESS_TYPE", "Corporate"),
                businessEmail=self.email,
                businessMobile=self.phone_number or "9999999999",
                address=address,
                businessAddress=address,
                gst_number=os.getenv("DEFAULT_ADMIN_GST_NUMBER", "ADMIN0000000"),
                is_approved='approved',
                approved_by=self
            )
            seller.save()

    @staticmethod
    def create_default_admin():
        role = Role.objects(name='admin').first()
        if not role:
            print("Admin role not found. Cannot create default admin.")
            return

        if not User.objects(email=os.getenv("DEFAULT_ADMIN_EMAIL")).first():
            admin = User(
                first_name=os.getenv("DEFAULT_ADMIN_FIRST_NAME", "Admin"),
                last_name=os.getenv("DEFAULT_ADMIN_LAST_NAME", "User"),
                email=os.getenv("DEFAULT_ADMIN_EMAIL", "admin@example.com"),
                password=os.getenv("DEFAULT_ADMIN_PASSWORD", "securepassword"),
                phone_number=os.getenv("DEFAULT_ADMIN_PHONE", "9999999999"),
                role=role,
                is_admin=True
            )
            admin.hash_password()
            admin.save()
            print("Default admin user, address, and seller profile created.")
        else:
            print("Admin user already exists.")

    @staticmethod
    def validate_role(role_name):
        role = Role.objects(name=role_name).first()
        if not role:
            raise ValueError(f"Role '{role_name}' does not exist.")
        return role