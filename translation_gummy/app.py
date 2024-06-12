from flask import Flask, request
from dotenv import load_dotenv
import uuid
from tasks.transcribe.api import *

load_dotenv()
app = Flask(__name__)


@app.route("/transcribe", methods=["POST"])
def transcribe():
    content = request.json
    video_url = content["video_url"]
    if not isinstance(video_url, list):
        return {"error": "video_url must be a list"}
    kaggle_username = content.get("kaggle_username", None)
    kaggle_key = content.get("kaggle_key", None)
    task_id = str(uuid.uuid4())
    try:
        run_kaggle_kernel(
            video_url=video_url, kaggle_username=kaggle_username, kaggle_key=kaggle_key
        )
    except Exception as e:
        return {"error": str(e)}
    return {"task_id": task_id, "status": "running"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9000)
