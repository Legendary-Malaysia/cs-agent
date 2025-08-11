from langgraph.graph import START, StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from csagent.product.state import (
    ChatWorkflowState,
    ChatWorkflowStateInput,
    ChatWorkflowStateOutput,
)
from csagent.product.nodes import product_supervisor_node, orchid_agent, violet_agent, summary_agent, mahsuri_agent, man_agent, spiritI_agent, spiritII_agent, threewishes_agent
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
chat_builder.add_node("mahsuri_agent", mahsuri_agent)
chat_builder.add_node("man_agent", man_agent)
chat_builder.add_node("spiritI_agent", spiritI_agent)
chat_builder.add_node("spiritII_agent", spiritII_agent)
chat_builder.add_node("threewishes_agent", threewishes_agent)

chat_builder.add_edge(START, "product_supervisor_node")
chat_builder.add_edge("orchid_agent", "product_supervisor_node")
chat_builder.add_edge("violet_agent", "product_supervisor_node")
chat_builder.add_edge("mahsuri_agent", "product_supervisor_node")
chat_builder.add_edge("man_agent", "product_supervisor_node")
chat_builder.add_edge("spiritI_agent", "product_supervisor_node")
chat_builder.add_edge("spiritII_agent", "product_supervisor_node")
chat_builder.add_edge("threewishes_agent", "product_supervisor_node")
chat_builder.add_edge("summary_agent", END)

checkpointer = InMemorySaver()
product_graph = chat_builder.compile()