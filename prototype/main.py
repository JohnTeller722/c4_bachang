import sys
import os
import math
import logging
import random
import time
import uvicorn
import tarfile
import json
from config import settings
from model import Experiment, ExperimentStatus, ExperimentRuntime
from flask import Flask, request, send_file
from utils import *
import threading
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

explist = []
portlist = [i for i in range(20000, 60001)]
kube_arch = ""

ssh_pool = ThreadPoolExecutor(settings.SSH_MAX_CONNECTIONS)

LOGFORMAT = "[%(asctime)s] [%(levelname)s] <%(threadName)s> %(message)s"
logging.basicConfig(format=LOGFORMAT, level = settings.LOGLEVEL)

def Response(code, message, content):
    if content is not None:
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
    print(explist)
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
    return Response(200, "ok", 
                   {"page": page,
                    "pageSize": pageSize,
                    "pageCount": math.ceil(count / pageSize),
                    "itemCount": count,
                    "list": selected})


@app.route("/exp/create", methods=["GET", "POST"])
def exp_create():
    name = request.args.get("name")
    if not name:
        return Response(400, "请求有误：请给出实验名称。", None)
    _t = Experiment(name)
    _t.updateUUID()
    _t.dirname = name
    write_exp(_t)
    explist.append(_t)
    return Response(200, f"实验{name}创建成功。", None)


@app.route("/exp/delete", methods=["GET", "POST"])
def exp_delete():
    uuid = request.args.get("uuid")
    if not uuid:
        return Response(400, "请求有误：请给出实验UUID。", None)
    _t = [i for i in explist if i.match(None, uuid, None, None)]
    if len(_t) == 1:
        _t = _t[0]
    elif len(_t) == 0:
        return Response(400, "请求有误：实验UUID无效。", None)
    else:
        _t = _t[0]
        logging.warning("发现多个UUID相同的实验！")
        logging.warning(f"目前选中的是{_t.name}，再次执行此函数以删除剩余的实验。")
    explist.remove(_t)
    if remove_exp(_t):
        logging.info(f"删除了实验{_t.name}")
        return Response(200, "ok", None)
    else:
        logging.error(f"删除实验{_t.name}失败")
        return Response(500, "删除实验失败", None)


@app.route("/exp/start", methods=["GET", "POST"])
def exp_start():
    global kube_arch
    uuid = request.args.get("uuid")
    if not uuid:
        return Response(400, "请求有误：请给出实验UUID。", None)
    _t = select_exp(uuid)
    if _t is None:
        return Response(400, "请求有误：实验UUID无效。", None)
    try:
        _l1 = list_experiments(namespace="default")
        logging.debug(f"启动实验前，命名空间{'default'}运行的pod: {_l1}")
        _success = False

        for i in _t.components:
            if i.types == ComponentType.KUBERNETES: 
                if kube_arch in i.config:
                    logging.info(f"启动组件{i.name}的{kube_arch}架构配置{i.config[kube_arch]}")
                    action_from_yaml(yaml_file=i.config[kube_arch],
                                     workdir=settings.RESOURCE_DIR + '/' + _t.dirname,
                                     action="apply")
                    _success = True
                elif "all" in i.config:
                    logging.info(f"启动组件{i.name}的通用架构配置{i.config['all']}")
                    action_from_yaml(yaml_file=i.config["all"],
                                     workdir=settings.RESOURCE_DIR + '/' + _t.dirname,
                                     action="apply")
                    _success = True
                else:
                    logging.warning(f"组件{i.name}没有当前架构({kube_arch})的启动配置！已跳过该组件。")
            time.sleep(0.5)

        time.sleep(1)
        _l2 = list_experiments(namespace="default")
        logging.debug(f"启动实验后，命名空间{'default'}运行的pod: {_l2}")
        _delta = list(set(_l2)-set(_l1))
        _t.runtime.components=_delta
        if _success:
            _t.status = ExperimentStatus.RUNNING
            _t.statusComment = f"于{current_time()}启动成功"
            return Response(200, "实验启动成功", None)
        else:
            _t.status = ExperimentStatus.MISTAKEN
            _t.statusComment = f"找不到匹配本架构({kube_arch})的配置文件"
            return Response(400, "实验配置有误", {"reason": "没有任何一个组件被启动"})
    except FileNotFoundError as e:
        print(e)
        # _t.status = ExperimentStatus.MISTAKEN
        _t.statusComment = f"找不到下列配置文件:{e.filename}"
        return Response(400, "实验配置有误", {"reason": str(e)})
    except Exception as e:
        # raise e
        _t.status = ExperimentStatus.FAILED
        _t.statusComment = f"启动时出错:{str(e)}" # TODO:traceback
        return Response(500, "实验启动失败", {"exception": str(e)})

