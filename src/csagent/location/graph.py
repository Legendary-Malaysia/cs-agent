from langgraph.graph import START, StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from csagent.location.state import (
    LocationWorkflowState,
    LocationWorkflowStateInput,
    LocationWorkflowStateOutput,
)
from csagent.location.nodes import location_agent
from csagent.configuration import Configuration

# Build the chat graph
location_builder = StateGraph(
    LocationWorkflowState,
    input=LocationWorkflowStateInput,
    output=LocationWorkflowStateOutput,
    config_schema=Configuration,
)

# location_builder.add_node("triage_location", triage_location)
location_builder.add_node("location_agent", location_agent)
location_builder.add_edge(START, "location_agent")
location_builder.add_edge("location_agent", END)

checkpointer = InMemorySaver()
location_graph = location_builder.compile()