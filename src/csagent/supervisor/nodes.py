import logging
from typing import Literal

from pathlib import Path

from langchain.chat_models import init_chat_model
from langgraph.runtime import Runtime
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
    get_buffer_string,
)
from langgraph.types import Command
from langgraph.config import get_stream_writer
from pydantic import BaseModel, Field

from csagent.supervisor.state import SupervisorWorkflowState
from csagent.configuration import Configuration, get_model_info
from csagent.product.graph import product_graph
from csagent.location.graph import location_graph
from csagent.profile.graph import profile_graph


logger = logging.getLogger(__name__)

TEAMS = ["product_team", "location_team", "profile_team", "customer_service_team"]


class Router(BaseModel):
    """Team to route to next."""

    next_step: Literal[*TEAMS]
    task: str = Field(description="The task for this team.")
    reason: str = Field(description="The reason for routing to this team.")


def supervisor_node(
    state: SupervisorWorkflowState, runtime: Runtime[Configuration]
) -> Command[Literal[*TEAMS]]:
    logger.info("Supervisor node")
    writer = get_stream_writer()
    writer({"custom_key": "One moment..."})

    try:
        if not state["messages"]:
            raise ValueError("No messages in state")

        messages = state["messages"]

        model_info = get_model_info(runtime.context.model)

        system_prompt = None  # Initialize to avoid NameError
        # Check if we need to inject the system prompt
        if not isinstance(messages[0], SystemMessage):
            logger.info("Preparing SystemMessage Supervisor:")
            current_dir = Path(__file__).parent

            prompt_path = (
                current_dir
                / "resources"
                / "prompts"
                / f"supervisor_prompt_{runtime.context.language}.md"
            )
            if not prompt_path.exists():
                raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
            with open(prompt_path, "r") as f:
                system_prompt_template = f.read()

            system_prompt = SystemMessage(content=system_prompt_template)

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
            **model_info, temperature=0, streaming=False
        ).with_structured_output(Router)
        final_prompt = (
            [system_prompt, *messages, instruction_prompt]
            if system_prompt
            else [*messages, instruction_prompt]
        )
        response = llm.invoke(final_prompt)
        logger.info(f"Response: {response.reason}")

        return Command(
            goto=response.next_step,
            update={
                "next_step": response.next_step,
                "task": response.task,
            },
        )
    except Exception:
        logger.exception("Error in supervisor node")
        return Command(
            goto="customer_service_team",
            update={
                "next_step": "customer_service_team",
                "task": "Unexpected error occurred. Please try again later.",
            },
        )


def call_product_team(state: SupervisorWorkflowState, runtime: Runtime[Configuration]):
    logger.info("Call product team")
    writer = get_stream_writer()
    writer({"custom_key": "Looking up product details..."})

    try:
        response = product_graph.invoke(
            {"task": state["task"]}, context=runtime.context
        )

        logger.info(f"Response from product team: {response['response']}")
        writer({"custom_key": "Product details found"})

        return Command(
            goto="supervisor_node",
            update={
                "notes": [
                    f"Product Team Task: {state['task']}\n  Product Team Response: {response['response']}"
                ]
            },
        )
    except Exception:
        logger.exception("Error in product team node")
        return Command(
            goto="supervisor_node",
            update={
                "notes": [
                    f"Product Team Task: {state['task']}\n  Product Team Response: Error in product team node"
                ]
            },
        )


def call_location_team(state: SupervisorWorkflowState, runtime: Runtime[Configuration]):
    logger.info("Call location team")
    writer = get_stream_writer()
    writer({"custom_key": "Looking up location details..."})

    try:
        response = location_graph.invoke(
            {"task": state["task"]}, context=runtime.context
        )

        logger.info(f"Response from location team: {response['response']}")
        writer({"custom_key": "Location details found"})

        return Command(
            goto="supervisor_node",
            update={
                "notes": [
                    f"Location Team Task: {state['task']}\n  Location Team Response: {response['response']}"
                ]
            },
        )
    except Exception:
        logger.exception("Error in location team node")
        return Command(
            goto="supervisor_node",
            update={
                "notes": [
                    f"Location Team Task: {state['task']}\n  Location Team Response: Error in location team node"
                ]
            },
        )

def call_profile_team(state: SupervisorWorkflowState, runtime: Runtime[Configuration]):
    logger.info("Call profile team")
    writer = get_stream_writer()
    writer({"custom_key": "Looking up profile details..."})

    try:
        response = profile_graph.invoke(
            {"task": state["task"]}, context=runtime.context
        )

        logger.info(f"Response from profile team: {response['response']}")
        writer({"custom_key": "Profile details found"})

        return Command(
            goto="supervisor_node",
            update={
                "notes": [
                    f"Profile Team Task: {state['task']}\n  Profile Team Response: {response['response']}"
                ]
            },
        )
    except Exception:
        logger.exception("Error in profile team node")
        return Command(
            goto="supervisor_node",
            update={
                "notes": [
                    f"Profile Team Task: {state['task']}\n  Profile Team Response: Error in profile team node"
                ]
            },
        )

def customer_service_team(
    state: SupervisorWorkflowState, runtime: Runtime[Configuration]
):
    logger.info("Call customer service team")
    writer = get_stream_writer()
    writer({"custom_key": "Finalizing answer..."})

    try:
        task = state["task"]
        conversation = get_buffer_string(state["messages"])
        model_info = get_model_info(runtime.context.model_small)

        current_dir = Path(__file__).parent

        prompt_path = (
            current_dir
            / "resources"
            / "prompts"
            / f"cs_prompt_{runtime.context.language}.md"
        )
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        with open(prompt_path, "r") as f:
            system_prompt = f.read()

        notes = "\n-----\n".join(state["notes"])

        instruction = f"""
            Here is the conversation so far:
            <Conversation>
            {conversation}
            </Conversation>
            ----- 

            Information that our team has gathered so far (if any):
            <Information>
            {notes}
            </Information>
            ----- 

            Your task is:
            {task}
        """

        messages = [
            # Using HumanMessage to support Gemma model
            HumanMessage(content=system_prompt),
            HumanMessage(content=instruction),
        ]

        llm = init_chat_model(
            **model_info,
            temperature=0,
        )

        response = llm.invoke(messages)

        logger.info(f"Response from customer service team: {response.content}")

        response.name = "customer_service_team"
        return {"messages": [response]}
    except Exception:
        logger.exception("Error in customer service team node")
        return {
            "messages": [
                AIMessage(
                    content="Unexpected error occurred. Please try again later.",
                    name="customer_service_team",
                )
            ]
        }
