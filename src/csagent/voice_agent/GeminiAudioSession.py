import os
import asyncio
import base64
from pathlib import Path
import json
import traceback
from typing import Optional, Dict, Any, List

from fastapi import WebSocket, WebSocketDisconnect
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError

from google import genai
from google.genai import types
from dotenv import load_dotenv
import logging
from csagent.product.utils import get_products, read_product_file

logger = logging.getLogger(__name__)

load_dotenv()

# Gemini client
client = genai.Client(http_options={"api_version": "v1alpha"})

CURRENT_DIR = Path(__file__).parent

prompt_path = CURRENT_DIR / "resources" / "prompts" / "prompts.md"
if not prompt_path.exists():
    raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
with open(prompt_path, "r") as f:
    system_prompt = f.read()

SYSTEM_INSTRUCTION = system_prompt

MODEL = "gemini-2.5-flash-native-audio-preview-12-2025"

available_products = get_products()

# Define function declarations
FUNCTION_DECLARATIONS = [
    {
        "name": "legendary_profile",
        "description": "Get the company profile of Legendary",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "legendary_locations",
        "description": "Get the physical store locations, online store, shipping, and retail & business partners",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_product_info",
        "description": "Get the product information of Legendary",
        "parameters": {
            "type": "object",
            "properties": {
                "product_name": {
                    "type": "string",
                    "enum": available_products,
                    "description": "The product name",
                },
            },
            "required": ["product_name"],
        },
    },
]


