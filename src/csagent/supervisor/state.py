from langgraph.graph import MessagesState
from typing import List, Annotated
import operator


class SupervisorWorkflowState(MessagesState):
    users_question: str
    task: str
    response: str
    notes: Annotated[List[str], operator.add]
    next: str


class SupervisorWorkflowStateInput(MessagesState):
    users_question: str


class SupervisorWorkflowStateOutput(MessagesState):
    response: str
