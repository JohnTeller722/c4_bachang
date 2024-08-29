import re
import yaml
import uuid
from enum import Enum, IntEnum
import logging
from config import settings

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


    def __init__(self, ID, yaml_object):
        # print(ID, yaml_object, list(yaml_object.keys())[0])
        self.ID = ID
        try:
            name = list(yaml_object.keys())[0]
            self.name = name
            self.config = yaml_object[name]["config"]
            self.types = self.gettype(yaml_object[name]["types"])
            if self.types == ComponentType.DOCKER or self.types == ComponentType.COMPOSE:
                logging.warning(f"组件类型{self.types}暂未支持！")
            if self.types == ComponentType.CUSTOM:
                logging.warning(f"自定义组件暂未支持！")
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

class ExperimentRuntime():
    port = []
    components = []

    def __init__(self):
        pass


class Experiment():
    # ID = 0
    expUUID = ""
    name = ""
    author = ""
    tags = []
    desc = ""
    status = ExperimentStatus.NOT_RUNNING # 事实上之后可能会做成 分用户的 状态
    statusComment = "实验尚未运行"
    components = []
    dirname = ""
    attachments = []
    document = "" # 同下
    # solution = "" # 存文件名，和components.config是一样的
    runtime = ExperimentRuntime() # 运行时信息

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
                "statusComment": self.statusComment, 
                "attachments": self.attachments,
                "document": self.document,
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
                # "status": self.status,
                # "status"
                "components": self.components,
                "attachments": self.attachments,
                "document": self.document,
                # "solution": self.solution
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
                # "solution": self.solution
                "document": self.document,
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

    def updateUUID(self, UUID=""):
        if UUID:
            self.expUUID = UUID
        else:
            self.expUUID = str(uuid.uuid4())


    def from_yaml(self, yaml_object = {}, yaml_file="", dirname=""):
        if not (yaml_object or yaml_file):
            raise ValueError("应当指定yaml_object或yaml_file中的一个。")
        if yaml_file and yaml_object:
            logging.warning("model.Experiment.from_yaml:应当只指定yaml_object或yaml_file中的一个。")
            yaml_file = ""
        if yaml_file:
            with open(yaml_file, "r") as f:
                yaml_object = yaml.load(f.read(), yaml.SafeLoader)

        # print(yaml_object)
        if dirname:
            self.dirname = dirname
        try:
            self.name = yaml_object["name"]
            if self.expUUID and self.expUUID != yaml_object["expUUID"]:
                logging.warning(f"导入实验时发现UUID不一致，原来是{self.expUUID}而现在是{yaml_object['expUUID']}")
            self.expUUID = yaml_object["expUUID"]
            self.status = ExperimentStatus.NOT_RUNNING
            self.statusComment = "实验尚未运行"
            if yaml_object["version"] < settings.MINIMUM_RANGE_CONFIG_VERSION:
                logging.error(f"实验{self.name}配置版本({yaml_object['version']})低于要求版本{settings.MINIMUM_RANGE_CONFIG_VERSION}")
                self.status = ExperimentStatus.MISTAKEN
                self.statusComment = f"实验配置版本({yaml_object['version']})低于要求版本{settings.MINIMUM_RANGE_CONFIG_VERSION}"
            elif yaml_object["version"] < settings.SUGGEST_RANGE_CONFIG_VERSION:
                logging.warning(f"实验{self.name}配置版本({yaml_object['version']})低于推荐版本{settings.MAXINUM_RANGE_CONFIG_VERSION}")
            elif yaml_object["version"] > settings.MAXINUM_RANGE_CONFIG_VERSION:
                logging.error(f"实验{self.name}配置版本({yaml_object['version']})高于支持版本{settings.MAXINUM_RANGE_CONFIG_VERSION}")
                self.statusComment = f"实验配置版本({yaml_object['version']})高于要求版本{settings.MAXINUM_RANGE_CONFIG_VERSION}"
                self.status = ExperimentStatus.MISTAKEN
            # self.ID = yaml_object["expID"]
            self.author = yaml_object["author"]
            self.tags = yaml_object["tags"]
            self.desc = yaml_object["desc"]
            self.document = yaml_object["document"]
            # print([yaml_object["components"][i] for i in yaml_object["components"]])
            self.components = [Component(i, j) for i,j in enumerate(yaml_object["components"])]
        except KeyError:
            raise ValueError("传入yaml缺少必要参数，请检查。")
        except TypeError:
            raise RuntimeError("yaml解析失败。")
        except ValueError as e:
            raise e
        except Exception as e:
            print(e)
            raise e
        try:
            self.attachments = yaml_object["attachments"]
        except:
            self.attachments = []


if __name__ == "__main__":
    # a = Component(ID=1, UUID="40ecc6a9-b4a8-4460-8f78-86012dbc2693", name="test1", config="dummy", types=3)
    # print(a)
    b = Experiment("test")
    b.from_yaml(yaml_file="resource/Flask SSTI/range-config.yaml")
    print(b.dict())


