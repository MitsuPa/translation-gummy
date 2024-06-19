import os
from dotenv import load_dotenv
import tempfile
import json
from pathlib import Path
import os
from .gen_cmd import *


if os.getenv("KAGGLE_CONFIG_DIR") is None:
    with tempfile.TemporaryDirectory() as tmpdirname:
        os.environ["KAGGLE_CONFIG_DIR"] = tmpdirname
os.environ["KAGGLE_USERNAME"] = os.getenv("KAGGLE_USERNAME", "example")
os.environ["KAGGLE_KEY"] = os.getenv("KAGGLE_KEY", "example")
from kaggle.api.kaggle_api_extended import KaggleApi

api = KaggleApi()


kernel_metadata = {
    "id": "",
    "title": "Translation Gummy",
    "code_file": "code_file.py",
    "language": "python",
    "kernel_type": "script",
    "is_private": True,
    "enable_gpu": True,
    "enable_tpu": False,
    "enable_internet": True,
    "keywords": [],
    "dataset_sources": [],
    "kernel_sources": [],
    "competition_sources": [],
    "model_sources": [],
}


def run_kaggle_kernel(
    video_url: list[str],
    kaggle_username: str,
    kaggle_key: str,
    max_files: int = 1,
    api_jwt: str = "",
    api_url: str = "",
) -> None:
    with tempfile.TemporaryDirectory() as tmpdirname:
        kernel_metadata["id"] = f"{kaggle_username}/translation-gummy"
        with open(os.path.join(tmpdirname, "kernel-metadata.json"), "w") as new_f:
            json.dump(kernel_metadata, new_f)
        with open(Path(__file__).with_name(kernel_metadata["code_file"]), "r") as f:
            lines = f.readlines()
            commands = gen_commands(
                [gen_yt_dlp_command(url) for url in video_url],
                gen_whisper_command(),
                gen_count_video_files_command(max_files),
            )
            lines[0] = f"commands: list[str] = {commands}\n"
            lines[1] = f'api_jwt: str = "{api_jwt}"\n'
            lines[2] = f'api_url: str = "{api_url}"\n'
        with open(os.path.join(tmpdirname, kernel_metadata["code_file"]), "w") as new_f:
            new_f.writelines(lines)
        authenticate(kaggle_username, kaggle_key)
        result = api.kernels_push(tmpdirname)
        if result is None or result.error:
            raise Exception(result)


def check_kaggle_status(kernel: str, kaggle_username: str, kaggle_key: str) -> str:
    """
    Check the status of a Kaggle kernel.

    Args:
        kernel (str): The name or ID of the Kaggle kernel.
        kaggle_username (str): The Kaggle username.
        kaggle_key (str): The Kaggle API key.

    Returns:
        str: The status of the Kaggle kernel. Possible values are:
            - "complete" if the kernel has completed running.
            - "error" if there was an error running the kernel.
            - "running" if the kernel is currently running.
            - The error message if there was an error executing the command.
    """
    authenticate(kaggle_username, kaggle_key)
    return api.kernels_status_cli(kernel)["status"]


def authenticate(kaggle_username: str, kaggle_key: str) -> None:
    """
    Authenticates the user with Kaggle API.

    Args:
        kaggle_username (str): The Kaggle username.
        kaggle_key (str): The Kaggle API key.

    Returns:
        None
    """
    os.environ["KAGGLE_USERNAME"] = kaggle_username
    os.environ["KAGGLE_KEY"] = kaggle_key
    api.authenticate()
