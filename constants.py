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


# API Endpoint Constants
BASE_URL = ''

REGISTER = f'{BASE_URL}/register'
LOGIN = f'{BASE_URL}/login'
FORGOT_PASSWORD = f'{BASE_URL}/send-email-code'
VERIFY_OTP = f'{BASE_URL}/verify-email-code'
RESET_PASSWORD = f'{BASE_URL}/reset-password'

# WEB Endpoint Constants
Login_WEB_URL = f'/login'
SIGNUP_WEB_URL = f'/signup'
FORGOT_PASSWORD_WEB_URL = f'/forgot-password'
VERIFY_OTP_WEB_URL= f'/verify-otp'
RESET_PASSWORD_WEB_URL = f'/reset-password'
DASHBOARD_WEB_URL = f'/dashboard'
ALL_USER_LIST_WEB_URL = f'/all-users-list'
CATEGORY_LIST_WEB_URL = '/category-list'
ADD_CATEGORY_WEB_URL = '/add-new-category'
SUBCATEGORY_LIST_WEB_URL = f'/subcategories-list'
Add_SUBCATEGORY_LIST_WEB_URL = f'/subcategories/add'
PRODUCT_LIST_WEB_URL = f'/product-list'
PRODUCT_ADD_WEB_URL = f'products/add'

# User API Endpoint Constants
GET_USER_PROFILE = f'/me'
UPDATE_PROFILE = f'/update-profile'
UPDATE_PROFILE_PIC = f'/update-profile-pic'
DELETE_PROFILE_PIC = f'/delete-profile-pic'
LOGOUT = f'/logout'
ADD_SELLER = f'/add_new_seller'



# Category API Endpoint Constants
API_CATEGORY_LIST = '/api/categories/list'
API_ADD_CATEGORY = '/api/categories/add'
API_SUBCATEGORY_LIST = '/api/subcategories/list'
API_ADD_SUBCATEGORY = '/api/subcategories/add'
API_GET_SUBCATEGORIES_BY_CATEGORY_ID = '/api/get-subcategories/<category_id>'

API_ADD_PRODUCTTYPE = '/api/add-product-type'
API_GET_PRODUCT_TYPE_BY_SUBCATEGORY_ID = '/api/get-product-types/<subcategory_id>'
