from typing import Dict
from langgraph.graph import MessagesState


class ChatWorkflowState(MessagesState):
    question: str
    product: str
    response: str
    final_answer: str


class ChatWorkflowStateInput(MessagesState):
    question: str


class ChatWorkflowStateOutput(MessagesState):
    response: str
