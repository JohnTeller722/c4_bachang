from __future__ import annotations
from logging import warn # 允许循环类型标注
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from typing import List
from enum import StrEnum, Enum
import uuid
from sqlalchemy.orm.relationships import foreign
import yaml

db = SQLAlchemy()

class ExperimentStatus(StrEnum):
    RUNNING = "运行中"
    STOPPED = "已停止"
    PAUSED = "已暂停"
    NOT_RUNNING = "未运行"
    CRASHED = "已崩溃"
    FAILED = "启动失败"
    MISTAKEN = "配置有误"

class ExperimentComponentType(Enum):
    UNDEFINED = 0
    DOCKER = 1
    COMPOSE = 2
    KUBERNETES = 3
    VIRTMACHINE = 4
    CUSTOM = 5

class ExperimentComponent(db.Model):
    __tablename__ = "experimentcomponents"
    
    # ID: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    UUID: Mapped[str] = mapped_column(db.String(255), primary_key=True, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(db.String(255))
    Type: Mapped[int] = mapped_column(db.Integer)
    config: Mapped[str] = mapped_column(db.String(512))

class Task(db.Model): # 重新规定Task表示正在运行的实验...吗？
    # NOTE: 暂不实现
    __tablename__ = 'tasks'
    
    ID: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    owner: Mapped[str] = mapped_column(db.String(256)) # TODO:换为User类型
    taskUUID: Mapped[str] = mapped_column(db.String(255), unique=True, nullable=False)
    expUUID: Mapped[str] = mapped_column(db.String(255), nullable=False)
    status: Mapped[str] = mapped_column(db.String(32))
    
    # experiment: Mapped['Experiment'] = relationship(Experiment, back_populates='tasks')

    def __init__(self, exp: Experiment, owner: str):
        self.id = 0 # 等待程序分配
        self.owner = owner
        self.taskUUID = str(uuid.uuid4())
        self.expUUID = exp.expUUID

    def to_dict(self) -> dict:
        return {
            "exp": {
                # "expId": self.experiment.id,
                # "expUUID": self.experiment.expUUID,
                # "name": self.experiment.name,
            },
            "taskID": self.taskUUID,
            "status": self.status
        }

class Experiment(db.Model):
    __tablename__ = 'experiments'
    
    ID: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    expUUID: Mapped[str] = mapped_column(db.String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    tags: Mapped[str] = mapped_column(db.Text)  # 存储为逗号分隔的字符串
    desc: Mapped[str] = mapped_column(db.Text)
    author: Mapped[str] = mapped_column(db.String(255))
    version: Mapped[str] = mapped_column(db.String(50))
    status: Mapped[str] = mapped_column(db.String(32))  # WARN:使用字符串enum表示状态
    attachments: Mapped[str] = mapped_column(db.String(4096))
    ports: Mapped[str] = mapped_column(db.String(96)) 
    
    # tasks: Mapped[List['Task']] = relationship(Task, back_populates='experiment')
    #componentUUID = mapped_column(db.String(255), ForeignKey("experimentcomponent.UUID"))
    #component: Mapped[List[ExperimentComponent]] = relationship(ExperimentComponent, foreign_keys=[componentUUID])


    def __init__(self, name):
        self.name = name
        self.id = 0 # 等待程序分配
        self.expUUID = str(uuid.uuid4())

    def to_dict(self):
        return {
            "expId": self.id,
            "expUUID": self.expUUID,
            "name": self.name,
            "tag": self.tags.split(',') if self.tags else [],
            "desc": self.desc,
            "author": self.author,
            "version": self.version,
            "status": self.status
        }

    def from_yaml(self, yml_file:str = "", yml_object:dict = {}):
        if not (yml_file or yml_object):
            raise ValueError("Either yml_file or yml_object should be specified.")
        if yml_file and yml_object:
            warn("Both yml_file and yml_object is specified, using yml_object instead.")
            yml_file = ""

        if yml_file:
            with open(yml_file, "r", encoding="utf-8") as f:
                yml_object = yaml.load(f.read(), yaml.SafeLoader)
        self.id = yml_object["expId"]
        self.expUUID = yml_object["expUUID"]
        self.name = yml_object["name"]
        self.tags = ','.join(yml_object["tag"])
        self.desc = yml_object["desc"]
        self.author = yml_object["author"]
        print(yml_object)
        for i in yml_object["component"]:
            _t = ExperimentComponent()
            _t.UUID = i["uuid"]
            _t.name = i["name"]
            #self.component.append(_t)
            pass



