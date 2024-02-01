from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient

from models.messages import Messages

# from app import app
from ..app import app

client = TestClient(app)


@app.get("/")
def hello():
    return "hello world"


def test_svc_ok():
    response = client.get("/")
    assert response.status_code == 200


# @pytest.mark.anyio
def test_db(client_test: AsyncClient):
    Messages(user_name="aa", type="ai", text="hello", ctime=1, mtime=1).create()
    # rets = retrieve_messages("aa", 2)
    # assert len(rets) == 1
