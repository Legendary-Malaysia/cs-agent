from csagent.location.state import LocationWorkflowState
from csagent.configuration import get_model_info, Configuration
from langgraph.runtime import Runtime
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
import os
from pathlib import Path
from langchain.agents import create_agent
from langchain.agents.middleware import ToolCallLimitMiddleware
from langchain_core.tools import tool
from langgraph.config import get_stream_writer
import logging
from typing import Literal

logger = logging.getLogger(__name__)


def get_resources_dir():
    current_dir = Path(__file__).parent
    return current_dir / "resources"


def get_locations():
    locations_dir = get_resources_dir() / "locations"
    if not locations_dir.exists():
        logger.warning(f"Locations directory not found: {locations_dir}")
        return []
    locations = [
        file[:-3] for file in os.listdir(locations_dir) if file.endswith(".md")
    ]
    return locations


LOCATIONS = get_locations()


@tool(description="Use this tool to read location information")
def read_location(location: Literal[*LOCATIONS]):
    writer = get_stream_writer()
    writer({"custom_key": "Anchoring the scent into location..."})

    if location not in LOCATIONS:
        return f"Location {location} not found. Available locations: {', '.join(LOCATIONS)}"

    try:
        locations_dir = get_resources_dir() / "locations"
        with open(locations_dir / f"{location}.md", "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.exception("Error in read_location tool")
        return f"Error in read_location tool: {str(e)}"


def location_agent_node(state: LocationWorkflowState, runtime: Runtime[Configuration]):
    """
    This is Location Agent. This agent will answer the user's question based on the location information.
    """
    try:
        task = state.get("task")

        llm = init_chat_model(
            **get_model_info(runtime.context.model), temperature=0, streaming=False
        )
        tools = [read_location]

        prompt_path = (
            get_resources_dir()
            / "prompts"
            / "location_prompt.md"
        )
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        with open(prompt_path, "r") as f:
            system_prompt_template = f.read()

        prompt = system_prompt_template.format(locations=", ".join(LOCATIONS))
        agent_executor = create_agent(
            llm,
            tools,
            system_prompt=prompt,
            name="location_agent",
            middleware=[ToolCallLimitMiddleware(run_limit=3)],
        )
        agent_response = agent_executor.invoke(
            {"messages": [HumanMessage(content=f"Here is your task: {task}")]},
            config={"tags": ["location_team"]},
        )

        logger.info(
            f"Location agent response: {agent_response['messages'][-1].content[:50]}"
        )

        return {"response": agent_response["messages"][-1].content}
    except Exception as e:
        logger.exception("Error in location agent node")
        return {"response": f"Location agent error: {str(e)}"}
