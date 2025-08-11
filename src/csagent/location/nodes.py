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