@app.route("/exp/shell", methods=["GET", "POST"])
def exp_shell():
    uuid = request.args.get("uuid")
    if not uuid:
        return Response(400, "请求有误：请给出容器UUID。", None)
    uuid, crid = parseUUID(uuid, hascrid=True)
    logging.debug(f"尝试连接实验{uuid}的容器{crid}")
    _t = select_exp(uuid)
    if _t is None:
        return Response(400, "请求有误：实验UUID无效。", None)
    print(_t.runtime.components)
    try:
        _c = _t.runtime.components[crid]
    except IndexError:
        return Response(400, "请求有误：容器UUID无效。", None)
    logging.debug(f"连接容器{_c}...")
    if get_pod_status(_c)!="Running":
        _t.status = ExperimentStatus.FAILED
        return Response(500, "容器启动失败", {"podStatus": get_pod_status(_c)})
    try:
        port = random.choice(portlist)
        portlist.append(port)
        _t.runtime.port.append(port)
        ssh_pool.submit(ssh_tunnel, _c, namespace="default", port=port)
        return Response(200, "请求成功。", {"wsport": port})
    except Exception as e:
        print(e)
        return Response(500, "请求失败：未能连接到容器。", None)

def select_exp(uuid):
    _t = [i for i in explist if i.match(None, uuid, None, None)]
    if len(_t) == 1:
        _t = _t[0]
    elif len(_t) == 0:
        return None
    else:
        _t = _t[0]
        logging.warning("发现多个UUID相同的实验！")
    return _t
    

@app.route("/exp/config/list", methods=["GET"])
def exp_config_list():
    uuid = request.args.get("uuid")
    if not uuid:
        return Response(400, "请求有误：请给出实验UUID。", None)
    uuid = parseUUID(uuid, hascrid=False)
    _t = select_exp(uuid)
    if _t is None:
        return Response(400, "请求有误：实验UUID无效。", None)
    if _t.dirname=="":
        return Response(500, "服务器错误：数据有误。", "该实验不存在dirname字段。")
    _l = []
    for i in os.listdir(exp_path(_t.dirname)):
        if os.stat(exp_path(_t.dirname)+"/"+i).st_size > settings.MAXINUM_FILESIZE:
            logging.debug(f"文件{i}超过限制大小，已被排除。")
            pass
        _l.append({"label": '/' + i , "value": i})
    return Response(200, "ok", _l)

@app.route("/exp/config/read",methods=["GET"])
def exp_config_read():
    uuid = request.args.get("uuid")
    filename = request.args.get("filename")
    if not uuid:
        return Response(400, "请求有误：请给出实验UUID。", None)
    if not filename:
        return Response(400, "请求有误：请给出文件名。", None)
    if '/' in filename:
        return Response(400, "请求有误：请求存在威胁。", None)
    uuid = parseUUID(uuid, hascrid=False)
    _t = select_exp(uuid)
    if _t is None:
        return Response(400, "请求有误：实验UUID无效。", None)
    try:
        os.stat(exp_path(_t.dirname)+"/"+filename)
        return Response(200, "ok", open(exp_path(_t.dirname) + '/' + filename).read())
    except FileNotFoundError:
        return Response(404, "请求有误：文件不存在。", f"文件{filename}不存在。")

