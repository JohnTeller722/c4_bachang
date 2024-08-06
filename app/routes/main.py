from flask import Blueprint, jsonify

main_bp = Blueprint('main', __name__)

@main_bp.route('/version', methods=['GET'])
def get_version() -> jsonify:
    return jsonify({"version": "v1.0.0"})

@main_bp.route('/ping', methods=['GET'])
def ping() -> jsonify:
    return jsonify({"status": 200, "message": "pong!"})