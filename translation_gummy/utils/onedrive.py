import inspect
import os
import requests
from urllib.parse import quote
from functools import wraps
from model import db, OneDrive


BASE_URL = "https://graph.microsoft.com"


def get_access_token():
    with db.session.begin():
        onedrive = db.session.query(OneDrive).first()
        return onedrive.access_token


def retry_on_error(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        arg_names = inspect.getfullargspec(func).args
        kwargs.update(dict(zip(arg_names, args)))
        response_json = func(**kwargs)
        if (
            "error" in response_json
            and response_json["error"]["code"] == "InvalidAuthenticationToken"
        ):
            new_token = refresh_token(
                os.environ["ONEDRIVE_CLIENT_ID"],
                os.environ["ONEDRIVE_CLIENT_SECRET"],
                os.environ["ONEDRIVE_TENANT_ID"],
            )["access_token"]
            kwargs["access_token"] = new_token
            with db.session.begin():
                onedrive = db.session.query(OneDrive).first()
                onedrive.access_token = new_token
            response_json = func(**kwargs)
        return response_json

    return wrapper


def refresh_token(client_id, client_secret, tenant_id):
    response = requests.post(
        f"https://login.microsoftonline.com/{tenant_id}/oauth2/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
            "resource": BASE_URL + "/",
            "scope": BASE_URL + "/.default",
        },
    )
    return response.json()


@retry_on_error
def get_item(path, access_token, email):
    path = quote(path)
    if path != "":
        if path.startswith("/"):
            path = path[1:]
        path = f":/{path}"
    response = requests.get(
        BASE_URL + f"/v1.0/users/{email}/drive/root{path}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    return response.json()


@retry_on_error
def create_upload_session(item_id, file_name, access_token, email):
    file_name = quote(file_name)
    response = requests.post(
        BASE_URL
        + f"/v1.0/users/{email}/drive/items/{item_id}:/{file_name}:/createUploadSession",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
    )
    return response.json()


@retry_on_error
def create_folder(folder_name, access_token, email):
    folder_name = quote(folder_name)
    if folder_name.startswith("/"):
        folder_name = folder_name[1:]
    response = requests.patch(
        BASE_URL + f"/v1.0/users/{email}/drive/root:/{folder_name}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json={
            "folder": {},
            "@microsoft.graph.conflictBehavior": "fail",
        },
    )
    return response.json()


@retry_on_error
def move_item(item_id, folder_id, access_token, email):
    response = requests.patch(
        BASE_URL + f"/v1.0/users/{email}/drive/items/{item_id}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json={
            "parentReference": {"id": folder_id},
        },
    )
    return response.json()
