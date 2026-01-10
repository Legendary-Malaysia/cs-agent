import logging

from csagent.location.state import LocationWorkflowState
from csagent.configuration import get_model_info, Configuration
from csagent.utils import get_locations, get_resources_dir, read_location

from langgraph.runtime import Runtime
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent
from langchain.agents.middleware import ToolCallLimitMiddleware


logger = logging.getLogger(__name__)

LOCATIONS = get_locations()


def location_agent_node(state: LocationWorkflowState, runtime: Runtime[Configuration]):
    """
    This is Location Agent. This agent will answer the user's question based on the location information.
    """
    try:
        task = state.get("task")

        llm = init_chat_model(
            **get_model_info(runtime.context.model), temperature=0, streaming=False
        )
        tools = [read_location]

        prompt_path = get_resources_dir() / "prompts" / "location_prompt.md"
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_prompt_template = f.read()

        prompt = system_prompt_template.format(locations=", ".join(LOCATIONS))
        agent_executor = create_agent(
            llm,
            tools,
            system_prompt=prompt,
            name="location_agent",
            middleware=[ToolCallLimitMiddleware(run_limit=3)],
        )
        agent_response = agent_executor.invoke(
            {"messages": [HumanMessage(content=f"Here is your task: {task}")]},
            config={"tags": ["location_team"]},
        )

        logger.info(
            f"Location agent response: {agent_response['messages'][-1].content[:50]}"
        )

        return {"response": agent_response["messages"][-1].content}
    except Exception as e:
        logger.exception("Error in location agent node")
        return {"response": f"Location agent error: {str(e)}"}
