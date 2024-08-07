from flask import Blueprint, request, jsonify, current_app as app  # noqa: F401
from flask_security import Security, SQLAlchemyUserDatastore, login_required, current_user
from flask_login import login_user, logout_user
from app.models.user import db, User, Role

auth_bp = Blueprint('auth', __name__)

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security()

@auth_bp.route('/user/login', methods=['POST'])
def login():
    username: str = request.form.get('username')
    password: str = request.form.get('password')
    user: User = user_datastore.find_user(email=username)
    if user and user.check_password(password):
        login_user(user)
        return jsonify({"status": 200, "message": "OK!"})
    return jsonify({"status": 401, "message": "凭据错误，登录失败！请检查你的用户名或密码。"})

@auth_bp.route('/user/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({"status": 200, "message": "登出成功"})

@auth_bp.route('/user/status', methods=['GET'])
@login_required
def status():
    user_info = {
        "id": current_user.id,
        "email": current_user.email,
        "roles": [role.name for role in current_user.roles],
        "avatar": current_user.avatar,
        "experience": current_user.experience,
        "level": current_user.level
    }
    return jsonify(user_info)
