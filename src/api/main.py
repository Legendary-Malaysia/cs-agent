from fastapi import FastAPI
from pydantic import BaseModel

# Add the 'src' directory to the Python path
import sys
import os
import logging
from fastapi.middleware.cors import CORSMiddleware
import json
from fastapi.responses import StreamingResponse

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
    # config: Configuration


@app.post("/supervisor")
async def run_supervisor(request: UserRequest):
    async def event_generator():
        # Use astream for async iteration in FastAPI
        async for namespace, data in supervisor_graph.astream(
            {"messages": [{"role": "user", "content": request.messages}]},
            stream_mode="messages",
            subgraphs=True,
            # context=request.config,
            context=Configuration(),
        ):
            token, metadata = data
            print(namespace)
            print("token", token)
            print("metadata", metadata)
            # Extract content from the message chunk
            # Most providers use .content; content_blocks is provider-specific
            content = token.content if hasattr(token, "content") else str(token)

            # Format as Server-Sent Events (SSE) if using text/event-stream
            if metadata["langgraph_node"] == "supervisor_node":
                yield f"data: {json.dumps({'node': metadata['langgraph_node'], 'content': ''})}\n\n"
            else:
                yield f"data: {json.dumps({'node': metadata['langgraph_node'], 'content': content})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8001)
