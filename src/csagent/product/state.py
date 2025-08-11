from typing import Dict
from langgraph.graph import MessagesState


class ChatWorkflowState(MessagesState):
    users_question: str
    question: str
    response: str
    # final_answer: str


class ChatWorkflowStateInput(MessagesState):
    users_question: str


class ChatWorkflowStateOutput(MessagesState):
    response: str
