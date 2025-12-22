"""Define the configurable parameters for the agent."""

from typing import Annotated, Literal
from pydantic import BaseModel, Field, computed_field
import os
from pathlib import Path

current_dir = Path(__file__).parent
available_langs = [
    file[:-5]
    for file in os.listdir(f"{current_dir}/../../locales")
    if file.endswith(".json")
]


class Configuration(BaseModel):
    """The configuration for the agent."""

    thread_id: str = Field(
        default="",
        description="The thread ID to use for the agent's interactions. "
        "This ID is used to identify the thread in the chat history.",
    )

    model: Annotated[
        Literal[
            "google_genai:gemma-3-4b-it",
            "google_genai:gemma-3-12b-it",
            "google_genai:gemma-3-27b-it",
            "LongCat-Flash-Chat",
            "GLM-4.6V-Flash",
            "mimo-v2-flash",
        ],
        {"__template_metadata__": {"kind": "llm"}},
    ] = Field(
        default="google_genai:gemma-3-12b-it",
        description="The name of the language model to use for the agent's main interactions. "
        "Should be in the form: provider/model-name.",
    )

    model_small: Annotated[
        Literal[
            "google_genai:gemma-3-4b-it",
            "google_genai:gemma-3-12b-it",
            "google_genai:gemma-3-27b-it",
            "GLM-4.6V-Flash",
        ],
        {"__template_metadata__": {"kind": "llm"}},
    ] = Field(
        default="google_genai:gemma-3-12b-it",
        description="The name of the language model to use for the agent's main interactions. "
        "Should be in the form: provider/model-name.",
    )

    language: Annotated[
        Literal[*available_langs],
        {"__template_metadata__": {"kind": "language"}},
    ] = Field(
        default=available_langs[0],
        description="The language to use for the agent's interactions. "
        "This is used to select the language for the app and user interactions.",
    )


def get_model_info(model: str) -> dict:
    """Automatically extracted from the model string."""
    if model == "LongCat-Flash-Chat":
        return {
            "model": model,
            "model_provider": "openai",
            "base_url": "https://api.longcat.chat/openai",
            "api_key": os.getenv("LONGCAT_API_KEY"),
        }
    if model == "GLM-4.6V-Flash":
        return {
            "model": model,
            "model_provider": "openai",
            "base_url": "https://api.z.ai/api/paas/v4/",
            "api_key": os.getenv("ZAI_API_KEY"),
        }
    if model == "mimo-v2-flash":
        return {
            "model": model,
            "model_provider": "openai",
            "base_url": "https://api.xiaomimimo.com/v1",
            "api_key": os.getenv("MIMO_API_KEY"),
        }
    if model in [
        "google_genai:gemma-3-4b-it",
        "google_genai:gemma-3-12b-it",
        "google_genai:gemma-3-27b-it",
    ]:
        return {
            "model": model,
            "api_key": os.getenv("GOOGLE_API_KEY"),
        }
    return {
        "model": model 
    }
