from langgraph.graph import START, StateGraph, END
from csagent.product.state import (
    ProductWorkflowState,
    ProductWorkflowStateInput,
    ProductWorkflowStateOutput,
)
from csagent.product.nodes import (
    product_agent_node,
)
from csagent.configuration import Configuration

product_builder = StateGraph(
    ProductWorkflowState,
    input_schema=ProductWorkflowStateInput,
    output_schema=ProductWorkflowStateOutput,
    context_schema=Configuration,
)

product_builder.add_node("product_agent_node", product_agent_node)

product_builder.add_edge(START, "product_agent_node")
product_builder.add_edge("product_agent_node", END)

product_graph = product_builder.compile()
