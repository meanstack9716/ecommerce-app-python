from app.extensions import db
from datetime import datetime
from mongoengine import EmbeddedDocument, EmbeddedDocumentField
from bson import ObjectId

class PromoCodeApplicableProducts(EmbeddedDocument):
    product_id = db.ReferenceField('Products')
    category_id = db.ReferenceField('Category')
    subcategory_id = db.ReferenceField('SubCategory')
    subsubcategory_id = db.ReferenceField('SubSubCategory')
    brand_id = db.ReferenceField('ProductBrands')

class PromoCode(db.Document):
    code = db.StringField(required=True, unique=True)
    description = db.StringField()
    discount_type = db.StringField(required=True)
    discount_value = db.DecimalField(required=True, precision=2)
    min_order_amount = db.DecimalField(precision=2)
    max_discount_amount = db.DecimalField(precision=2)
    start_date = db.DateTimeField(required=True)
    end_date = db.DateTimeField(required=True)
    max_uses = db.IntField()
    current_uses = db.IntField(default=0)
    is_active = db.BooleanField(default=True)
    is_single_use = db.BooleanField(default=False)
    applicable_to = db.StringField(default='all')
    applicable_products = db.ListField(EmbeddedDocumentField(PromoCodeApplicableProducts))
    created_by = db.ReferenceField('User', required=True)
    created_at = db.DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'promo_codes',
        'indexes': [
            'code',
            'start_date',
            'end_date',
            'is_active',
            'created_by'
        ]
    }

    def is_valid(self, user_id, order_amount, products):
        now = datetime.utcnow()
        if not self.is_active:
            return False, "Promo code is not active"
        if now < self.start_date:
            return False, "Promo code is not yet valid"
        if now > self.end_date:
            return False, "Promo code has expired"
        if self.max_uses and self.current_uses >= self.max_uses:
            return False, "Promo code usage limit reached"
        if self.min_order_amount and order_amount < float(self.min_order_amount):
            return False, f"Minimum order amount of {self.min_order_amount} required"
        
        if self.applicable_to == 'specific':
            valid = False
            for product in products:
                for applicable in self.applicable_products:
                    if (applicable.product_id and product.id == applicable.product_id.id) or \
                       (applicable.category_id and product.category_id.id == applicable.category_id.id) or \
                       (applicable.subcategory_id and product.subcategory_id.id == applicable.subcategory_id.id) or \
                       (applicable.subsubcategory_id and product.subsubcategory_id.id == applicable.subsubcategory_id.id) or \
                       (applicable.brand_id and product.brand_id.id == applicable.brand_id.id):
                        valid = True
                        break
                if not valid:
                    return False, "Promo code not applicable to all products in cart"
        
        return True, "Valid promo code"

    def calculate_discount(self, order_amount):
        if self.discount_type == 'percentage':
            discount = (order_amount * float(self.discount_value)) / 100
            if self.max_discount_amount and discount > float(self.max_discount_amount):
                return float(self.max_discount_amount)
            return discount
        else:
            if self.max_discount_amount and float(self.discount_value) > float(self.max_discount_amount):
                return float(self.max_discount_amount)
            return min(float(self.discount_value), order_amount)

    def increment_usage(self):
        self.current_uses += 1
        if self.max_uses and self.current_uses >= self.max_uses:
            self.is_active = False
        self.save()

class UserPromoCode(db.Document):
    user_id = db.ReferenceField('User', required=True)
    promo_code_id = db.ReferenceField('PromoCode', required=True)
    order_id = db.ReferenceField('Order')
    used_at = db.DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'user_promo_codes',
        'indexes': [
            'user_id',
            'promo_code_id',
            'order_id'
        ]
    }