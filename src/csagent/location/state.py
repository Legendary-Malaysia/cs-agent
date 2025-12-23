from typing import Dict
from langgraph.graph import MessagesState


class LocationWorkflowState(MessagesState):
    task: str
    response: str
    location: str


class LocationWorkflowStateInput(MessagesState):
    task: str


class LocationWorkflowStateOutput(MessagesState):
    response: str
    location: str
