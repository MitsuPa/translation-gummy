import datetime
import jwt
import os


def encode(data: dict) -> str:
    data["exp"] = datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(
        minutes=int(os.environ.get("JWT_EXPIRATION_MINUTES", 5))
    )
    return jwt.encode(data, os.environ["JWT_SECRET"], algorithm="HS256")


def decode(token: str) -> dict:
    return jwt.decode(token, os.environ["JWT_SECRET"], algorithms=["HS256"])
