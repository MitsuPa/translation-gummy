commands: list[str] = []
api_jwt: str = ""
api_url: str = ""
import subprocess
import os
import requests

log = open("log.txt", "w")


def run_command(
    command: str,
    env: dict[str, str] = os.environ.copy(),
) -> subprocess.CompletedProcess:
    return subprocess.run(
        command,
        text=True,
        shell=True,
        stdout=log,
        stderr=log,
        env=env,
    )


def upload_file(upload_url, file_path):
    jsons = []
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(10 * 1024 * 1024)
            if not chunk:
                break
            response = requests.put(
                upload_url,
                data=chunk,
                headers={
                    "Content-Length": str(len(chunk)),
                    "Content-Range": f"bytes {f.tell() - len(chunk)}-{f.tell() - 1}/{os.path.getsize(file_path)}",
                },
            )
            jsons.append(response.json())
    return jsons


status = "completed"
try:
    for command in commands:
        result = run_command(command)
        if result.returncode != 0:
            status = "failed"
            raise Exception(f"Command failed: {command}")
    for file in os.listdir("video"):
        upload_url = requests.post(
            f"{api_url}upload",
            headers={
                "Authorization": f"{api_jwt}",
                "Content-Type": "application/json",
            },
            json={"file": file},
        ).json()["upload_url"]
        upload_file(upload_url, f"video/{file}")
finally:
    if api_url != "":
        requests.post(
            f"{api_url}transcribe/callback",
            headers={
                "Authorization": f"{api_jwt}",
                "Content-Type": "application/json",
            },
            json={"status": status},
        )
    log.close()
    if status == "failed":
        exit(1)
