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

CATEGORY_LIST_WEB_URL = '/category-list'
ADD_CATEGORY_WEB_URL = '/add-new-category'

SUBCATEGORY_LIST_WEB_URL = f'/sub-categories/list'
Add_SUBCATEGORY_LIST_WEB_URL = f'/subcategories/add'

SUB_SUB_CATEGORY_LIST_WEB_URL = f'/sub-sub-category-list'
SUB_SUB_CATEGORY_WEB_URL = f'sub-sub-category/add'

ADD_NEW_PRODUCT_WEB_URL = f'products/add'

# WEB Endpoint Constants End


# API Endpoint Constants Start

# User API Endpoint Constants
GET_USER_PROFILE = f'/me'
UPDATE_PROFILE = f'/update-profile'
UPDATE_PROFILE_PIC = f'/update-profile-pic'
DELETE_PROFILE_PIC = f'/delete-profile-pic'
LOGOUT = f'/logout'
ADD_SELLER = f'/add-new-seller'

# Category API Endpoint Constants
API_CATEGORY_LIST = '/api/categories/list'
API_ADD_CATEGORY = '/api/categories/add'

# Sub Category API Endpoint Constants
API_SUBCATEGORY_LIST = '/api/sub-categories/list'
API_ADD_SUBCATEGORY = '/api/sub-categories/add'
API_GET_SUBCATEGORIES_BY_CATEGORY_ID = '/api/sub-categories/<category_id>'

# Sub Sub Category API Endpoint Constants
SUB_SUB_CATEGORY_ADD_API = '/api/sub-sub-category/add'
GET_SUBSUBCATEGORIES_BY_SUBCATEGORY_ID_API = '/api/product-types/<subcategory_id>'

ADD_NEW_PRODUCT = f'/api/products/add'

# API Endpoint Constants End
