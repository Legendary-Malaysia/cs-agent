from fastapi.testclient import TestClient
import requests
from main import app
import sys
import os
import pytest
import json
import httpx
import asyncio

# Add the 'src' directory to the Python path to resolve csagent module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from csagent.configuration import Configuration

BASE_URL = os.getenv("BASE_URL")

client = TestClient(app)


def test_health_check():
    """Tests the health check endpoint."""
    response = client.get("/")
    print("################# response: ", response)
    assert response.status_code == 200
    assert response.json() == "The health check is successful."


@pytest.mark.skip(reason="Run this test manually")
def test_health_check_deployed():
    """Tests the health check endpoint on deployed app."""
    response = requests.get(f"{BASE_URL}/")
    print("################# response: ", response, BASE_URL)
    print("################# response.json(): ", response.json())
    assert response.status_code == 200
    assert response.json() == "The health check is successful."


@pytest.mark.skip(reason="Run this test manually")
def test_run_supervisor():
    """Tests the supervisor endpoint."""
    config = {
        "configurable": {
            "thread_id": "test_thread_id",
            "language": "en",
            "model": "LongCat-Flash-Chat",
        }
    }
    response = client.post(
        "/supervisor",
        json={"messages": "Where can I buy spirit?", "config": config},
    )
    print("################# response: ", response)
    print("################# response.json(): ", response.json()["response"])
    # assert response.status_code == 200
    # You might want to add more specific assertions here based on the expected output
    # assert isinstance(response.json(), dict)


@pytest.mark.skip(reason="Run this test manually")
async def test_run_supervisor_stream():
    """Tests the supervisor endpoint."""

    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            "http://localhost:8000/supervisor",
            json={
                "messages": "Where can I buy spirit?",
                "config": Configuration().model_dump(),
            },
            timeout=30.0,
        ) as response:
            # if response.status_code == 200:
            async for line in response.aiter_lines():
                if line and line.startswith("data: "):
                    json_str = line.replace("data: ", "")
                    data = json.loads(json_str)
                    print(f"Node: {data['node']} | Content: {data['content']}")


@pytest.mark.skip(reason="Run this test manually")
def test_run_supervisor_deployed():
    """Tests the supervisor endpoint on deployed app."""
    config = {
        "configurable": {
            "thread_id": "test_thread_id",
            "language": "en",
            "model": "LongCat-Flash-Chat",
        }
    }
    response = requests.post(
        f"{BASE_URL}/supervisor",
        json={
            "messages": [{"role": "user", "content": "Where can I buy spirit?"}],
            "config": config,
        },
    )
    print("################# response: ", response)
    print("################# response.json(): ", response.json()["response"])


if __name__ == "__main__":
    # test_health_check()
    # test_health_check_deployed()
    # test_run_supervisor()
    # test_run_supervisor_deployed()
    # test_run_supervisor_stream()
    asyncio.run(test_run_supervisor_stream())
