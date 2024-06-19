from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.mysql import VARCHAR
from . import db


class OneDrive(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    access_token: Mapped[VARCHAR] = mapped_column(VARCHAR(4096))
