from csagent.location.state import LocationWorkflowState
from csagent.configuration import Configuration
from langchain_core.runnables import RunnableConfig
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage,ToolMessage
import os
from typing import Literal, TypedDict, Optional
from pathlib import Path
from langgraph.graph import END
from langgraph.types import Command
from pydantic import Field
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
import logging

logger = logging.getLogger(__name__)

def get_locations():
    current_dir = Path(__file__).parent
    locations_dir = f"{current_dir}/../../../resources/locations"
    locations = [file[:-3] for file in os.listdir(locations_dir) if file.endswith(".md")]
    return locations

class Router(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""
    location: Literal[*get_locations()]

def triage_location(state: LocationWorkflowState, config: RunnableConfig):
    """
    This is Triage Location node. This node will triage the location based on the user's question.
    """
    question = state["users_question"]

    # final_answer = state["final_answer"]
    system_prompt = "You are a triage location agent, your task is to decide based on the customer's question which location information should be loaded to the next agent. Here are available locations:\n{locations}"
    messages = [SystemMessage(content=system_prompt.format(locations=", ".join(get_locations())))] + [HumanMessage(content=question)]

    llm = init_chat_model(config["configurable"]["model"], temperature=0).with_structured_output(Router)
    response = llm.invoke(messages)

    return {"location": response["location"]}

@tool(description= f"Use this tool to read location information. The available locations are: {', '.join(get_locations())}")
def read_location(location: Literal[*get_locations()]):
    try:
        current_dir = Path(__file__).parent
        locations_dir = f"{current_dir}/../../../resources/locations"
        with open(f"{locations_dir}/{location}.md", "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error in read_location tool: {e}")
        return f"Error in read_location tool: {str(e)}"

def location_agent(state: LocationWorkflowState, config: RunnableConfig):
    """
    This is Location Agent. This agent will answer the user's question based on the location information.
    """
    try:
        question = state["users_question"]

        llm = init_chat_model("google_genai:gemini-2.5-flash", temperature=0)
        tools = [read_location]

        current_dir = Path(__file__).parent
        prompt_path = f"{current_dir}/../../../resources/prompts/location_prompt_{config['configurable']['language']}.md"
        with open(prompt_path, "r") as f:
            system_prompt_template = f.read()
        
        prompt = system_prompt_template.format(locations=", ".join(get_locations()))
        agent_executor = create_react_agent(llm, tools, prompt=prompt, name="location_agent")
        agent_response = agent_executor.invoke({"messages": [("user", question)]})

        logger.info(f"Location agent response: {agent_response['messages'][-1].content[:50]}")

        return {"response": agent_response['messages'][-1].content}
    except Exception as e:
        logger.error(f"Error in location agent node: {e}")
        return {"response": f"Location agent error: {str(e)}"}