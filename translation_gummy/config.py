import os


class Config:
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{os.environ['MYSQL_USER']}:"
        f"{os.environ['MYSQL_PASSWORD']}@"
        f"{os.environ['MYSQL_HOST']}/"
        f"{os.environ['MYSQL_DB']}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
