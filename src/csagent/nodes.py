from csagent.state import ChatWorkflowState
from csagent.configuration import Configuration
from langchain_core.runnables import RunnableConfig
import random
from langchain.chat_models import init_chat_model
# from langchain.schema import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage,ToolMessage
import os
from typing import Literal, TypedDict, Optional
from pathlib import Path
from langgraph.graph import END
from langgraph.types import Command
from pydantic import Field
import inspect


def orchid_agent(state: ChatWorkflowState, config: RunnableConfig):
    """
    This is Orchid Agent, an expert in orchid.
    """
    question = state["question"]
    product = "orchid"
    messages = []

    # Prepare messages for the LLM
    if len(messages) == 0:
        current_dir = Path(__file__).parent

        product_description = f"{current_dir}/../../resources/products/{product}_{config['configurable']['language']}.md"
        with open(product_description, "r") as f:
            product_description = f.read()

        prompt_path = f"{current_dir}/../../resources/prompts/product_prompt_{config['configurable']['language']}.md"
        with open(prompt_path, "r") as f:
            system_prompt_template = f.read()

        system_prompt = system_prompt_template.format(
            product=product,
            question=question,
            product_description=product_description,
        )
        messages.append(SystemMessage(content=system_prompt))
    messages.append(HumanMessage(content=question))

    llm = init_chat_model(config["configurable"]["model"], temperature=1)
    response = llm.invoke(messages)
    answer = HumanMessage(content=response.content, name="orchid_agent")

    return {"messages": [answer]}

def violet_agent(state: ChatWorkflowState, config: RunnableConfig):
    """
    This is Violet Agent, an expert in violet.
    """
    question = state["question"]
    product = "violet"
    messages = []

    # Prepare messages for the LLM
    if len(messages) == 0:
        current_dir = Path(__file__).parent

        product_description = f"{current_dir}/../../resources/products/{product}_{config['configurable']['language']}.md"
        with open(product_description, "r") as f:
            product_description = f.read()

        prompt_path = f"{current_dir}/../../resources/prompts/product_prompt_{config['configurable']['language']}.md"
        with open(prompt_path, "r") as f:
            system_prompt_template = f.read()

        system_prompt = system_prompt_template.format(
            product=product,
            question=question,
            product_description=product_description,
        )
        messages.append(SystemMessage(content=system_prompt))
    messages.append(HumanMessage(content=question))

    llm = init_chat_model(config["configurable"]["model"], temperature=1)
    response = llm.invoke(messages)
    answer = HumanMessage(content=response.content, name="violet_agent")

    return {"messages": [answer]}

def summary_agent(state: ChatWorkflowState, config: RunnableConfig):
    """
    This is Summary Agent, an expert in summary.
    """
    question = state["question"]
    final_answer = state["final_answer"]
    system_prompt = "You are a summary agent, your task is to answer the user's question based on the final answer. Make sure to limit your response to under 200 words. Do not end your response with a question. Be friendly and helpful. Here is the question: {question}. Here is the final answer: {final_answer}"
    messages = [HumanMessage(content=system_prompt.format(question=question, final_answer=final_answer))]

    llm = init_chat_model(config["configurable"]["model"], temperature=0)   
    response = llm.invoke(messages)

    return {"response": response.content}


def _collect_agents_with_docs():
    """Collect all agent functions from current module"""
    current_module = inspect.getmodule(inspect.currentframe())
    agents = []
    for name, func in inspect.getmembers(current_module, inspect.isfunction):
        if name.endswith("_agent") and func.__module__ == current_module.__name__:
            docstring = inspect.getdoc(func) or "No docstring found."
            agents.append((name, docstring))
    return agents


# Cache the agent data
AGENT_DATA = _collect_agents_with_docs()
AGENT_NAMES = [name for name, _ in AGENT_DATA]


def get_agents():
    return AGENT_NAMES


def get_agents_with_docs():
    return AGENT_DATA

class Router(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""
    next: Literal[*get_agents()]
    question: str = Field(description="The question for this agent.")
    reason: str = Field(description="The reason for routing to this agent.")
    final_answer: Optional[str] = Field(description="The final answer for this agent.")

def product_supervisor_node(state: ChatWorkflowState, config: RunnableConfig) -> Command[Literal[*get_agents()]]:
    question = state["question"]
    messages = state["messages"]

    # Prepare messages for the LLM
    if len(messages) == 0:
        current_dir = Path(__file__).parent

        prompt_path = f"{current_dir}/../../resources/prompts/supervisor_prompt_{config['configurable']['language']}.md"
        with open(prompt_path, "r") as f:
            system_prompt_template = f.read()

        agents_str = "\n---\n".join(
            [
                f"Agent: {agent_name}\nDescription: {docstring}"
                for agent_name, docstring in get_agents_with_docs()
            ]
        )

        system_prompt = system_prompt_template.format(
            members=get_agents(),
            agents=agents_str,
        )
        messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=question))
    
    instruction_prompt = HumanMessage(content="Now as a supervisor, analyze the steps that have been done and think about what to do next. If you can answer the user's question using the past steps, then pass your answer to the summary agent. Otherwise, break it down into delegated tasks.")
    llm = init_chat_model(config["configurable"]["model"], temperature=0).with_structured_output(Router)
    response = llm.invoke(messages + [instruction_prompt])

    # tool_message = ToolMessage(content=f"Tool:{response['next']}",tool_call_id=uuid.uuid4().hex)
    final_answer = ""
    if response["final_answer"]:
        final_answer = response["final_answer"]

    return Command(goto=response["next"], update={"next": response["next"], "question": response["question"], "final_answer": final_answer})