from langgraph.graph import MessagesState


class ProfileWorkflowState(MessagesState):
    task: str
    response: str


class ProfileWorkflowStateInput(MessagesState):
    task: str


class ProfileWorkflowStateOutput(MessagesState):
    response: str
