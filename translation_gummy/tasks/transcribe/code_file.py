commands: list[str] = []
import subprocess
import os

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


for command in commands:
    result = run_command(command)
    if result.returncode != 0:
        raise Exception(f"Command failed: {command}")
