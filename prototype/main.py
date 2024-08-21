import os
import math
import logging
import random
import time
from config import settings
from model import Experiment, ExperimentStatus, ExperimentRuntime
from flask import Flask, request
from utils import *

app = Flask(__name__)

explist = []
portlist = [i for i in range(20000, 60001)]

LOGFORMAT = "[%(asctime)s] [%(levelname)s] <%(threadName)s> %(message)s"
logging.basicConfig(format=LOGFORMAT, level = settings.LOGLEVEL)

def Request(code, message, content):
    if content:
        return {"code": code,
                "message": message,
                "type": "success" if code==200 else "failed",
                "result": content}
    else:
        return {"code": code,
                "message": message,
                "type": "success" if code==200 else "failed"}

@app.route("/exp/list", methods=["GET"])
def exp_list():
    name = request.args.get("name")
    ID = request.args.get("id")
    tags = request.args.get("tags")
    status = request.args.get("status")
    page = request.args.get("page")
    if not page:
        page = 1
    page = int(page)
    pageSize = request.args.get("pageSize")
    if not pageSize:
        pageSize = 10
    pageSize = int(pageSize)
    selected = []
    if not (name or ID or tags or status):
        selected = [i.dict() for i in explist]
    else:
        selected = [i.dict() for i in explist if i.match(name, ID, tags, status)]
    length = len(selected)
    tail = max(page * pageSize, length)
    try:
        result = selected[(page-1) * pageSize: tail]
    except:
        result = []
    count = len(result)
    return Request(200, "ok", 
                   {"page": page,
                    "pageSize": pageSize,
                    "pageCount": math.ceil(count / pageSize),
                    "itemCount": count,
                    "list": selected})


@app.route("/exp/create", methods=["POST"])
def exp_create():
    name = request.args.get("name")
    if not name:
        return Request(400, "请求有误：请给出实验名称。", None)
    _t = Experiment(name)
    write_exp(_t)
    explist.append(_t)
    return Request(200, f"实验{name}创建成功。", None)


@app.route("/exp/start", methods=["POST"])
def exp_start():
    uuid = request.args.get("uuid")
    if not uuid:
        return Request(400, "请求有误：请给出实验UUID。", None)
    _t = [i for i in explist if i.match(None, uuid, None, None)]
    if len(_t):
        _t = _t[0]
    else:
        return Request(400, "请求有误：实验UUID无效。", None)
    try:
        _l1 = list_experiments(namespace="default")
        logging.debug(f"启动实验前，命名空间{'default'}运行的pod: {_l1}")
        for i in _t.components:
            action_from_yaml(yaml_file=i.config, action="apply")
        time.sleep(1)
        _l2 = list_experiments(namespace="default")
        logging.debug(f"启动实验后，命名空间{'default'}运行的pod: {_l2}")
        _delta = list(set(_l2)-set(_l1))
        _t.runtime.components=_delta
        _t.status = ExperimentStatus.RUNNING
        return Request(200, "实验启动成功", None)
    except Exception as e:
        raise e
        _t.status = ExperimentStatus.FAILED
        return Request(400, "实验启动失败", {"exception": str(e)})

@app.route("/exp/shell", methods=["POST"])
def exp_shell():
    uuid = request.args.get("uuid")
    if not uuid:
        return Request(400, "请求有误：请给出容器UUID。", None)
    crid = int(uuid[37:])
    uuid = uuid[:36]
    logging.debug(f"尝试连接实验{uuid}的容器{crid}")
    _t = [i for i in explist if i.match(None, uuid, None, None)]
    if len(_t):
        _t = _t[0]
    else:
        return Request(400, "请求有误：实验UUID无效。", None)
    print(_t.runtime.components)
    try:
        _c = _t.runtime.components[crid]
    except IndexError:
        return Request(400, "请求有误：容器UUID无效。", None)
    logging.debug(f"连接容器{_c}...")
    if get_pod_status(_c)!="Running":
        _t.status = ExperimentStatus.FAILED
        return Request(500, "容器启动失败", {"podStatus": get_pod_status(_c)})
    try:
        port = random.choice(portlist)
        portlist.append(port)
        _t.runtime.port.append(port)
        ssh_tunnel(_c, namespace="default", port=port)
        return Request(200, "请求成功。", {"wsport": port})
    except Exception as e:
        print(e)
        return Request(500, "请求失败：未能连接到容器。", None)


@app.route("/exp/stop", methods=["POST"])
def exp_stop():
    uuid = request.args.get("uuid")
    if not uuid:
        return Request(400, "请求有误：请给出实验UUID。", None)
    _t = [i for i in explist if i.match(None, uuid, None, None)]
    if len(_t):
        _t = _t[0]
    else:
        return Request(400, "请求有误：实验UUID无效。", None)
    try:
        for i in _t.components:
            action_from_yaml(i.config, action="delete")
        _t.status = ExperimentStatus.STOPPED
        _t.runtime = ExperimentRuntime()
        return Request(200, "实验已停止", None)
    except Exception as e:
        print(e)
        _t.status = ExperimentStatus.CRASHED
        return Request(400, "实验停止失败", e)


def init():
    logging.info("自动导入resource中的实验...")
    uuidlist = set()
    for i in os.listdir("./resource"):
        logging.info(f"导入实验：{i}")
        _t = Experiment(i)
        _t.from_yaml(yml_file = "./resource/"+i+"/range-config.yaml")
        if _t.expUUID in uuidlist:
            logging.warning(f"实验{_t.name}的UUID已被导入过！")
        uuidlist.add(_t.expUUID)
        explist.append(_t)
    if test_kube_connection() is False:
        logging.error("无法连接到集群。")


if __name__ == "__main__":
    init()
    app.run(debug=True)