@app.route("/exp/config/write", methods=["POST"])
def exp_config_write():
    uuid = request.args.get("uuid")
    filename = request.args.get("filename")
    if not uuid:
        return Response(400, "请求有误：请给出实验UUID。", None)
    if not filename:
        return Response(400, "请求有误：请给出文件名。", None)
    if '/' in filename:
        return Response(400, "请求有误：请求存在威胁。", None)
    uuid = parseUUID(uuid, hascrid=False)
    _t = select_exp(uuid)
    if _t is None:
        return Response(400, "请求有误：实验UUID无效。", None)
    code = request.data
    # print(code)
    code = eval(code.decode("utf-8"))
    # print(code, type(code))
    if filename == "range-config.yaml":
        try:
            yaml_object = yaml.load(code, yaml.SafeLoader)
            # print("yaml_OBJ", yml_object)
            if yaml_object["expUUID"] != _t.expUUID:
                return Response(400,
                               "服务器不接受该保存：UUID已改变",
                               {"oldUUID": _t.expUUID, "newUUID": yaml_object["expUUID"]})
        except Exception as e:
            logging.warning(f"分析yaml时失败，已跳过。")
            logging.warning(str(e))
            pass
    with open(exp_path(_t.dirname)+'/'+filename, "w") as f:
        f.write(code)
    _t.from_yaml(yaml_file=exp_path(_t.dirname)+"/range-config.yaml")
    return Response(200, "文件保存成功", None)

@app.route("/exp/param", methods=["GET", "POST"])
def exp_param():
    uuid = request.args.get("uuid")
    if not uuid:
        return Response(400, "请求有误：请给出实验UUID。", None)
    uuid = parseUUID(uuid, hascrid=False)
    _t = select_exp(uuid)
    if _t is None:
        return Response(400, "请求有误：实验UUID无效。", None)
    if request.method == "GET":
        return Response(200, "ok", _t.dict())
    else:
        # print(request.data)
        _d = json.loads(request.data)
        try:
            _t.name = _d["name"]
            _t.desc = _d["desc"]
            _t.tags = _d["tags"]
            _t.author = _d["author"]
            return Response(200, "保存成功", None)
        except KeyError as e:
            return Response(400, "请求有误：键值缺失", str(e))
        except Exception as e:
            return Response(500, "保存失败，内部错误", str(e))


@app.route("/exp/download", methods=["GET"])
def exp_download():
    # TODO:鉴权
    uuid = request.args.get("uuid")
    if not uuid:
        return Response(400, "请求有误：请给出实验UUID。", None)
    uuid = parseUUID(uuid, hascrid=False)
    _t = select_exp(uuid)
    if _t is None:
        return Response(400, "请求有误：实验UUID无效。", None)
    file = tarfile.open(name=f"{settings.TEMP_DIR}/{_t.expUUID}.tar.gz", mode="w:gz")
    for i in os.listdir(exp_path(_t.dirname)):
        file.add(exp_path(_t.dirname) + '/' + i, arcname=i)
    file.close()
    return send_file(f"{settings.TEMP_DIR}/{_t.expUUID}.tar.gz")


@app.route("/exp/upload", methods=["GET", "POST"])
def exp_upload():
    # TODO:鉴权
    uuid = request.args.get("uuid")
    if not uuid:
        return Response(400, "请求有误：请给出实验UUID。", None)
    uuid = parseUUID(uuid, hascrid=False)
    _t = select_exp(uuid)
    if _t is None:
        return Response(400, "请求有误：实验UUID无效。", None)
    data = request.files.get("file")
    _n = str(random.randint(0,32768))
    logging.debug(f"正在将接收到的文件保存到{settings.TEMP_DIR}/{_n}.tar.gz")
    if data:
        data.save(f"{settings.TEMP_DIR}/{_n}.tar.gz")
    else:
        return Response(400, "请求有误：上传文件为空。", None)
    _f = tarfile.open(name=f"{settings.TEMP_DIR}/{_n}.tar.gz", mode="r|*")
    _f.extractall(path=exp_path(_t.dirname))
    # try:
    _t.from_yaml(yaml_file=exp_path(_t.dirname)+"/range-config.yaml")
    # except Exception as e:
    #     _t.status = ExperimentStatus.MISTAKEN
    #     _t.statusComment = str(e)
    #     return Response(400, f"上传文件有误：{str(e)}", str(e))
    return Response(200, "ok", None)


