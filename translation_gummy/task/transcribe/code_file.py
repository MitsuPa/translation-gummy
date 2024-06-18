commands: list[str] = []
callback_jwt: str = ""
callback_url: str = ""
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


status = "completed"
try:
    for command in commands:
        result = run_command(command)
        if result.returncode != 0:
            status = "failed"
            raise Exception(f"Command failed: {command}")
finally:
    if callback_url != "":
        requests.post(
            callback_url,
            headers={
                "Authorization": f"{callback_jwt}",
                "Content-Type": "application/json",
            },
            json={"status": status},
        )
    log.close()
    if status == "failed":
        exit(1)
