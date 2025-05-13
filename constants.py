# Role constants
ROLE_ADMIN = "admin"
ROLE_SELLER = "seller"
ROLE_USER = "user"
ALL_ROLES = [ROLE_ADMIN, ROLE_SELLER, ROLE_USER]

# Gender constants
GENDER_MALE = "male"
GENDER_FEMALE = "female"
GENDER_OTHER = "other"
GENDER_CHOICES = [GENDER_MALE, GENDER_FEMALE, GENDER_OTHER]

OTP_EXPIRY_MINUTES = 10

# Allowed Size and Allowed Gender constants 
ALLOWED_SIZES = ['XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL']
ALLOWED_GENDERS = ['Men', 'Women', 'Unisex', 'Kids']

APPROVAL_STATUSES = ['pending', 'approved', 'cancelled']

# API Endpoint Constants
BASE_URL = ''

REGISTER = f'{BASE_URL}/register'
LOGIN = f'{BASE_URL}/login'
FORGOT_PASSWORD = f'{BASE_URL}/send-email-code'
VERIFY_OTP = f'{BASE_URL}/verify-email-code'
RESET_PASSWORD = f'{BASE_URL}/reset-password'

# WEB Endpoint Constants Start
Login_WEB_URL = f'/login'
SIGNUP_WEB_URL = f'/signup'
FORGOT_PASSWORD_WEB_URL = f'/forgot-password'
VERIFY_OTP_WEB_URL= f'/verify-otp'
RESET_PASSWORD_WEB_URL = f'/reset-password'

DASHBOARD_WEB_URL = f'/dashboard'

ALL_USER_LIST_WEB_URL = f'/all-users-list'

ADD_SELLER_WEB_URL = f'/add-new-seller'
GET_SELLER_LIST_WEB_URL = f'/seller/list'
GET_SELLERS_API_URL = '/api/sellers'

CATEGORY_LIST_WEB_URL = '/category-list'
ADD_CATEGORY_WEB_URL = '/add-new-category'
CATEGORY_LIST_WEB_URL = '/category/list'
GET_CATEGORIES_FILTER_API_URL = '/api/categories'

SUBCATEGORY_LIST_WEB_URL = f'/sub-categories/list'
Add_SUBCATEGORY_LIST_WEB_URL = f'/subcategories/add'

SUB_SUB_CATEGORY_LIST_WEB_URL = f'/sub-sub-category-list'
SUB_SUB_CATEGORY_WEB_URL = f'sub-sub-category/add'

ADD_NEW_PRODUCT_WEB_URL = f'products/add'
GET_PRODUCT_LIST_WEB_URL = f'products/list'

GET_BRANDS_WEB_URL = f'/brands/list'
ADD_BRAND_WEB_URL = f'/brands/add'
UPDATE_BRAND_WEB_URL = f'/brands/edit/<brand_id>'

GET_BRANDS_WEB_URL = f'/brands/list'
ADD_BRAND_WEB_URL = f'/brands/add'
UPDATE_BRAND_WEB_URL = f'/brands/edit/<brand_id>'



# WEB Endpoint Constants End

# API Endpoint Constants Start

# User API Endpoint Constants
GET_USER_PROFILE = f'/me'
UPDATE_PROFILE = f'/update-profile'
UPDATE_PROFILE_PIC = f'/update-profile-pic'
DELETE_PROFILE_PIC = f'/delete-profile-pic'
LOGOUT = f'/logout'
ADD_SELLER = f'/add-new-seller'
GET_SELLER_API = f'/seller/list'


# Category API Endpoint Constants
API_CATEGORY_LIST = '/api/categories/list'
API_ADD_CATEGORY = '/api/categories/add'
API_CATEGORY_LIST_BY_ID = '/api/categories/list/<string:category_id>'

# Sub Category API Endpoint Constants
API_SUBCATEGORY_LIST = '/api/sub-categories/list'
API_ADD_SUBCATEGORY = '/api/sub-categories/add'
API_GET_SUBCATEGORIES_BY_CATEGORY_ID = '/api/sub-categories/list/<category_id>'

# Sub Sub Category API Endpoint Constants
SUB_SUB_CATEGORY_ADD_API = '/api/sub-sub-category/add'
GET_SUBSUBCATEGORIES_BY_CATEGORY_ID_API = '/api/sub-sub-categories/list';

ADD_NEW_PRODUCT_API = f'/api/products/add'
PRODUCT_LISTS_API= f'/api/products/list'
EDIT_PRODUCT_API = f'/api/products/edit'
# Sub Sub Category API Endpoint Constants End

# Brand Endpoint API Start
GET_BRANDS_LIST_API = '/api/brand/lists'
ADD_BRAND_API = '/api/brands/add'
UPDATE_BRAND_API = '/api/update-brand'
DELETE_BRAND_API = '/delete_brand/<string:brand_id>'
# Brand Endpoint API End

# Cart Endpoint API Start
CART_ADD = '/api/cart/add'
CART_REMOVE = '/api/cart/remove'
CART_LIST = '/api/cart/list'
CART_CHECKOUT = '/api/cart/checkout'
# Cart Endpoint API End


WISHLIST_ADD = '/api/wishlist/add'
WISHLIST_REMOVE = '/api/wishlist/remove'
WISHLIST_LIST = '/api/wishlist'

SAVEFORLATER_ADD = '/api/saveforlater/add'
SAVEFORLATER_REMOVE = '/api/saveforlater/remove'
SAVEFORLATER_LIST = '/api/saveforlater'
SAVEFORLATER_TO_CART = '/api/saveforlater/to-cart'