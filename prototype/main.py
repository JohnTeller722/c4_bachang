import os
import math
import logging
from model import Experiment
from flask import Flask, request
from utils import write_exp

app = Flask(__name__)

explist = []


LOGFORMAT = "[%(asctime)s] [%(levelname)s] <%(threadName)s> %(message)s"
logging.basicConfig(format=LOGFORMAT, level = 1)

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


def init():
    logging.info("自动导入resource中的实验...")
    for i in os.listdir("./resource"):
        logging.info(f"导入实验：{i}")
        _t = Experiment(i)
        _t.from_yaml(yml_file = "./resource/"+i+"/range-config.yaml")
        explist.append(_t)


if __name__ == "__main__":
    init()
    app.run(debug=True)
