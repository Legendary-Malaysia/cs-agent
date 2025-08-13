from fastapi.testclient import TestClient
from main import app
import sys
import os

# Add the 'src' directory to the Python path to resolve csagent module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

client = TestClient(app)

def test_health_check():
    """Tests the health check endpoint."""
    response = client.get("/")
    print("################# response: ", response)
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

if __name__ == "__main__":
    test_health_check()
    test_run_supervisor()
