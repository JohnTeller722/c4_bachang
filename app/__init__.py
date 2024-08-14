from flask import Flask
from flask_sqlalchemy import SQLAlchemy # noqa: F401
from flask_security import Security, SQLAlchemyUserDatastore
from app.models.user import db, User, Role
from app.routes.auth import auth_bp
from app.routes.main import main_bp
from config import Config
import qrcode   # noqa: F401

def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    security = Security(app, user_datastore)    # noqa: F841

    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(main_bp, url_prefix='/api')

    with app.app_context():
        db.create_all()

    return app
