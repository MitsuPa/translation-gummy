from calendar import timegm
import datetime
from flask import Flask, request, g
from dotenv import load_dotenv
from sqlalchemy import func
from model import db, Task, Url, KaggleUser
from task.transcribe.api import *
from utils import jwt_manager, onedrive
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
        with db.session.begin():
            request_transcribe(task, video_url)
    except Exception as e:
        app.log_exception(e)
    return {"task_id": task_id, "status": task.status}


@app.before_request
def before_request():
    need_auth = request.path in ["/transcribe/callback", "/upload"]
    if not need_auth:
        return
    jwt = request.headers.get("Authorization")
    if not jwt:
        return {"error": "Authorization header is missing"}, 401
    try:
        payload = jwt_manager.decode(jwt, options={"verify_exp": False})
        with db.session.begin():
            g.task = db.session.query(Task).filter_by(uuid=payload["task_id"]).first()
        # if timegm(datetime.datetime.now(tz=datetime.timezone.utc).utctimetuple()) > int(
        #     payload["exp"]
        # ):
        #     raise Exception("Token has expired")
    except Exception as e:
        return {"error": str(e)}, 401


def request_transcribe(task: Task, video_url: list[str]):
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
            api_jwt=jwt_manager.encode({"task_id": task.uuid}),
            api_url=os.environ["API_BASE_URL"],
        )
        kaggle_user.available = False
        kaggle_user.updated_at = func.now()
        task.kaggle_user_id = kaggle_user.id
        task.status = "running"


def get_top_pending_task():
    task = (
        db.session.query(Task)
        .filter_by(status="pending")
        .order_by(Task.created_at.asc())
        .with_for_update()
        .limit(1)
        .first()
    )
    if task:
        request_transcribe(task, [url.url for url in task.url])


@app.route("/transcribe/callback", methods=["POST"])
def transcribe_callback():
    content = request.json
    if "status" not in content:
        return {"error": "status is missing"}
    with db.session.begin():
        if g.task.status != "running":
            return {"error": "Task is not running"}
        status = content["status"]
        g.task.status = status
        g.task.updated_at = func.now()
        g.task.kaggle_user.available = True
    try:
        with db.session.begin():
            get_top_pending_task()
    except Exception as e:
        app.log_exception(e)
    return {"task_id": g.task.uuid, "status": g.task.status}


@app.route("/upload", methods=["POST"])
def upload():
    content = request.json
    if "file" not in content:
        return {"error": "file is missing"}
    with db.session.begin():
        task_id = g.task.uuid
    folder_path = f"{os.environ['UPLOAD_FOLDER']}/{task_id}"
    email = os.environ["ONEDRIVE_EMAIL"]
    folder_id = onedrive.get_item(folder_path, onedrive.get_access_token(), email).get(
        "id", None
    )
    if not folder_id:
        folder_id = onedrive.create_folder(
            folder_path, onedrive.get_access_token(), email
        )["id"]
    return {
        "upload_url": onedrive.create_upload_session(
            folder_id, content["file"], onedrive.get_access_token, email
        )["uploadUrl"]
    }


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=9000)
