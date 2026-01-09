from langgraph.graph import START, StateGraph, END
from csagent.profile.state import (
    ProfileWorkflowState,
    ProfileWorkflowStateInput,
    ProfileWorkflowStateOutput,
)
from csagent.profile.nodes import profile_team_node
from csagent.configuration import Configuration

# Build the profile graph
profile_builder = StateGraph(
    ProfileWorkflowState,
    input_schema=ProfileWorkflowStateInput,
    output_schema=ProfileWorkflowStateOutput,
    context_schema=Configuration,
)

profile_builder.add_node("profile_team_node", profile_team_node)
profile_builder.add_edge(START, "profile_team_node")
profile_builder.add_edge("profile_team_node", END)

profile_graph = profile_builder.compile()
