from flask import Flask, redirect, url_for, session, g, current_app
from app.extensions import db, jwt, mail, bcrypt
from .config import Config
from app.models import User
import os
from app.utils.sidebar import sidebar_context

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    bcrypt.init_app(app)

    # Import models here
    from app.models.user import User
    from app.models.role import Role
    from app.models.seller import Seller
    from app.models.brands import ProductBrands
    from app.models.address import Address, AddressDetail
    from app.models.identification import Identification
    from app.models.category_modal import Category, SubCategory, SubSubCategory
    from app.models.products import Products, ProductVariant, ProductVariantImage

    from app.seed_data import seed_data



    from app.models.add_products import AddProducts
    from app.models.brands import ProductBrands
    from app.seed_data import seed_data

    sidebar_context(app)
    with app.app_context():
        Role.initialize_roles()
        User.create_default_admin()
        seed_data()

    # Import routes and blueprints
    from app.routes.api.auth import auth_bp
    from app.routes.web import admin_api
    from app.routes.api.user import user_bp
    from app.routes.api.seller import seller_bp
    from app.routes.api.category import category_bp
    from app.routes.api.subcategory import subcategory_bp
    from app.routes.api.sub_sub_category import sub_sub_category_bp
    from app.routes.api.products import products_bp
    from app.routes.api.brands import brand_bp

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_api)
    app.register_blueprint(user_bp)
    app.register_blueprint(seller_bp)
    app.register_blueprint(category_bp)
    app.register_blueprint(subcategory_bp)
    app.register_blueprint(sub_sub_category_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(brand_bp)

    @app.before_request
    def before_request():
        if 'user_id' in session:
            g.current_user = User.objects(id=session['user_id']).first()
        else:
            g.current_user = None

    @app.route('/')
    def index():
        return redirect(url_for('admin_api.login_page'))

    return app
