from fastapi import (
    FastAPI,
    HTTPException,
    Security,
    Depends,
    WebSocket,
    WebSocketDisconnect,
)
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
from csagent.router_agent.graph import router_graph
from csagent.configuration import Configuration
from csagent.voice_agent.GeminiAudioSession import GeminiAudioSession
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

API_KEY = os.getenv("CSAGENT_API_KEY")
ACTIVE_GRAPH = os.getenv("ACTIVE_GRAPH", "router")
max_messages_str = os.getenv("MAX_MESSAGES", "11")
try:
    MAX_MESSAGES = int(max_messages_str)
except ValueError:
    logger.warning(
        f"Failed to parse MAX_MESSAGES '{max_messages_str}' as integer, defaulting to 11"
    )
    MAX_MESSAGES = 11

app = FastAPI(
    title="Customer Service API",
    version="1.0",
    description="API for the customer service graph",
)

# Define API Key security scheme
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)


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


@app.post("/customer-service")
async def run_customer_service(
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
        logger.exception("Unexpected error in config")
        raise HTTPException(status_code=500, detail="Configuration error") from e

    async def event_generator():
        try:
            graph = router_graph if ACTIVE_GRAPH == "router" else supervisor_graph
            graph_name = ACTIVE_GRAPH
            logger.info(f"Using {graph_name} graph")

            messages = request.messages
            if len(messages) > MAX_MESSAGES:
                messages = messages[-MAX_MESSAGES:]
                logger.info(
                    f"Messages trimmed. Only last {MAX_MESSAGES} messages sent to {graph_name}"
                )

            async for _namespace, mode, data in graph.astream(
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
                    except TypeError:
                        logger.exception("JSON serialization error")

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
                        except TypeError:
                            logger.exception("JSON serialization error")
            # Signal completion
            yield f"data: {json.dumps({'event': 'done'})}\n\n"
        except Exception:
            logger.exception("Error during streaming")
            yield f"data: {json.dumps({'error': 'An unexpected error occurred'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.websocket("/ws/audio")
async def websocket_endpoint(
    websocket: WebSocket, enable_search: bool = False, enable_functions: bool = True
):
    """
    WebSocket endpoint for audio streaming with tool calling support.

    Query parameters:
    - enable_search: Enable Google Search grounding (default: True)
    - enable_functions: Enable function calling (default: True)

    Example: ws://localhost:8000/ws/audio?enable_search=true&enable_functions=true
    """
    await websocket.accept()

    session = GeminiAudioSession(
        websocket, enable_search=enable_search, enable_functions=enable_functions
    )
    try:
        await session.run()
    except WebSocketDisconnect:
        logger.exception("Client disconnected")
    except Exception:
        logger.exception("WebSocket error")
    finally:
        try:
            await websocket.close()
        except Exception:
            logger.exception("WebSocket close error")
