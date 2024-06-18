from flask import Flask, redirect, request
from dotenv import load_dotenv
from sqlalchemy import func
from model import db, Task, Url, KaggleUser
from task.transcribe.api import *
from utils import jwt_manager
import uuid

load_dotenv()
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
KAGGLE_KEYS = dict(
    pair.split(":") for pair in os.environ["KAGGLE_USERNAMES_AND_KEYS"].split(",")
)


@app.route("/transcribe", methods=["POST"])
def transcribe():
    content = request.json
    video_url = content["video_url"]
    if not isinstance(video_url, list):
        return {"error": "video_url must be a list"}
    task_id = str(uuid.uuid4())
    with db.session.begin():
        task = Task(uuid=task_id)
        db.session.add(task)
        db.session.flush()
        urls = [Url(task_id=task.id, url=url) for url in video_url]
        db.session.add_all(urls)
    try:
        request_transcribe(task, video_url)
    except Exception as e:
        app.log_exception(e)
    return {"task_id": task_id, "status": task.status}


@app.before_request
def before_request():
    need_auth = request.path in ["/transcribe/callback"]
    if not need_auth:
        return
    jwt = request.headers.get("Authorization")
    if not jwt:
        return {"error": "Authorization header is missing"}, 401
    try:
        jwt_manager.decode(jwt)
    except Exception as e:
        return {"error": str(e)}, 401


def request_transcribe(task: Task, video_url: list[str]):
    with db.session.begin():
        kaggle_user = (
            db.session.query(KaggleUser)
            .filter_by(available=True)
            .order_by(KaggleUser.updated_at.asc())
            .with_for_update()
            .limit(1)
            .first()
        )
        if kaggle_user:
            run_kaggle_kernel(
                video_url,
                kaggle_username=kaggle_user.username,
                kaggle_key=KAGGLE_KEYS[kaggle_user.username],
                max_files=os.environ.get("MAX_FILES", 1),
                callback_jwt=jwt_manager.encode({"task_id": task.uuid}),
                callback_url=os.environ["API_BASE_URL"] + "transcribe/callback",
            )
            kaggle_user.available = False
            kaggle_user.updated_at = func.now()
            task.kaggle_user_id = kaggle_user.id
            task.status = "running"


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=9000)
