from langgraph.graph import START, StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from csagent.location.state import (
    LocationWorkflowState,
    LocationWorkflowStateInput,
    LocationWorkflowStateOutput,
)
from csagent.location.nodes import triage_location
from csagent.configuration import Configuration

# Build the chat graph
location_builder = StateGraph(
    LocationWorkflowState,
    input=LocationWorkflowStateInput,
    output=LocationWorkflowStateOutput,
    config_schema=Configuration,
)

location_builder.add_node("triage_location", triage_location)
location_builder.add_edge(START, "triage_location")
location_builder.add_edge("triage_location", END)

checkpointer = InMemorySaver()
location_graph = location_builder.compile()