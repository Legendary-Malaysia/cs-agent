from csagent.supervisor.state import SupervisorWorkflowState
from csagent.configuration import get_model_info
from langchain_core.runnables import RunnableConfig
from langchain.chat_models import init_chat_model

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
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
    "Customer Service Team is the customer facing team. Send your final answer to the customer service team and the team will format the final answer and pass it to the user. Do not pass any tasks to the customer service team.",
]


class Router(TypedDict):
    """Team to route to next."""

    next: Literal[*TEAMS]
    question: str = Field(description="The question for this team.")
    reason: str = Field(description="The reason for routing to this team.")


async def supervisor_node(
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

        prompt_path = f"{current_dir}/../../../resources/prompts/supervisor_prompt_{config['configurable']['language']}.md"
        with open(prompt_path, "r") as f:
            system_prompt_template = f.read()

        members_str = "\n---\n".join(
            [
                f"Team: {team_name}\nDescription: {desc}"
                for team_name, desc in zip(TEAMS, TEAMS_DESC)
            ]
        )

        system_prompt = system_prompt_template.format(
            members=members_str,
            question=users_question,
        )
        messages.append(SystemMessage(content=system_prompt))

    instruction_prompt = HumanMessage(
        content="Now as a supervisor, analyze the steps that have been done and think about what to do next. If you can answer the user's question using the past steps, then pass your answer to the summary agent. Otherwise, break it down into delegated tasks."
    )

    llm = init_chat_model(
        **model_info,
        temperature=0,
    ).with_structured_output(Router)
    response = await llm.ainvoke(messages + [instruction_prompt])
    logger.info(f"Response: {response['reason']}")

    return Command(
        goto=response["next"],
        update={
            "next": response["next"],
            "question": response["question"],
            "messages": AIMessage(content=response["reason"], name="supervisor"),
        },
    )


def call_product_team(state: SupervisorWorkflowState, config: RunnableConfig):
    logger.info(f"Call product team")
    response = product_graph.invoke({"users_question": state["question"]})
    logger.info(f"Response from product team: {response['response']}")
    return Command(
        goto="supervisor_node",
        update={
            "messages": [
                HumanMessage(content=response["response"], name="product_team")
            ]
        },
    )


def call_location_team(state: SupervisorWorkflowState, config: RunnableConfig):
    logger.info(f"Call location team")
    response = location_graph.invoke({"users_question": state["question"]})
    logger.info(f"Response from location team: {response['response']}")
    return Command(
        goto="supervisor_node",
        update={
            "messages": [
                HumanMessage(content=response["response"], name="location_team")
            ]
        },
    )


def customer_service_team(state: SupervisorWorkflowState, config: RunnableConfig):
    logger.info(f"Call customer service team")
    question = state["users_question"]
    model_info = get_model_info(config["configurable"]["model_small"])

    current_dir = Path(__file__).parent

    prompt_path = f"{current_dir}/../../../resources/prompts/cs_prompt_{config['configurable']['language']}.md"
    with open(prompt_path, "r") as f:
        system_prompt_template = f.read()
    system_prompt = system_prompt_template.format(question=question)
    messages = state["messages"][1:] + [HumanMessage(content=system_prompt)]

    llm = init_chat_model(
        **model_info,
        temperature=0,
    )

    response = llm.invoke(messages)

    logger.info(f"Response from customer service team: {response.content}")
    return {"response": response.content}
