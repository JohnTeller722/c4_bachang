from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List,TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from .task import Task

db = SQLAlchemy()

class ExperimentStatus(Enum):
    RUNNING = 1
    STOPPED = 2
    PAUSED = 3
    NOT_RUNNING = 4
    CRASHED = 5
    FAILED = 6
    MISTAKEN = 7

class Experiment(db.Model):
    __tablename__ = 'experiments'
    
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    expUUID: Mapped[str] = mapped_column(db.String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    tags: Mapped[str] = mapped_column(db.Text)  # 存储为逗号分隔的字符串
    desc: Mapped[str] = mapped_column(db.Text)
    author: Mapped[str] = mapped_column(db.String(255))
    version: Mapped[str] = mapped_column(db.String(50))
    status: Mapped[int] = mapped_column(db.Integer)  # 使用数值enum表示状态
    
    tasks: Mapped[List['Task']] = relationship('Task', back_populates='experiment')

    def to_dict(self):
        return {
            "expId": self.id,
            "expUUID": self.expUUID,
            "name": self.name,
            "tag": self.tags.split(',') if self.tags else [],
            "desc": self.desc,
            "author": self.author,
            "version": self.version,
            "status": ExperimentStatus(self.status).name.lower()
        }