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

ORDER_STATUS = ['pending', 'confirmed', 'processing', 'shipped', 'outOfDelivery', 'delivered', 'cancelled', 'return', 'refund']

ADDRESS_TYPES = ['Home', 'Office', 'Work', 'Store', 'Business', 'Other']

PROMO_CODE_TYPES = ['percentage', 'fixed_amount']
PROMO_CODE_APPLICABLE_TO = ['all', 'specific']

# API Endpoint Constants
REGISTER = f'/register'
LOGIN = f'/login'
FORGOT_PASSWORD = f'/send-email-code'
VERIFY_OTP = f'/verify-email-code'
AUTHENTICATE_USER = f'/verify-user'
RESET_PASSWORD = f'/reset-password'
RESEND_OTP = f'/resend-otp'

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
GET_CATEGORIES_FILTER_API_URL = '/categories-list'
DELETE_CATEGORIES_API_WEB_URL = '/delete_category/<category_id>'
EDIT_CATEGORY_WEB_URL = '/category/edit/<category_id>'

SUBCATEGORY_LIST_WEB_URL = f'/sub-categories/list'
Add_SUBCATEGORY_LIST_WEB_URL = f'/subcategories/add'
GET_SUBCATEGORIES_FILTER_API_URL = '/api/subcategories'

SUB_SUB_CATEGORY_LIST_WEB_URL = f'/sub-sub-category-list'
SUB_SUB_CATEGORY_WEB_URL = f'sub-sub-category/add'

ADD_NEW_PRODUCT_WEB_URL = f'/products/add'
GET_PRODUCT_LIST_WEB_URL = f'/products/list'
GET_PRODUCT_DETAILS_WEB_URL = f'/products/<product_id>'
GET_PROUDCT_EDIT_PAGE_BY_ID_WEB_URL = f'/products/edit/<product_id>'

GET_BRANDS_WEB_URL = f'/brands/list'
ADD_BRAND_WEB_URL = f'/brands/add'
UPDATE_BRAND_WEB_URL = f'/brands/edit/<brand_id>'

GET_BRANDS_WEB_URL = f'/brands/list'
ADD_BRAND_WEB_URL = f'/brands/add'
UPDATE_BRAND_WEB_URL = f'/brands/edit/<brand_id>'

ORDER_LIST_WEB_URL = '/orders'
ORDER_STATUS_UPDATE_WEB_URL = f'/orders/<order_id>/update-status'
ORDER_DETAILS_PAGE_WEB_URL = f'/order-details/<order_id>'

ADD_PROMO_CODE_WEB_URL = '/add-promo-code'
PROMO_CODE_LIST = '/promo-code-list'
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
PRODUCT_LISTS__BY_ID_API = f'/api/products/<string:product_id>'
EDIT_PRODUCT_API = f'/api/products/edit'
PRODUCT_LISTS_BY_ID_API = f'/api/products/<string:product_id>'
# Sub Sub Category API Endpoint Constants End

# Brand Endpoint API Start
GET_BRANDS_LIST_API = '/api/brand/lists'
ADD_BRAND_API = '/api/brands/add'
UPDATE_BRAND_API = '/api/update-brand'
DELETE_BRAND_API = '/brands/delete/<brand_id>'
# Brand Endpoint API End

# Cart Endpoint API Start
CART_ADD = '/api/cart/add'
CART_REMOVE = '/api/cart/remove'
CART_REMOVE_ALL = '/api/cart/remove-all'
CART_LIST = '/api/cart/list'
CART_CHECKOUT = '/api/cart/checkout'
# Cart Endpoint API End

# Address Endpoint Start
ADDRESS_ADD = '/api/address/add'
ADDRESS_UPDATE = '/api/address/update'
ADDRESS_REMOVE = '/api/address/remove/<address_id>'
ADDRESS_LIST = '/api/address/list'
ADDRESS_TYPES_API = '/api/address/types-list'
# Address Endpoint End

# Wishlist Endpoint Start
WISHLIST_ADD = '/api/wishlist/add'
WISHLIST_REMOVE = '/api/wishlist/remove'
WISHLIST_LIST = '/api/wishlist'
# Wishlist Endpoint End

# SaveForLater Endpoint Start
SAVEFORLATER_ADD = '/api/saveforlater/add'
SAVEFORLATER_REMOVE = '/api/saveforlater/remove'
SAVEFORLATER_LIST = '/api/saveforlater'
SAVEFORLATER_TO_CART = '/api/saveforlater/to-cart'
# SaveForLater Endpoint End

# Search Product Endpoint Start
SEARCH_PRODUCT_BY_KEYWORD_API = '/api/search-products'
# Search Product Endpoint End

# Orders Endpoint Start
ORDER_PLACE_API = f'/api/orders/new'
ORDER_LIST_API = f'/api/orders/list'
# Orders Endpoint End

# Sales OverView Endpoint Start
SALES_OVERVIEW_API = f'/api/sales/overview'
SALES_OVER_TIME_API = f'/api/sales/over-time'
SALES_TOP_PRODUCTS_API = f'/api/sales/top-products'
RECENT_SALES_API = f'/api/sales/recent'
TOP_PRODUCT_SALES_API = f'/api/sales/top-products'
GET_SALES_SELLER = f'/api/sales/sellers'
