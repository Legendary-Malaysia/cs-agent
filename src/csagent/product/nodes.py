from csagent.product.state import ProductWorkflowState
from csagent.configuration import get_model_info, Configuration
from langgraph.runtime import Runtime
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from typing import Literal
import os
from pathlib import Path
from langchain.agents import create_agent
from langchain_core.tools import tool
from langgraph.config import get_stream_writer
import logging

logger = logging.getLogger(__name__)


def get_resources_dir():
    current_dir = Path(__file__).parent
    return current_dir / "resources"


def get_products():
    products_dir = get_resources_dir() / "products"
    if not products_dir.exists():
        logger.warning(f"Products directory not found: {products_dir}")
        return []
    # Get unique product names and remove the language suffix
    products = {
        file.rsplit("_", 1)[0]
        for file in os.listdir(products_dir)
        if file.endswith(".md")
    }
    return list(products)


@tool(description="Use this tool to read product information.")
def read_product(product: str, language: Literal["en"]) -> str:
    writer = get_stream_writer()
    writer({"custom_key": "Gathering information about " + product})

    available_products = get_products()
    if product not in available_products:
        return f"Product '{product}' not found. Available products: {', '.join(available_products)}"

    try:
        products_dir = get_resources_dir() / "products"
        file_path = products_dir / f"{product}_{language}.md"
        if not file_path.exists():
            return f"Product information for '{product}' not available in language '{language}'"
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.exception("Error in read_product tool")
        return f"Error in read_product tool: {str(e)}"


def product_agent_node(state: ProductWorkflowState, runtime: Runtime[Configuration]):
    try:
        task = state["task"]

        current_dir = get_resources_dir()

        prompt_path = (
            current_dir / "prompts" / f"pm_prompt_{runtime.context.language}.md"
        )
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        with open(prompt_path, "r") as f:
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
            llm, tools, system_prompt=system_prompt, name="product_agent"
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
