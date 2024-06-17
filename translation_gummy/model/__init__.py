from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base, engine_options={"pool_size": 1})

from model.task import Task, Url, KaggleUser
