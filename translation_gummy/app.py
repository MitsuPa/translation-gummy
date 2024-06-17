from flask import Flask, request
from dotenv import load_dotenv
from sqlalchemy import func
from model import db, Task, Url, KaggleUser
import uuid

load_dotenv()
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)


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
            kaggle_user.available = False
            kaggle_user.updated_at = func.now()
            task.kaggle_user_id = kaggle_user.id
            task.status = "running"
    return {"task_id": task.uuid, "status": task.status}


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=9000)
