from langgraph.graph import START, StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from csagent.supervisor.state import (
    SupervisorWorkflowState,
    SupervisorWorkflowStateInput,
    SupervisorWorkflowStateOutput,
)
from csagent.supervisor.nodes import supervisor_node, customer_service_team, call_product_team, call_location_team
from csagent.configuration import Configuration

# Build the chat graph
supervisor_builder = StateGraph(
    SupervisorWorkflowState,
    input=SupervisorWorkflowStateInput,
    output=SupervisorWorkflowStateOutput,
    config_schema=Configuration,
)

supervisor_builder.add_node("supervisor_node", supervisor_node)
supervisor_builder.add_node("product_team", call_product_team)
supervisor_builder.add_node("location_team", call_location_team)
supervisor_builder.add_node("customer_service_team", customer_service_team)
supervisor_builder.add_edge(START, "supervisor_node")
supervisor_builder.add_edge("product_team", "supervisor_node")
supervisor_builder.add_edge("location_team", "supervisor_node")
supervisor_builder.add_edge("customer_service_team", END)

checkpointer = InMemorySaver()
supervisor_graph = supervisor_builder.compile()