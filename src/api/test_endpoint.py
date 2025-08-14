from fastapi.testclient import TestClient
import requests
from main import app
import sys
import os

# Add the 'src' directory to the Python path to resolve csagent module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
BASE_URL = "https://cs-agent-phi.vercel.app"

client = TestClient(app)

def test_health_check():
    """Tests the health check endpoint."""
    response = client.get("/")
    print("################# response: ", response)
    assert response.status_code == 200
    assert response.json() == "The health check is successful."

def test_health_check_deployed():
    """Tests the health check endpoint on deployed app."""
    response = requests.get(f"{BASE_URL}/")
    print("################# response: ", response, BASE_URL)
    print("################# response.json(): ", response.json())
    assert response.status_code == 200
    assert response.json() == "The health check is successful."

def test_run_supervisor():
    """Tests the supervisor endpoint."""
    config = {
        "configurable": {
            "thread_id": "test_thread_id",
            "language": "en",
            "model": "google_genai:gemini-2.5-flash"
        }
    }
    response = client.post("/supervisor", json={"users_question": "Where can I buy spirit?", "config": config})
    print("################# response: ", response)
    print("################# response.json(): ", response.json()["response"])
    # assert response.status_code == 200
    # You might want to add more specific assertions here based on the expected output
    # assert isinstance(response.json(), dict)

def test_run_supervisor_deployed():
    """Tests the supervisor endpoint on deployed app."""
    config = {
        "configurable": {
            "thread_id": "test_thread_id",
            "language": "en",
            "model": "google_genai:gemini-2.5-flash"
        }
    }
    response = requests.post(f"{BASE_URL}/supervisor", json={"users_question": "Where can I buy spirit?", "config": config})
    print("################# response: ", response)
    print("################# response.json(): ", response.json()["response"])

if __name__ == "__main__":
    # test_health_check()
    test_health_check_deployed()
    # test_run_supervisor()
    test_run_supervisor_deployed()
