from langgraph.graph import MessagesState
from typing import List, Annotated
import operator


class SupervisorWorkflowState(MessagesState):
    users_question: str
    task: str
    response: str
    notes: Annotated[List[str], operator.add]
    next_step: str


class SupervisorWorkflowStateOutput(MessagesState):
    response: str
