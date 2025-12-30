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
def test_run_supervisor_stream_conversation(payload: dict):
    url = f"{BASE_URL}/supervisor"
    headers = {
        "X-API-KEY": os.getenv("CSAGENT_API_KEY", ""),
    }

    received_messages = []
    completion_received = False

    try:
        response = requests.post(
            url, json=payload, headers=headers, stream=True, timeout=60
        )
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                decoded_line = line.decode("utf-8")
                if decoded_line.startswith("data: "):
                    try:
                        content = json.loads(decoded_line[6:])

                        # Check for completion event
                        if content.get("event") == "done":
                            completion_received = True
                            print("Stream completed successfully")
                            break

                        # Check for errors
                        if "error" in content:
                            print(f"Error received: {content.get('error')}")
                            pytest.fail(
                                f"Server returned error: {content.get('error')}"
                            )

                        # Process normal messages
                        node = content.get("node")
                        message_content = content.get("content")

                        if node and message_content:
                            received_messages.append(content)
                            print(f"Node: {node}, Content: {message_content}")

                    except json.JSONDecodeError as e:
                        print(f"Failed to decode JSON: {decoded_line}, Error: {e}")

        # Assertions
        assert completion_received, "Stream did not complete with 'done' event"
        assert len(received_messages) > 0, "No messages received from stream"
        print(f"\nTotal messages received: {len(received_messages)}")
    except requests.exceptions.Timeout:
        pytest.fail("Request timed out")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {e}")


def test_supervisor_missing_api_key():
    """Tests that the endpoint requires an API key."""
    payload = {
        "messages": [{"role": "user", "content": "Hello"}],
        "config": {},
    }
    response = client.post("/supervisor", json=payload)
    assert response.status_code == 401


if __name__ == "__main__":
    # test_health_check()
    # test_health_check_deployed()
    payload_stream = {
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
    payload_product = {
        "messages": [
            {"role": "user", "content": "Hello, how are you? My name is John Doe"},
            {
                "role": "assistant",
                "content": "I'm doing well, thank you! How can I help you today?",
            },
            {"role": "user", "content": "Tell me about one product"},
        ],
        "config": {
            "thread_id": "test_thread_id",
            "language": "en",
            "model": "LongCat-Flash-Chat",
        },
    }
    payload_location = {
        "messages": [
            {"role": "user", "content": "Hello, how are you? My name is John Doe"},
            {
                "role": "assistant",
                "content": "I'm doing well, thank you! How can I help you today?",
            },
            {"role": "user", "content": "Where can I find your product in Langkawi?"},
        ],
        "config": {
            "thread_id": "test_thread_id",
            "language": "en",
            "model": "LongCat-Flash-Chat",
        },
    }
    test_run_supervisor_stream_conversation(payload_product)
