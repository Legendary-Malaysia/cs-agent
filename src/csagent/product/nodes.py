from csagent.product.state import ProductWorkflowState
from csagent.utils import read_product, get_products, get_resources_dir
from csagent.configuration import get_model_info, Configuration
from langgraph.runtime import Runtime
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage

from langchain.agents import create_agent
from langchain.agents.middleware import ToolCallLimitMiddleware

import logging

logger = logging.getLogger(__name__)


def product_agent_node(state: ProductWorkflowState, runtime: Runtime[Configuration]):
    try:
        task = state.get("task")

        current_dir = get_resources_dir()

        prompt_path = current_dir / "prompts" / "pm_prompt.md"
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_prompt_template = f.read()

        system_prompt = system_prompt_template.format(
            products=get_products(),
        )

        llm = init_chat_model(
            **get_model_info(runtime.context.model),
            temperature=0,
            streaming=False,
        )
        tools = [read_product]

        agent_executor = create_agent(
            llm,
            tools,
            system_prompt=system_prompt,
            name="product_agent",
            middleware=[ToolCallLimitMiddleware(run_limit=3)],
        )
        agent_response = agent_executor.invoke(
            {"messages": [HumanMessage(content=f"Here is your task: {task}")]}
        )
        logger.info(
            f"Product agent response: {agent_response['messages'][-1].content[:50]}"
        )

        return {"response": agent_response["messages"][-1].content}
    except Exception as e:
        logger.exception("Error in product agent node")
        return {"response": f"Product agent error: {str(e)}"}