@app.route("/exp/document", methods=["GET"])
def exp_document():
    uuid = request.args.get("uuid")
    if not uuid:
        return Response(400, "请求有误：请给出容器UUID。", None)
    uuid = parseUUID(uuid, hascrid=False)
    _t = select_exp(uuid)
    if _t is None:
        return Response(400, "请求有误：实验UUID无效。", None)
    return Response(200, "ok", open(_t.document, "r").read())


@app.route("/exp/stop", methods=["GET", "POST"])
def exp_stop():
    uuid = request.args.get("uuid")
    if not uuid:
        return Response(400, "请求有误：请给出实验UUID。", None)
    _t = select_exp(uuid)
    if _t is None:
        return Response(400, "请求有误：实验UUID无效。", None)
    try:
        for i in _t.components:
            if kube_arch in i.config:
                action_from_yaml(yaml_file=i.config[kube_arch],
                                 workdir=settings.RESOURCE_DIR + '/' + _t.dirname,
                                 action="delete")
            elif "all" in i.config:
                action_from_yaml(yaml_file=i.config["all"],
                                 workdir=settings.RESOURCE_DIR + '/' + _t.dirname,
                                 action="delete")
            else:
                # 无需kubectl delete
                pass
        _t.status = ExperimentStatus.STOPPED
        _t.runtime = ExperimentRuntime()
        _t.statusComment = f"于{current_time()}停止"
        return Response(200, "实验已停止", None)
    except Exception as e:
        # print(e)
        _t.status = ExperimentStatus.CRASHED
        # raise e
        _t.statusComment = f"停止时出错:{str(e)}"
        return Response(400, "实验停止失败", str(e))

@app.route("/exp/listcontainer", methods=["GET", "POST"])
def exp_cr_list():
    uuid = request.args.get("uuid")
    if not uuid:
        # 获取全部容器
        crlist = []
        for _t in explist:
            # print(_t.dict_full())
            for i,_c in enumerate(_t.runtime.components):
                # print(i, _c)
                crlist.append({"label": _t.name + ":" + _c, "value": _t.expUUID + ':' + str(i)})
        return Response(200, "ok", crlist)
    # crid, uuid = parseUUID(uuid, hascrid=True)
    _t = select_exp(uuid)
    if _t is None:
        return Response(400, "请求有误：实验UUID无效。", None)
    return Response(200, "ok", [{"label": j, "value": i} for i,j in enumerate(_t.runtime.components)])

@app.route("/monitor/journal", methods=["GET"])
def monitor_journal():
    uuid = request.args.get("uuid")
    if not uuid:
        return Response(400, "请求有误：请给出容器UUID。", None)
    uuid, crid = parseUUID(uuid, hascrid=True)
    _t = select_exp(uuid)
    if _t is None:
        return Response(400, "请求有误：实验UUID无效。", None)
    try:
        _c = _t.runtime.components[crid]
    except IndexError:
        return Response(400, "请求有误：容器UUID无效。", None)
    return Response(200, "ok", read_pod_log(_c, namespace="default"))


def init():
    global kube_arch
    logging.info("自动导入resource中的实验...")
    uuidlist = set()
    for i in os.listdir(settings.RESOURCE_DIR):
        logging.info(f"导入实验：{i}")
        _t = Experiment(i)
        _t.from_yaml(yaml_file = settings.RESOURCE_DIR+"/"+i+"/range-config.yaml",
                     dirname = i)
        if _t.expUUID in uuidlist:
            logging.warning(f"实验{_t.name}的UUID已被导入过！")
        uuidlist.add(_t.expUUID)
        explist.append(_t)
    if (kube_arch:=get_kube_arch()) =="":
        logging.error("无法连接到集群。")
        logging.warning(f"在无法连接到集群时，部分管理功能仍可使用，但是不能启动实验。")
        # sys.exit(2)
    else:
        logging.info("集群连接成功。")
    if not "linux" in kube_arch:
        logging.error(f"集群是{kube_arch}平台，但是目前还不支持。")
    kube_arch = kube_arch.replace("linux/","")
    logging.info("初始化成功。")


init()
if __name__ == "__main__":
    uvicorn.run("main:app", host = settings.ADDRESS, port = settings.PORT, interface = "wsgi", reload = True, reload_dirs=".", reload_excludes="resources, trash")

