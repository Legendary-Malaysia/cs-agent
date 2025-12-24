from langgraph.graph import START, StateGraph, END
from csagent.location.state import (
    LocationWorkflowState,
    LocationWorkflowStateInput,
    LocationWorkflowStateOutput,
)
from csagent.location.nodes import location_agent_node
from csagent.configuration import Configuration

# Build the chat graph
location_builder = StateGraph(
    LocationWorkflowState,
    input_schema=LocationWorkflowStateInput,
    output_schema=LocationWorkflowStateOutput,
    context_schema=Configuration,
)

location_builder.add_node("location_agent_node", location_agent_node)
location_builder.add_edge(START, "location_agent_node")
location_builder.add_edge("location_agent_node", END)

location_graph = location_builder.compile()
