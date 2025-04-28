from flask import Flask, redirect, url_for, session, g
from app.extensions import db, jwt, mail, bcrypt
from .config import Config
from app.models import User

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    bcrypt.init_app(app)

    from app.models.user import User
    from app.models.role import Role
    from app.models.seller import Seller
    from app.models.address import Address

    Role.initialize_roles()
    User.create_default_admin()
    from app.routes.api.auth import auth_bp
    from app.routes.web import admin_api
    from app.routes.api.user import user_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_api)
    app.register_blueprint(user_bp)

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
