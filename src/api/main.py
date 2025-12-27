from fastapi import FastAPI
from pydantic import BaseModel

# Add the 'src' directory to the Python path
import sys
import os
import logging
from fastapi.middleware.cors import CORSMiddleware
import json
from fastapi.responses import StreamingResponse
from typing import List, Dict

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
    messages: List[Dict[str, str]]
    # config: Configuration


@app.post("/supervisor")
async def run_supervisor(request: UserRequest):
    async def event_generator():
        # Use astream for async iteration in FastAPI
        async for namespace, mode, data in supervisor_graph.astream(
            {"messages": request.messages},
            stream_mode=["messages", "custom"],
            subgraphs=True,
            # context=request.config,
            context=Configuration(),
        ):
            if mode == "custom":
                yield f"data: {json.dumps({'node': 'custom', 'content': data.get('custom_key')})}\n\n"
            elif mode == "messages":
                message_chunk, metadata = data

                # Extract content from the message chunk
                content = (
                    message_chunk.content
                    if hasattr(message_chunk, "content")
                    else str(message_chunk)
                )

                # Format as Server-Sent Events (SSE) if using text/event-stream
                if metadata["langgraph_node"] == "customer_service_team" and content:
                    yield f"data: {json.dumps({'node': metadata['langgraph_node'], 'content': content})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
