from fastapi.testclient import TestClient
import requests
from main import app
import sys
import os
import pytest
import json

# Add the 'src' directory to the Python path to resolve csagent module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv

load_dotenv()
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
def test_run_supervisor_stream_conversation():
    url = "http://127.0.0.1:8000/supervisor"
    payload = {
        "messages": [
            {"role": "user", "content": "Hello, how are you? My name is John Doe"},
            {
                "role": "assistant",
                "content": "I'm doing well, thank you! How can I help you today?",
            },
            {"role": "user", "content": "What is my name?"},
        ],
        "config": {
            "thread_id": "test_thread_id",
            "language": "en",
            "model": "LongCat-Flash-Chat",
        },
    }

    try:
        response = requests.post(url, json=payload, stream=True)
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                decoded_line = line.decode("utf-8")
                if decoded_line.startswith("data: "):
                    content = json.loads(decoded_line[6:])
                    print(
                        f"Node: {content.get('node')}, Content: {content.get('content')}"
                    )

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    # test_health_check()
    # test_health_check_deployed()
    test_run_supervisor_stream_conversation()
