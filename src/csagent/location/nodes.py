from csagent.location.state import LocationWorkflowState
from csagent.configuration import get_model_info
from langchain_core.runnables import RunnableConfig
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
import os
from typing import Literal
from pathlib import Path
from langchain.agents import create_agent
from langchain_core.tools import tool
import logging

logger = logging.getLogger(__name__)


def get_resources_dir():
    current_dir = Path(__file__).parent
    return current_dir / "resources"


def get_locations():
    locations_dir = get_resources_dir() / "locations"
    locations = [
        file[:-3] for file in os.listdir(locations_dir) if file.endswith(".md")
    ]
    return locations


@tool(
    description=f"Use this tool to read location information. The available locations are: {', '.join(get_locations())}"
)
def read_location(location: Literal[*get_locations()]):
    try:
        locations_dir = get_resources_dir() / "locations"
        with open(locations_dir / f"{location}.md", "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error in read_location tool: {e}")
        return f"Error in read_location tool: {str(e)}"


def location_agent_node(state: LocationWorkflowState, config: RunnableConfig):
    """
    This is Location Agent. This agent will answer the user's question based on the location information.
    """
    try:
        task = state["task"]

        llm = init_chat_model(
            **get_model_info(config["configurable"]["model"]),
            temperature=0,
        )
        tools = [read_location]

        prompt_path = (
            get_resources_dir()
            / "prompts"
            / f"location_prompt_{config['configurable']['language']}.md"
        )
        with open(prompt_path, "r") as f:
            system_prompt_template = f.read()

        prompt = system_prompt_template.format(locations=", ".join(get_locations()))
        agent_executor = create_agent(
            llm, tools, system_prompt=prompt, name="location_agent"
        )
        agent_response = agent_executor.invoke(
            {"messages": [HumanMessage(content=f"Here is your task: {task}")]}
        )

        logger.info(
            f"Location agent response: {agent_response['messages'][-1].content[:50]}"
        )

        return {"response": agent_response["messages"][-1].content}
    except Exception as e:
        logger.error(f"Error in location agent node: {e}")
        return {"response": f"Location agent error: {str(e)}"}
