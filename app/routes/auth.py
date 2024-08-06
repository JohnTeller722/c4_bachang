from flask import Blueprint, request, jsonify, current_app as app
from flask_security import Security, SQLAlchemyUserDatastore, login_required, current_user
from flask_login import login_user, logout_user
from app.models.user import db, User, Role

auth_bp = Blueprint('auth', __name__)

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security()

@auth_bp.route('/login', methods=['POST'])
def login():
    username: str = request.form.get('username')
    password: str = request.form.get('password')
    user: User = user_datastore.find_user(email=username)
    if user and user.verify_password(password):
        login_user(user)
        return jsonify({"status": 200, "message": "OK!"})
    return jsonify({"status": 401, "message": "凭据错误，登录失败！请检查你的用户名或密码。"})

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({"status": 200, "message": "登出成功"})

@auth_bp.route('/status', methods=['GET'])
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

@auth_bp.route('/two_factor_setup', methods=['POST'])
@login_required
def two_factor_setup():
    method: str = request.form.get('method')
    if method not in app.config['SECURITY_TWO_FACTOR_ENABLED_METHODS']:
        return jsonify({"status": 400, "message": "无效的两步验证方法"})
    current_user.tf_primary_method = method
    db.session.commit()
    return jsonify({"status": 200, "message": "两步验证设置成功"})