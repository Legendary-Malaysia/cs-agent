from csagent.utils import (
    read_product,
    read_location,
    get_resources_dir,
    get_locations,
    read_company_profile,
)
from csagent.configuration import get_model_info, Configuration

from langgraph.runtime import Runtime
from langchain.chat_models import init_chat_model
from langgraph.config import get_stream_writer
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import MessagesState
from langchain.agents import create_agent
from langchain.agents.middleware import ToolCallLimitMiddleware
from langgraph.graph import START, StateGraph, END


import logging

logger = logging.getLogger(__name__)


def react_agent_node(state: MessagesState, runtime: Runtime[Configuration]):
    writer = get_stream_writer()
    writer({"custom_key": "Uncapping the bottle..."})
    logger.info("React agent node")
    language_map = {
        "en": "English",
        "id": "Bahasa Indonesia",
    }
    instruction_map = {
        "en": "Make your first tool call.",
        "id": "Lakukan panggilan tool pertama.",
    }

    try:
        target_language = language_map.get(runtime.context.language, "English")
        resource_dir = get_resources_dir()

        prompt_path = resource_dir / "prompts" / "react_prompt.md"
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_prompt = f.read()

        llm = init_chat_model(
            **get_model_info(runtime.context.model),
            temperature=0,
            streaming=False,
        )
        tools = [read_product, read_location, read_company_profile]

        agent_executor = create_agent(
            llm,
            tools,
            system_prompt=system_prompt.format(
                locations=", ".join(get_locations()), target_language=target_language
            ),
            name="react_agent",
            middleware=[ToolCallLimitMiddleware(run_limit=3)],
        )
        agent_response = agent_executor.invoke(
            {
                "messages": state["messages"]
                + [
                    HumanMessage(
                        content=instruction_map.get(
                            runtime.context.language, instruction_map["en"]
                        )
                    )
                ]
            }
        )
        logger.info("React agent response")

        return {"messages": [agent_response["messages"][-1]]}
    except Exception:
        logger.exception("Error in react agent node")
        return {"messages": [AIMessage(content="React agent error")]}


# Build the profile graph
react_agent_builder = StateGraph(
    MessagesState,
    context_schema=Configuration,
)

react_agent_builder.add_node("react_agent_node", react_agent_node)
react_agent_builder.add_edge(START, "react_agent_node")
react_agent_builder.add_edge("react_agent_node", END)

react_agent_graph = react_agent_builder.compile()
