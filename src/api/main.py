from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

# Add the 'src' directory to the Python path
import sys
import os
import logging
import json
from fastapi.responses import StreamingResponse
from fastapi import Request
from typing import List, Dict

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from csagent.supervisor.graph import supervisor_graph
from csagent.configuration import Configuration
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("CSAGENT_API_KEY")

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

# Define API Key security scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)):
    """Verify the API key from the request header."""
    if not API_KEY:
        logger.error("API_KEY not configured in environment")
        raise HTTPException(status_code=500, detail="API key not configured on server")

    if not api_key:
        raise HTTPException(status_code=401, detail="API key is missing")

    if api_key != API_KEY:
        logger.warning("Invalid API key attempt")
        raise HTTPException(status_code=403, detail="Invalid API key")

    return api_key


@app.get("/")
async def health_check():
    return "The health check is successful."


class Message(BaseModel):
    role: str
    content: str


class UserRequest(BaseModel):
    messages: List[Message]
    config: Dict[str, str]


@app.post("/supervisor")
async def run_supervisor(
    request: UserRequest, raw_request: Request, api_key: str = Depends(verify_api_key)
):
    if not request.messages:
        raise HTTPException(status_code=400, detail="Messages are required")
    try:
        config = Configuration(**request.config)
    except ValueError as e:
        logger.warning(f"Invalid config, using defaults: {str(e)}")
        config = Configuration()
    except Exception as e:
        logger.error(f"Unexpected error in config: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Configuration error")

    async def event_generator():
        try:
            messages = request.messages
            if len(messages) > 11:
                messages = messages[-11:]
                logger.info(f"Only last 11 messages sent to supervisor: {messages}")
            async for namespace, mode, data in supervisor_graph.astream(
                {"messages": [msg.model_dump() for msg in messages]},
                stream_mode=["messages", "custom"],
                subgraphs=True,
                context=config,
            ):
                # Check for client disconnection
                if await raw_request.is_disconnected():
                    logger.info("Client disconnected")
                    break

                if mode == "custom":
                    custom_data = {
                        "node": "custom",
                        "content": data.get("custom_key"),
                    }
                    try:
                        yield f"data: {json.dumps(custom_data)}\n\n"
                    except TypeError as e:
                        logger.error(f"JSON serialization error: {e}")

                elif mode == "messages":
                    message_chunk, metadata = data

                    # Extract content safely
                    if hasattr(message_chunk, "content"):
                        content = message_chunk.content
                    else:
                        content = str(message_chunk)
                        logger.warning(f"No content attribute: {type(message_chunk)}")

                    # Get node name safely
                    node_name = metadata.get("langgraph_node")

                    # Format as Server-Sent Events (SSE) if using text/event-stream
                    if node_name == "customer_service_team" and content:
                        response_data = {"node": node_name, "content": content}
                        try:
                            yield f"data: {json.dumps(response_data)}\n\n"
                        except TypeError as e:
                            logger.error(f"JSON serialization error: {e}")
            # Signal completion
            yield f"data: {json.dumps({'event': 'done'})}\n\n"
        except Exception as e:
            logger.error(f"Error during streaming: {str(e)}", exc_info=True)
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
