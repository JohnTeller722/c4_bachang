from flask import Blueprint, jsonify, request
from flask_socketio import SocketIO, emit
from app.models.experiment import Experiment
# from app.models.task import Task


main_bp = Blueprint('main', __name__)
socketio = SocketIO()


def NotImplemented(message):
    return {"status": 500, "message": message}


@main_bp.route('/version', methods=['GET'])
def get_version() -> jsonify:
    return jsonify({"version": "v1.0.0"})


@main_bp.route('/ping', methods=['GET'])
def ping() -> jsonify:
    return jsonify({"status": 200, "message": "pong!"})


@main_bp.route('/task/list', methods=['GET'])
def get_task_list() -> str:
    tasks = Task.query.all()
    result = [
        task.to_dict()
        for task in tasks
    ]
    return jsonify(result)


@main_bp.route('/task/pause', methods=['POST'])
def pause_task() -> str:
    taskUUID = request.args.get('taskUUID')

    if not taskUUID:
        return jsonify({"status": 400, "message": "Bad Request"}), 400

    # 暂停任务的逻辑
    # TODO: 实现暂停任务的具体逻辑
    return jsonify({"status": 200, "message": "Task paused"}), 200


@main_bp.route('/exp/list', methods=['GET'])
def get_experiment_list() -> str:
    experiments = Experiment.query.all()
    result = [
        exp.to_dict()
        for exp in experiments
    ]
    return jsonify(result)


@main_bp.route('/exp/start', methods=['POST'])
def start_experiment() -> str:
    expUUID = request.args.get('expUUID')
    start_type = request.args.get('type', type=int)

    # 参数检查
    if expUUID is None:
        return {"status": 400, "message": "参数里应该包含expUUID"}
    if start_type in [1, 2]:
        return {"status": 400, "message": "启动类型应该是1或者2"}

    # 检查是否已经有相同的实验在运行
    # WARN: 可以允许不同用户启动同一实验，这一点通过Namespace来保证
    existing_experiment = Experiment.query.filter_by(expUUID=expUUID).first()
    if existing_experiment:
        return jsonify({"status": 400, "message": "Experiment already running"}), 400

    # 启动实验的逻辑
    # TODO:实现这个逻辑
    return jsonify({"status": 200, "message": "Experiment started"}), 200

@main_bp.route('/exp/stop', methods=['POST'])
def stop_experiment() -> str:
    expUUID = request.args.get('expUUID')

    if not expUUID:
        return jsonify({"status": 400, "message": "Bad Request"}), 400

    # 停止实验的逻辑
    # TODO: 实现停止实验的具体逻辑
    return jsonify({"status": 200, "message": "Experiment stopped"}), 200

@main_bp.route('/exp/config', methods=['POST'])
def config_experiment() -> str:
    expUUID = request.args.get('expUUID')
    new_config = request.data.decode('utf-8')
    return NotImplemented("配置功能尚未实现")
    if not expUUID or not new_config:
        return jsonify({"status": 400, "message": "Bad Request"}), 400
    # 修改实验配置的逻辑
    # TODO: 实现修改实验配置的具体逻辑
    return jsonify({"status": 200, "message": "Experiment config updated"}), 200

@main_bp.route('/exp/delete', methods=['POST'])
def delete_experiment() -> str:
    expUUID = request.args.get('expUUID')
    raise NotImplementedError("删除功能尚未实现")
    if not expUUID:
        return jsonify({"status": 400, "message": "Bad Request"}), 400
    # 删除实验的逻辑
    # TODO: 实现删除实验的具体逻辑
    return jsonify({"status": 200, "message": "Experiment deleted"}), 200

@main_bp.route('/exp/edit', methods=['POST'])
def edit_experiment() -> str:
    expUUID = request.args.get('expUUID')
    # 获取其他需要修改的参数
    # TODO: 获取并处理其他参数
    raise NotImplementedError("编辑功能尚未实现")
    if not expUUID:
        return jsonify({"status": 400, "message": "Bad Request"}), 400
    # 修改实验参数的逻辑
    # TODO: 实现修改实验参数的具体逻辑
    return jsonify({"status": 200, "message": "Experiment edited"}), 200

@main_bp.route('/exp/add', methods=['POST'])
def add_experiment() -> str:
    expUUID = request.args.get('expUUID')
    raise NotImplementedError("增加功能尚未实现")
    if not expUUID:
        return jsonify({"status": 400, "message": "Bad Request"}), 400
    # 添加实验的逻辑
    # TODO: 实现具体逻辑
    return jsonify({"status": 200, "message": "Experiment added"}), 200

@main_bp.route('/exp/pause', methods=['POST'])
def pause_experiment() -> str:
    expUUID = request.args.get('expUUID')

    if not expUUID:
        return jsonify({"status": 400, "message": "Bad Request"}), 400

    # 暂停实验的逻辑
    # TODO: 实现暂停实验的具体逻辑
    return jsonify({"status": 200, "message": "Experiment paused"}), 200

@main_bp.route('/exp/submit', methods=['POST'])
def submit_experiment() -> str:
    expUUID = request.args.get('expUUID')
    flag = request.args.get('flag')

    if not expUUID or not flag:
        return jsonify({"status": 400, "message": "Bad Request"}), 400

    # 提交实验flag的逻辑
    # TODO: 实现提交实验flag的具体逻辑
    return jsonify({"status": 200, "message": "Flag submitted"}), 200

@socketio.on('task.ssh')
def handle_task_ssh(data):
    taskUUID = data.get('taskUUID')  # noqa: F841
    # 实现SSH逻辑
    emit('task.ssh.response', {'status': 200, 'message': 'SSH started'})

@socketio.on('task.vnc')
def handle_task_vnc(data):
    taskUUID = data.get('taskUUID')  # noqa: F841
    # 实现VNC逻辑
    emit('task.vnc.response', {'status': 200, 'message': 'VNC started'})

@socketio.on('monitor.resource')
def handle_monitor_resource(data):
    taskUUID = data.get('taskUUID')  # noqa: F841
    # 获取资源占用逻辑
    resource_usage = "example_resource_usage"  # 示例数据
    emit('monitor.resource.response', {'status': 200, 'resource_usage': resource_usage})

@socketio.on('monitor.traffic')
def handle_monitor_traffic(data):
    taskUUID = data.get('taskUUID')  # noqa: F841
    # 获取网络流量逻辑
    network_traffic = "example_network_traffic"  # 示例数据
    emit('monitor.traffic.response', {'status': 200, 'network_traffic': network_traffic})

@socketio.on('monitor.journal')
def handle_monitor_journal(data):
    taskUUID = data.get('taskUUID')  # noqa: F841
    # 获取容器日志逻辑
    logs = "example_logs"  # 示例数据
    emit('monitor.journal.response', {'status': 200, 'logs': logs})
