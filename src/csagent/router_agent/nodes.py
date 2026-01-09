import logging
from pathlib import Path

from langchain.chat_models import init_chat_model
from langgraph.runtime import Runtime
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
    get_buffer_string,
)
from langgraph.types import Send
from langgraph.config import get_stream_writer

from csagent.router_agent.state import (
    RouterWorkflowState,
    ClassificationResult,
    TeamInput,
)
from csagent.configuration import Configuration, get_model_info
from csagent.product.graph import product_graph
from csagent.location.graph import location_graph
from csagent.profile.graph import profile_graph


logger = logging.getLogger(__name__)


def classifier_node(
    state: RouterWorkflowState, runtime: Runtime[Configuration]
) -> dict:
    logger.info("Classifier node")
    writer = get_stream_writer()
    writer({"custom_key": "Uncapping the bottle..."})

    try:
        if not state["messages"]:
            raise ValueError("No messages in state")

        messages = state["messages"]

        model_info = get_model_info(runtime.context.model)

        # Check if we need to inject the system prompt
        if isinstance(messages[0], SystemMessage):
            final_prompt = messages
        else:
            logger.info("Preparing SystemMessage Classifier:")
            current_dir = Path(__file__).parent

            prompt_path = current_dir / "resources" / "prompts" / "classifier_prompt.md"
            if not prompt_path.exists():
                raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
            with open(prompt_path, "r") as f:
                system_prompt_template = f.read()

            system_prompt = SystemMessage(content=system_prompt_template)
            final_prompt = [system_prompt, *messages]

        llm = init_chat_model(
            **model_info, temperature=0, streaming=False
        ).with_structured_output(ClassificationResult)
        response = llm.invoke(final_prompt)
        logger.info(f"Response: {response}")

        return {"classification": response.classifications}
    except Exception:
        logger.exception("Error in classifier node")
        return {
            "classification": [
                {
                    "team": "profile_team",
                    "query": "Unexpected error occurred. Please try again later.",
                }
            ]
        }


def route_to_teams(state: RouterWorkflowState) -> list[Send]:
    """Fan out to agents based on classifications."""
    return [Send(c["team"], {"query": c["query"]}) for c in state["classification"]]


def call_product_team(state: TeamInput, runtime: Runtime[Configuration]) -> dict:
    logger.info("Call product team")
    writer = get_stream_writer()
    writer({"custom_key": "Opening the vial..."})

    try:
        response = product_graph.invoke(
            {"task": state["query"]}, context=runtime.context
        )

        logger.info(f"Response from product team: {response['response']}")
        writer({"custom_key": "The essence grows richer..."})

        return {"results": [response["response"]]}
    except Exception:
        logger.exception("Error in product team node")
        return {"results": ["Product team encountered unexpected error"]}


def call_location_team(state: TeamInput, runtime: Runtime[Configuration]) -> dict:
    logger.info("Call location team")
    writer = get_stream_writer()
    writer({"custom_key": "Unfolding the map..."})

    try:
        response = location_graph.invoke(
            {"task": state["query"]}, context=runtime.context
        )

        logger.info(f"Response from location team: {response['response']}")
        writer({"custom_key": "The trail lingers..."})

        return {"results": [response["response"]]}
    except Exception:
        logger.exception("Error in location team node")
        return {"results": ["Location team encountered unexpected error"]}


def call_profile_team(state: TeamInput, runtime: Runtime[Configuration]) -> dict:
    logger.info("Call profile team")
    writer = get_stream_writer()
    writer({"custom_key": "An aura of presence unfolds..."})

    try:
        response = profile_graph.invoke(
            {"task": state["query"]}, context=runtime.context
        )

        logger.info(f"Response from profile team: {response['response']}")
        writer({"custom_key": "Weaving a lasting impression..."})

        return {"results": [response["response"]]}
    except Exception:
        logger.exception("Error in profile team node")
        return {"results": ["Profile team encountered unexpected error"]}


def customer_service_team(
    state: RouterWorkflowState, runtime: Runtime[Configuration]
) -> dict:
    logger.info("Call customer service team")
    writer = get_stream_writer()
    writer({"custom_key": "Blending the scents into symphony..."})
    language_map = {
        "en": "English",
        "id": "Bahasa Indonesia",
    }
    target_language = language_map.get(runtime.context.language, "English")

    try:
        conversation = get_buffer_string(state["messages"])
        model_info = get_model_info(runtime.context.model_small)

        current_dir = Path(__file__).parent

        prompt_path = current_dir / "resources" / "prompts" / "cs_prompt.md"
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        with open(prompt_path, "r") as f:
            system_prompt = f.read()

        results = state.get("results", [])
        results_text = (
            "\n-----\n".join(results) if results else "No information gathered yet."
        )

        instruction = f"""
            Here is the conversation so far:
            <Conversation>
            {conversation}
            </Conversation>
            ----- 

            Information that our team has gathered so far (if any):
            <Information>
            {results_text}
            </Information>
            ----- 

            Your task is to combine information from multiple sources without redundancy. Keep the response concise and well-organized. Make sure to reply in {target_language}.
        """

        messages = [
            # Using HumanMessage to support Gemma model
            HumanMessage(content=system_prompt),
            HumanMessage(content=instruction),
        ]

        llm = init_chat_model(
            **model_info,
            temperature=0.8,
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
