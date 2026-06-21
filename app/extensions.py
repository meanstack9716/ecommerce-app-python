from flask_mongoengine import MongoEngine
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_bcrypt import Bcrypt
from flask_apscheduler import APScheduler

db = MongoEngine()
jwt = JWTManager()
mail = Mail()
bcrypt = Bcrypt()
scheduler = APScheduler()
