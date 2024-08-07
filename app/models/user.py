from flask_security import UserMixin, RoleMixin
from flask_sqlalchemy import SQLAlchemy
from typing import List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

db = SQLAlchemy()
ph = PasswordHasher()

roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'))
)

class Role(db.Model, RoleMixin):
    id: Mapped[int] = mapped_column(db.Integer(), primary_key=True)
    name: Mapped[str] = mapped_column(db.String(80), unique=True)
    description: Mapped[str] = mapped_column(db.String(255))

class User(db.Model, UserMixin):
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    email: Mapped[str] = mapped_column(db.String(255), unique=True)
    password: Mapped[str] = mapped_column(db.String(255))
    active: Mapped[bool] = mapped_column(db.Boolean())
    confirmed_at = mapped_column(db.DateTime())
    fs_uniquifier: Mapped[str] = mapped_column(db.String(64), unique=True, nullable=False) 
    # 用户角色
    roles: Mapped[List[Role]] = relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))
    # 用户头像
    avatar: Mapped[str] = mapped_column(db.String(255))  
    # 用户经验
    experience: Mapped[int] = mapped_column(db.Integer, default=0)  
    # 用户等级
    level: Mapped[int] = mapped_column(db.Integer, default=0)  

    def set_password(self, password: str) -> None:
        self.password = ph.hash(password)

    def check_password(self, password: str) -> bool:
        try:
            return ph.verify(self.password, password)
        except VerifyMismatchError:
            return False