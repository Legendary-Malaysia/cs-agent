from typing import Dict
from langgraph.graph import MessagesState


class LocationWorkflowState(MessagesState):
    users_question: str
    question: str
    response: str
    location: str


class LocationWorkflowStateInput(MessagesState):
    users_question: str


class LocationWorkflowStateOutput(MessagesState):
    response: str
    location: str
