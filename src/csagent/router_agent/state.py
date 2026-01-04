from langgraph.graph import MessagesState
from typing import Annotated, Literal, TypedDict
from pydantic import BaseModel, Field
import operator

TEAMS = ["product_team", "location_team", "profile_team"]


class Classification(TypedDict):
    """A single routing decision: which team to call with what query."""

    team: Literal[*TEAMS]
    query: str


class ClassificationResult(BaseModel):
    """Result of classifying a user query into agent-specific sub-questions."""

    classifications: list[Classification] = Field(
        description="List of agents to invoke with their targeted sub-questions"
    )


class RouterWorkflowState(MessagesState):
    """State of the router workflow."""

    classification: list[Classification]
    results: Annotated[list[str], operator.add]


class TeamInput(TypedDict):
    """Simple input state for each team."""

    query: str


class TeamOutput(TypedDict):
    """Output from each team."""

    result: str
