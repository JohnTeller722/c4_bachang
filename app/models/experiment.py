from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List,TYPE_CHECKING

if TYPE_CHECKING:
    from .task import Task

db = SQLAlchemy()

class Experiment(db.Model):
    __tablename__ = 'experiments'
    
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    expUUID: Mapped[str] = mapped_column(db.String(255), unique=True, nullable=False)
    type: Mapped[int] = mapped_column(db.Integer)
    status: Mapped[str] = mapped_column(db.String(50))
    config: Mapped[str] = mapped_column(db.Text)
    
    tasks: Mapped[List['Task']] = relationship('Task', back_populates='experiment')