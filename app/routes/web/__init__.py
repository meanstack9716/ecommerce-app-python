from flask import Blueprint

admin_api = Blueprint("admin_api", __name__, url_prefix="")

from .auth_routes import *
from .dashboard_routes import *
from .user_routes import *
from .order_routes import *
from .settings_routes import *