class GeminiAudioSession:
    def __init__(
        self,
        websocket: WebSocket,
        enable_search: bool = False,
        enable_functions: bool = True,
    ):
        self.websocket = websocket
        self.session: Optional[genai.LiveSession] = None
        self.running = True
        self.enable_search = enable_search
        self.enable_functions = enable_functions

    def _build_config(self) -> Dict[str, Any]:
        """Build the configuration with tools based on settings"""
        config = {
            "system_instruction": SYSTEM_INSTRUCTION,
            "response_modalities": ["AUDIO"],
            "proactivity": {"proactive_audio": True},
        }

        # Add tools if enabled
        tools = []
        if self.enable_search:
            tools.append({"google_search": {}})

        if self.enable_functions:
            tools.append({"function_declarations": FUNCTION_DECLARATIONS})

        if tools:
            config["tools"] = tools

        return config

    async def handle_tool_call(self, tool_call) -> List[types.FunctionResponse]:
        """Handle tool calls from Gemini and return responses"""
        function_responses = []

        for fc in tool_call.function_calls:
            print(f"Function called: {fc.name}")
            print(f"Function args: {fc.args}")

            # Send tool call notification to client (ignore if disconnected)
            try:
                await self.websocket.send_json(
                    {
                        "type": "tool_call",
                        "function_name": fc.name,
                        "arguments": dict(fc.args) if fc.args else {},
                    }
                )
            except (WebSocketDisconnect, ConnectionClosedOK, ConnectionClosedError):
                self.running = False
                return function_responses

            # Execute the function (this is where you'd implement actual logic)
            result = await self.execute_function(fc.name, fc.args)

            # Create function response
            function_response = types.FunctionResponse(
                id=fc.id, name=fc.name, response={"result": result}
            )
            function_responses.append(function_response)

            # Send result to client (ignore if disconnected)
            try:
                await self.websocket.send_json(
                    {"type": "tool_result", "function_name": fc.name, "result": result}
                )
            except (WebSocketDisconnect, ConnectionClosedOK, ConnectionClosedError):
                self.running = False
                return function_responses

        return function_responses

    async def execute_function(self, function_name: str, args: Dict) -> Any:
        """
        Execute the actual function logic.
        """
        if function_name == "legendary_profile":
            profile_path = (
                CURRENT_DIR
                / ".."
                / "profile"
                / "resources"
                / "profiles"
                / "company_profile.md"
            )
            if not profile_path.exists():
                profile = "Company profile not found"
            else:
                with open(profile_path, "r") as f:
                    profile = f.read()
            return {
                "profile": profile,
            }

        elif function_name == "legendary_locations":

            def get_locations():
                locations_dir = (
                    CURRENT_DIR / ".." / "location" / "resources" / "locations"
                )
                if not locations_dir.exists():
                    logger.warning(f"Locations directory not found: {locations_dir}")
                    return []
                locations = [
                    file[:-3]
                    for file in os.listdir(locations_dir)
                    if file.endswith(".md")
                ]
                return locations

            locations = get_locations()

            locations_path = CURRENT_DIR / "resources" / "prompts" / "locations.md"
            if not locations_path.exists():
                locations = "Locations not found"
            else:
                with open(locations_path, "r") as f:
                    locations_info = f.read()
                    locations_info = locations_info.format(
                        locations=", ".join(locations)
                    )
            return {
                "locations": locations_info,
            }

        elif function_name == "get_product_info":
            product_name = args.get("product_name", "Unknown")
            product_info = read_product_file(product_name)
            return {
                "product_info": product_info,
            }

        else:
            return {"error": f"Unknown function: {function_name}"}

    async def send_to_gemini(self):
        """Send audio from websocket to Gemini"""
        try:
            while self.running:
                data = await self.websocket.receive_text()
                message = json.loads(data)

                if message.get("type") == "audio":
                    # Audio data is base64 encoded from browser
                    audio_data = base64.b64decode(message["data"])
                    await self.session.send_realtime_input(
                        audio={"data": audio_data, "mime_type": "audio/pcm"}
                    )
                elif message.get("type") == "text":
                    # Support text input as well
                    text = message.get("data", "")
                    await self.session.send_client_content(
                        turns={"parts": [{"text": text}]}
                    )
                elif message.get("type") == "stop":
                    self.running = False
                    break
        except WebSocketDisconnect:
            self.running = False
        except Exception as e:
            print(f"Error in send_to_gemini: {e}")
            traceback.print_exc()
            self.running = False

    async def receive_from_gemini(self):
        """Receive audio/text from Gemini and send to websocket"""
        try:
            while self.running:
                turn = self.session.receive()
                async for response in turn:
                    # Handle audio data
                    if data := response.data:
                        audio_b64 = base64.b64encode(data).decode("utf-8")
                        await self.websocket.send_json(
                            {"type": "audio", "data": audio_b64}
                        )

                    # Handle text transcription
                    if text := response.text:
                        await self.websocket.send_json({"type": "text", "data": text})

                    # Handle tool calls
                    if response.tool_call:
                        print("Tool call received from Gemini")
                        function_responses = await self.handle_tool_call(
                            response.tool_call
                        )

                        # Send tool responses back to Gemini
                        await self.session.send_tool_response(
                            function_responses=function_responses
                        )

                    # Handle server content (for Google Search results)
                    if response.server_content:
                        model_turn = response.server_content.model_turn
                        if model_turn:
                            for part in model_turn.parts:
                                # Executable code from Google Search
                                if part.executable_code:
                                    await self.websocket.send_json(
                                        {
                                            "type": "search_code",
                                            "code": part.executable_code.code,
                                        }
                                    )

                                # Code execution results
                                if part.code_execution_result:
                                    await self.websocket.send_json(
                                        {
                                            "type": "search_result",
                                            "output": part.code_execution_result.output,
                                        }
                                    )

                # Handle turn complete (interruptions)
                await self.websocket.send_json({"type": "turn_complete"})
        except (WebSocketDisconnect, ConnectionClosedOK, ConnectionClosedError):
            # Client disconnected - this is expected behavior, not an error
            print("Client disconnected, stopping receive_from_gemini")
            self.running = False
        except Exception as e:
            print(f"Error in receive_from_gemini: {e}")
            traceback.print_exc()
            self.running = False

    async def run(self):
        """Main loop for the audio session"""
        try:
            config = self._build_config()
            async with client.aio.live.connect(model=MODEL, config=config) as session:
                self.session = session

                # Send ready signal to client with enabled features
                await self.websocket.send_json(
                    {
                        "type": "ready",
                        "features": {
                            "search": self.enable_search,
                            "functions": self.enable_functions,
                            "available_functions": [
                                f["name"] for f in FUNCTION_DECLARATIONS
                            ],
                        },
                    }
                )

                # Run both send and receive tasks concurrently
                async with asyncio.TaskGroup() as tg:
                    tg.create_task(self.send_to_gemini())
                    tg.create_task(self.receive_from_gemini())
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Error in session: {e}")
            traceback.print_exc()
            try:
                await self.websocket.send_json({"type": "error", "data": str(e)})
            except Exception as e:
                print(f"Error sending error to client: {e}")
                pass
