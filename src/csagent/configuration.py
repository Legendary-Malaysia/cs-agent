"""Define the configurable parameters for the agent."""

from typing import Annotated, Literal
from pydantic import BaseModel, Field
import os
from pathlib import Path

current_dir = Path(__file__).parent
available_langs = [file[:-5] for file in os.listdir(f"{current_dir}/../../locales") if file.endswith(".json")]


class Configuration(BaseModel):
    """The configuration for the agent."""

    thread_id: str = Field(
        default="",
        description="The thread ID to use for the agent's interactions. "
        "This ID is used to identify the thread in the chat history.",
    )

    model: Annotated[
        Literal[
            "google_genai:gemma-3-12b-it",
            "google_genai:gemma-3-27b-it",
            "google_genai:gemini-2.5-flash-lite",
            "google_genai:gemini-2.5-flash",
        ],
        {"__template_metadata__": {"kind": "llm"}},
    ] = Field(
        default="google_genai:gemini-2.5-flash-lite",
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
