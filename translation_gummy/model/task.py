from typing import List, Literal, get_args
from sqlalchemy import Boolean, func
from sqlalchemy.dialects.mysql import CHAR, ENUM, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
from . import db


TaskStatus = Literal["pending", "running", "completed", "failed"]


class Task(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid: Mapped[CHAR] = mapped_column(CHAR(36), unique=True)
    status: Mapped[CHAR] = mapped_column(
        ENUM(
            *get_args(TaskStatus),
            name="task_status",
            create_constraint=True,
            validate_strings=True,
        ),
        server_default="pending",
    )
    kaggle_user_id: Mapped[int] = mapped_column(
        db.ForeignKey("kaggle_user.id"), nullable=True
    )
    created_at: Mapped[int] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[int] = mapped_column(TIMESTAMP, server_default=func.now())

    url: Mapped[List["Url"]] = db.relationship("Url", back_populates="task")


class Url(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(db.ForeignKey("task.id"))
    url: Mapped[CHAR] = mapped_column(CHAR(255))

    task: Mapped["Task"] = db.relationship("Task", back_populates="url")


class KaggleUser(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[CHAR] = mapped_column(CHAR(255), primary_key=True)
    available: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[int] = mapped_column(TIMESTAMP, server_default=func.now())
