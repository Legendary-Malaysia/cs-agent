from fastapi import FastAPI
from pydantic import BaseModel

# Add the 'src' directory to the Python path
import sys
import os
import logging
from fastapi.middleware.cors import CORSMiddleware

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from csagent.supervisor.graph import supervisor_graph
from csagent.configuration import Configuration
from dotenv import load_dotenv

load_dotenv()


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Supervisor API",
    version="1.0",
    description="API for the supervisor graph",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def health_check():
    return "The health check is successful."


class UserRequest(BaseModel):
    messages: str


@app.post("/supervisor")
async def run_supervisor(request: UserRequest):
    """
    Runs the supervisor graph with the user's question.
    """

    result = await supervisor_graph.ainvoke(
        {"messages": [{"role": "user", "content": request.messages}]},
        context=Configuration(),
    )
    return result


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8001)
