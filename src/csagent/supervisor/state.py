from langgraph.graph import MessagesState


class SupervisorWorkflowState(MessagesState):
    users_question: str
    task: str
    response: str
    next: str


class SupervisorWorkflowStateInput(MessagesState):
    users_question: str


class SupervisorWorkflowStateOutput(MessagesState):
    response: str