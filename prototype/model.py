import re
import yaml
from enum import Enum, IntEnum
import logging

UUID_REGEX = r"[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}"

class ComponentType(IntEnum):
    UNDEFINED = 0
    DOCKER = 1
    COMPOSE = 2
    KUBERNETES = 3
    VIRTMACHINE = 4
    CUSTOM = 5

class Component():
    ID = 0
    name = ""
    config = ""
    types = ComponentType.UNDEFINED


    def __init__(self, ID, yml_object):
        # print(ID, yml_object, list(yml_object.keys())[0])
        self.ID = ID
        try:
            name = list(yml_object.keys())[0]
            self.name = name
            self.config = yml_object[name]["config"]
            self.types = self.gettype(yml_object[name]["types"])
        except:
            raise ValueError("yaml子模块(Components)读取失败。")

    def gettype(self, typename) -> ComponentType:
        try:
            return ComponentType(typename)
        except:
            if typename == "k8s":
                return ComponentType.KUBERNETES
            elif typename == "docker":
                return ComponentType.DOCKER
            elif typename == "compose":
                return ComponentType.COMPOSE
            elif "virt" in typename:
                return ComponentType.VIRTMACHINE
            else:
                return ComponentType.UNDEFINED

    def dict(self):
        return {"ID": self.ID,
                "name": self.name,
                "config": self.config,
                "types": self.types}


    def check(self, ID, UUID, name, config, types):
        # 原型版暂时不做配置检查提示，配置检查仅用于调试和演示配置检查功能
        assert isinstance(ID, int)
        assert isinstance(UUID, str)
        assert re.match(UUID_REGEX, UUID)
        assert isinstance(name, str)
        assert isinstance(config, str)
        assert isinstance(types, ComponentType) or isinstance(types, int)

class ExperimentStatus(IntEnum):
    NOT_RUNNING = 0
    RUNNING = 1
    STOPPED = 2
    PAUSED = 3
    FAILED = 4
    CRASHED = 5
    MISTAKEN = 6

class Experiment():
    # ID = 0
    expUUID = ""
    name = ""
    author = ""
    tags = []
    desc = ""
    status = ExperimentStatus.NOT_RUNNING # 事实上之后可能会做成 分用户的 状态
    components = []
    attachments = []
    solution = "" # 存文件名，和components.config是一样的

    def __init__(self, name):
        # self.ID = 0
        self.name = name

    def dict(self):
        return {
                # "ID": self.ID,
                "expUUID": self.expUUID,
                "name": self.name,
                "author": self.author,
                "tags": self.tags,
                "desc": self.desc,
                "status": self.status,
                "components": [i.dict() for i in self.components],
                "attachments": self.attachments,
                #"solution": self.solution
                }


    def dict_dump(self):
        return {
                # "ID": self.ID,
                "expUUID": self.expUUID,
                "name": self.name,
                "author": self.author,
                "tags": self.tags,
                "desc": self.desc,
                #"status": self.status,
                "components": self.components,
                "attachments": self.attachments,
                "solution": self.solution
                }


    def dict_full(self):
        return {
                # "ID": self.ID,
                "expUUID": self.expUUID,
                "name": self.name,
                "author": self.author,
                "tags": self.tags,
                "desc": self.desc,
                "status": self.status,
                "components": [i.dict() for i in self.components],
                "attachments": self.attachments,
                "solution": self.solution
                }


    def match(self, name, ID, tags, status):
        if name and name not in self.name:
            return False
        if ID and ID not in self.expUUID:
            return False
        if tags and tags not in self.tags:
            return False
        if status and self.status not in status:
            return False
        return True


    def from_yaml(self, yml_object = {}, yml_file=""):
        if not (yml_object or yml_file):
            raise ValueError("应当指定yml_object或yml_file中的一个。")
        if yml_file and yml_object:
            logging.warn("model.Experiment.from_yaml:应当只指定yml_object或yml_file中的一个。")
            yml_file = ""
        if yml_file:
            with open(yml_file, "r") as f:
                yml_object = yaml.load(f.read(), yaml.SafeLoader)

        # print(yml_object)
        try:
            # self.ID = yml_object["expID"]
            self.expUUID = yml_object["expUUID"]
            self.name = yml_object["name"]
            self.author = yml_object["author"]
            self.tags = yml_object["tags"]
            self.desc = yml_object["desc"]
            self.status = ExperimentStatus.NOT_RUNNING
            # print([yml_object["components"][i] for i in yml_object["components"]])
            self.components = [Component(i, j) for i,j in enumerate(yml_object["components"])]
        except KeyError:
            raise ValueError("传入yaml缺少必要参数，请检查。")
        except TypeError:
            raise RuntimeError("yaml解析失败。")
        try:
            self.attachments = yml_object["attachments"]
        except:
            self.attachments = []


if __name__ == "__main__":
    # a = Component(ID=1, UUID="40ecc6a9-b4a8-4460-8f78-86012dbc2693", name="test1", config="dummy", types=3)
    # print(a)
    b = Experiment("test")
    b.from_yaml(yml_file="resource/range-config.yaml")
    print(b.dict())


