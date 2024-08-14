from __future__ import annotations # 允许循环类型标注
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List
from enum import StrEnum
import uuid

db = SQLAlchemy()

class ExperimentStatus(StrEnum):
    RUNNING = "运行中"
    STOPPED = "已停止"
    PAUSED = "已暂停"
    NOT_RUNNING = "未运行"
    CRASHED = "已崩溃"
    FAILED = "启动失败"
    MISTAKEN = "配置有误"

class Task(db.Model): # 重新规定Task表示正在运行的实验
    __tablename__ = 'tasks'
    
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
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
    
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    expUUID: Mapped[str] = mapped_column(db.String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    tags: Mapped[str] = mapped_column(db.Text)  # 存储为逗号分隔的字符串
    desc: Mapped[str] = mapped_column(db.Text)
    author: Mapped[str] = mapped_column(db.String(255))
    version: Mapped[str] = mapped_column(db.String(50))
    status: Mapped[str] = mapped_column(db.String(32))  # WARN:使用字符串enum表示状态
    
    # tasks: Mapped[List['Task']] = relationship(Task, back_populates='experiment')

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

