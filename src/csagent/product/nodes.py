from csagent.product.state import ProductWorkflowState
from csagent.configuration import get_model_info
from langchain_core.runnables import RunnableConfig
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from typing import Literal
import os
from pathlib import Path
from langchain.agents import create_agent
from langchain_core.tools import tool
import logging

logger = logging.getLogger(__name__)


def get_resources_dir():
    current_dir = Path(__file__).parent
    return current_dir / "resources"


def get_products():
    products_dir = get_resources_dir() / "products"
    # Get unique product names and remove the language suffix
    products = {
        file.rsplit("_", 1)[0]
        for file in os.listdir(products_dir)
        if file.endswith(".md")
    }
    return list(products)


@tool(
    description=f"Use this tool to read product information. The available products are: {', '.join(get_products())}"
)
def read_product(
    product: Literal[*get_products()], language: Literal["en", "jp", "zh"]
) -> str:
    try:
        products_dir = get_resources_dir() / "products"
        with open(
            products_dir / f"{product}_{language}.md", "r", encoding="utf-8"
        ) as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error in read_product tool: {e}")
        return f"Error in read_product tool: {str(e)}"


def product_agent_node(state: ProductWorkflowState, config: RunnableConfig):
    try:
        task = state["task"]

        current_dir = get_resources_dir()

        prompt_path = (
            current_dir
            / "prompts"
            / f"pm_prompt_{config['configurable']['language']}.md"
        )
        with open(prompt_path, "r") as f:
            system_prompt_template = f.read()

        system_prompt = system_prompt_template.format(
            products=get_products(),
        )

        llm = init_chat_model(
            **get_model_info(config["configurable"]["model"]),
            temperature=0,
        )
        tools = [read_product]

        agent_executor = create_agent(
            llm, tools, system_prompt=system_prompt, name="product_agent"
        )
        agent_response = agent_executor.invoke(
            {"messages": [HumanMessage(content=f"Here is your task: {task}")]}
        )
        logger.info(
            f"Location agent response: {agent_response['messages'][-1].content[:50]}"
        )

        return {"response": agent_response["messages"][-1].content}
    except Exception as e:
        logger.error(f"Error in product supervisor node: {e}")
        return {"response": f"Product supervisor error: {str(e)}"}
