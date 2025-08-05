from langgraph.graph import START, StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from csagent.state import (
    ChatWorkflowState,
    ChatWorkflowStateInput,
    ChatWorkflowStateOutput,
)
from csagent.nodes import product_supervisor_node, orchid_agent, violet_agent, summary_agent
from csagent.configuration import Configuration

# Build the chat graph
chat_builder = StateGraph(
    ChatWorkflowState,
    input=ChatWorkflowStateInput,
    output=ChatWorkflowStateOutput,
    config_schema=Configuration,
)

chat_builder.add_node("product_supervisor_node", product_supervisor_node)
chat_builder.add_node("orchid_agent", orchid_agent)
chat_builder.add_node("violet_agent", violet_agent)
chat_builder.add_node("summary_agent", summary_agent)

chat_builder.add_edge(START, "product_supervisor_node")
chat_builder.add_edge("orchid_agent", "product_supervisor_node")
chat_builder.add_edge("violet_agent", "product_supervisor_node")
chat_builder.add_edge("summary_agent", END)

checkpointer = InMemorySaver()
chat_graph = chat_builder.compile()