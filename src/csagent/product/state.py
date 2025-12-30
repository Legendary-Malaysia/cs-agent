from langgraph.graph import MessagesState


class ProductWorkflowState(MessagesState):
    task: str
    response: str


class ProductWorkflowStateInput(MessagesState):
    task: str


class ProductWorkflowStateOutput(MessagesState):
    response: str
