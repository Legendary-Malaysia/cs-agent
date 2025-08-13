from fastapi import FastAPI
from pydantic import BaseModel
from csagent.supervisor.graph import supervisor_graph
import sys
import os
import logging
# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
# Add the 'src' directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

app = FastAPI(
    title="Supervisor API",
    version="1.0",
    description="API for the supervisor graph",
)

@app.get("/")
async def health_check():
    return "The health check is successful."

class UserRequest(BaseModel):
    users_question: str
    config: dict

@app.post("/supervisor")
async def run_supervisor(request: UserRequest):
    """
    Runs the supervisor graph with the user's question.
    """
    result = supervisor_graph.invoke({"users_question": request.users_question}, request.config)
    return result

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8001)
