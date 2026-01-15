"""Define the configurable parameters for the agent."""

from typing import Annotated, Literal
from pydantic import BaseModel, Field
import os


class Configuration(BaseModel):
    """The configuration for the agent."""

    thread_id: str = Field(
        default="",
        description="The thread ID to use for the agent's interactions. "
        "This ID is used to identify the thread in the chat history.",
    )

    model: Annotated[
        Literal[
            "LongCat-Flash-Chat",
            "GLM-4.6V-Flash",
            "mimo-v2-flash",
        ],
        {"__template_metadata__": {"kind": "llm"}},
    ] = Field(
        default="LongCat-Flash-Chat",
        description="The name of the language model to use for the agent's main interactions.",
    )

    model_medium: Annotated[
        Literal[
            "google_genai:gemma-3-4b-it",
            "google_genai:gemma-3-12b-it",
            "google_genai:gemma-3-27b-it",
            "GLM-4.6V-Flash",
            "mimo-v2-flash",
        ],
        {"__template_metadata__": {"kind": "llm"}},
    ] = Field(
        default="GLM-4.6V-Flash",
        description="The name of the medium language model to use for medium-weight tasks. "
        "Google model should be in the form: provider/model-name.",
    )

    model_small: Annotated[
        Literal[
            "google_genai:gemma-3-4b-it",
            "google_genai:gemma-3-12b-it",
            "google_genai:gemma-3-27b-it",
            "GLM-4.6V-Flash",
            "mimo-v2-flash",
        ],
        {"__template_metadata__": {"kind": "llm"}},
    ] = Field(
        default="google_genai:gemma-3-4b-it",
        description="The name of the smaller language model to use for lightweight tasks. "
        "Google model should be in the form: provider/model-name.",
    )

    language: Annotated[
        Literal["en", "id"],
        {"__template_metadata__": {"kind": "language"}},
    ] = Field(
        default="en",
        description="The language to use for the agent's interactions. "
        "This is used to select the language for the app and user interactions.",
    )


def get_model_info(model: str) -> dict:
    """Get model configuration including provider details and API key."""
    if model == "LongCat-Flash-Chat":
        api_key = os.getenv("LONGCAT_API_KEY")
        if not api_key:
            raise ValueError("LONGCAT_API_KEY environment variable is not set")
        return {
            "model": model,
            "model_provider": "openai",
            "base_url": "https://api.longcat.chat/openai",
            "api_key": api_key,
        }
    if model == "GLM-4.6V-Flash":
        api_key = os.getenv("ZAI_API_KEY")
        if not api_key:
            raise ValueError("ZAI_API_KEY environment variable is not set")
        return {
            "model": model,
            "model_provider": "openai",
            "base_url": "https://api.z.ai/api/paas/v4/",
            "api_key": api_key,
        }
    if model == "mimo-v2-flash":
        api_key = os.getenv("MIMO_API_KEY")
        if not api_key:
            raise ValueError("MIMO_API_KEY environment variable is not set")
        return {
            "model": model,
            "model_provider": "openai",
            "base_url": "https://api.xiaomimimo.com/v1",
            "api_key": api_key,
        }
    if model in [
        "google_genai:gemma-3-4b-it",
        "google_genai:gemma-3-12b-it",
        "google_genai:gemma-3-27b-it",
    ]:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")
        return {
            "model": model,
            "api_key": api_key,
        }
    raise ValueError(f"Unknown model: {model}")
