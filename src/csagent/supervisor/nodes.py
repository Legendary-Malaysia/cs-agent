from csagent.supervisor.state import SupervisorWorkflowState
from csagent.configuration import get_model_info
from langchain_core.runnables import RunnableConfig
from langchain.chat_models import init_chat_model

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from typing import Literal, TypedDict
from pathlib import Path
from langgraph.types import Command
from pydantic import Field
from csagent.product.graph import product_graph
from csagent.location.graph import location_graph
import logging

logger = logging.getLogger(__name__)

TEAMS = ["product_team", "location_team", "customer_service_team"]
TEAMS_DESC = [
    "Product Team in charge of answering questions about products. Available products are: Mahsuri, Man, Orchid, Spirit I, Spirit II, Three Wishes, Violet.",
    "Location Team in charge of answering questions about locations.",
    "Customer Service Team is the customer facing team. If sufficient data is available, then call the customer service team. Otherwise, delegate the task to the appropriate team.",
]


class Router(TypedDict):
    """Team to route to next."""

    next: Literal[*TEAMS]
    task: str = Field(description="The task for this team.")
    reason: str = Field(description="The reason for routing to this team.")


def supervisor_node(
    state: SupervisorWorkflowState, config: RunnableConfig
) -> Command[Literal[*TEAMS]]:
    logger.info("Supervisor node")
    users_question = state["users_question"]
    messages = state["messages"]
    model_info = get_model_info(config["configurable"]["model"])

    # Prepare messages for the LLM
    if len(messages) == 0:
        logger.info(f"Preparing messages for the LLM: {users_question}")
        current_dir = Path(__file__).parent

        prompt_path = (
            current_dir
            / "resources"
            / "prompts"
            / f"supervisor_prompt_{config['configurable']['language']}.md"
        )
        with open(prompt_path, "r") as f:
            system_prompt_template = f.read()

        members_str = "\n---\n".join(
            [
                f"Team: {team_name}\nDescription: {desc}"
                for team_name, desc in zip(TEAMS, TEAMS_DESC)
            ]
        )

        system_prompt = system_prompt_template.format(members=members_str)
        messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=users_question))

    notes = "\n-----\n".join(state["notes"])
    instruction_prompt = HumanMessage(
        content=f"""
            Information that our team has gathered so far (if any):
            {notes}
            
            -----

            Now as a supervisor, analyze the information and think about what to do next. If you have enough information to answer the user's question, then pass your answer to the customer service team. Otherwise, delegate the next task to the appropriate team.
        """
    )

    llm = init_chat_model(
        **model_info,
        temperature=0,
    ).with_structured_output(Router)
    response = llm.invoke(messages + [instruction_prompt])
    logger.info(f"Response: {response['reason']}")

    return Command(
        goto=response["next"],
        update={
            "next": response["next"],
            "task": response["task"],
        },
    )


def call_product_team(state: SupervisorWorkflowState, config: RunnableConfig):
    logger.info("Call product team")
    response = product_graph.invoke({"task": state["task"]})
    logger.info(f"Response from product team: {response['response']}")
    return Command(
        goto="supervisor_node",
        update={
            "messages": [AIMessage(content=response["response"], name="product_team")]
        },
    )


def call_location_team(state: SupervisorWorkflowState, config: RunnableConfig):
    logger.info("Call location team")
    response = location_graph.invoke({"task": state["task"]})
    logger.info(f"Response from location team: {response['response']}")
    return Command(
        goto="supervisor_node",
        update={
            "notes": [f"Location Team Task: {state['task']}\n  Location Team Response: {response['response']}"]
        },
    )


def customer_service_team(state: SupervisorWorkflowState, config: RunnableConfig):
    logger.info("Call customer service team")
    task = state["task"]
    users_question = state["users_question"]
    model_info = get_model_info(config["configurable"]["model_small"])

    current_dir = Path(__file__).parent

    prompt_path = (
        current_dir
        / "resources"
        / "prompts"
        / f"cs_prompt_{config['configurable']['language']}.md"
    )
    with open(prompt_path, "r") as f:
        system_prompt = f.read()

    notes = "\n-----\n".join(state["notes"])

    instruction = f"""
        Here is the inquiries:
        <HumanQuestion>
        {users_question}
        </HumanQuestion>

        Information that our team has gathered so far (if any):
        {notes}

        ----- 

        Your task is:
        {task}
    """

    messages = [
        HumanMessage(content=system_prompt),
        HumanMessage(content=instruction),
    ]

    llm = init_chat_model(
        **model_info,
        temperature=0,
    )

    response = llm.invoke(messages)

    logger.info(f"Response from customer service team: {response.content}")
    return {
        "messages": [AIMessage(content=response.content, name="customer_service_team")]
    }
