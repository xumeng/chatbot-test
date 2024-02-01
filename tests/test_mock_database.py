import asyncio
from beanie import init_beanie
from fastapi.testclient import TestClient
from httpx import AsyncClient
import pytest

from models.messages import Messages
from tests.conftest import mock_no_authentication


class TestMockAuthentication:
    @classmethod
    def setup_class(cls):
        mock_no_authentication()

    @pytest.mark.anyio
    async def test_mock_databases(self, client_test: AsyncClient):
        Messages(user_name="aa", type="ai", text="hello", ctime=1, mtime=1).create()

        response = await client_test.get("student")

        assert response.status_code == 200
