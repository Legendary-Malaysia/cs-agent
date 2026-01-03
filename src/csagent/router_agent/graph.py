from langgraph.graph import START, StateGraph, MessagesState, END
from csagent.router_agent.state import (
    RouterWorkflowState,
)
from csagent.router_agent.nodes import (
    classifier_node,
    route_to_teams,
    customer_service_team,
    call_product_team,
    call_location_team,
    call_profile_team,
)
from csagent.configuration import Configuration

# Build the classifier graph
router_builder = StateGraph(
    RouterWorkflowState,
    input_schema=MessagesState,
    context_schema=Configuration,
)

router_builder.add_node("classifier_node", classifier_node)
router_builder.add_node("product_team", call_product_team)
router_builder.add_node("location_team", call_location_team)
router_builder.add_node("profile_team", call_profile_team)
router_builder.add_node("customer_service_team", customer_service_team)
router_builder.add_edge(START, "classifier_node")
router_builder.add_conditional_edges(
    "classifier_node", route_to_teams, ["product_team", "location_team", "profile_team"]
)
router_builder.add_edge("product_team", "customer_service_team")
router_builder.add_edge("location_team", "customer_service_team")
router_builder.add_edge("profile_team", "customer_service_team")
router_builder.add_edge("customer_service_team", END)

router_graph = router_builder.compile()
