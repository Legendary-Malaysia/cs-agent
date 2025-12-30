from langgraph.graph import MessagesState


class LocationWorkflowState(MessagesState):
    task: str
    response: str


class LocationWorkflowStateInput(MessagesState):
    task: str


class LocationWorkflowStateOutput(MessagesState):
    response: str
