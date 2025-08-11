from csagent.product.state import ChatWorkflowState
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


def _product_agent_factory(state: ChatWorkflowState, config: RunnableConfig, product: str):
    """
    This is a generic agent for any perfume brand.
    It takes the product name as an argument.
    """
    question = state["question"]
    messages = []

    # Prepare messages for the LLM
    if not messages:
        current_dir = Path(__file__).parent

        product_description_path = f"{current_dir}/../../../resources/products/{product}_{config['configurable']['language']}.md"
        with open(product_description_path, "r") as f:
            product_description = f.read()

        prompt_path = f"{current_dir}/../../../resources/prompts/product_prompt_{config['configurable']['language']}.md"
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
    answer = AIMessage(content=response.content, name=f"{product}_agent")

    return {"messages": [answer]}

def mahsuri_agent(state: ChatWorkflowState, config: RunnableConfig):
    """
    This is Mahsuri Agent, an expert in 'Mahsuri', one of the perfume brands by our company.
    """
    return _product_agent_factory(state, config, "mahsuri")

def man_agent(state: ChatWorkflowState, config: RunnableConfig):
    """
    This is Man Agent, an expert in 'Man', one of the perfume brands by our company.
    """
    return _product_agent_factory(state, config, "man")

def orchid_agent(state: ChatWorkflowState, config: RunnableConfig):
    """
    This is Orchid Agent, an expert in 'Orchid', one of the perfume brands by our company.
    """
    return _product_agent_factory(state, config, "orchid")

def spiritI_agent(state: ChatWorkflowState, config: RunnableConfig):
    """
    This is Spirit I Agent, an expert in 'Spirit I', one of the perfume brands by our company.
    """
    return _product_agent_factory(state, config, "spiritI")

def spiritII_agent(state: ChatWorkflowState, config: RunnableConfig):
    """
    This is Spirit II Agent, an expert in 'Spirit II', one of the perfume brands by our company.
    """
    return _product_agent_factory(state, config, "spiritII")

def threewishes_agent(state: ChatWorkflowState, config: RunnableConfig):
    """
    This is Three Wishes Agent, an expert in 'Three Wishes', one of the perfume brands by our company.
    """
    return _product_agent_factory(state, config, "threewishes")

def violet_agent(state: ChatWorkflowState, config: RunnableConfig):
    """
    This is Violet Agent, an expert in 'Violet', one of the perfume brands by our company.
    """
    return _product_agent_factory(state, config, "violet")

def summary_agent(state: ChatWorkflowState, config: RunnableConfig):
    """
    This is Summary Agent. This agent will formulate the final answer or recommendation for the user based on the final answer. This agent should always be the final step. Only call this agent when you have all the information to answer the question.
    """
    question = state["users_question"]
    # final_answer = state["final_answer"]
    system_prompt = "You are a customer service agent, your task is to answer the customer's question based on the given conversation. Answer the customer's question as if you are talking directly to the customer. Make sure to be concise and to the point. Whenever possible, limit your response to under 200 words. Do not end your response with a question. Be friendly and helpful. Here is the question: {question}."
    messages = state["messages"][1:] + [HumanMessage(content=system_prompt.format(question=question))]

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
    # tasks: str = Field(description="Task that you still need to do in order to answer the user's question.")
    # final_answer: Optional[str] = Field(description="The final answer to the user's question. Keep this empty until you have all the information to answer the question.")

def product_supervisor_node(state: ChatWorkflowState, config: RunnableConfig) -> Command[Literal[*get_agents()]]:
    users_question = state["users_question"]
    messages = state["messages"]

    # Prepare messages for the LLM
    if len(messages) == 0:
        current_dir = Path(__file__).parent

        prompt_path = f"{current_dir}/../../../resources/prompts/supervisor_prompt_{config['configurable']['language']}.md"
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
            question=users_question,
        )
        messages.append(SystemMessage(content=system_prompt))
        # messages.append(HumanMessage(content=question))
    
    instruction_prompt = HumanMessage(content="Now as a supervisor, analyze the steps that have been done and think about what to do next. If you can answer the user's question using the past steps, then pass your answer to the summary agent. Otherwise, break it down into delegated tasks.")
    llm = init_chat_model("google_genai:gemini-2.5-flash", temperature=0).with_structured_output(Router)
    response = llm.invoke(messages + [instruction_prompt])

    # tool_message = ToolMessage(content=f"Tool:{response['next']}",tool_call_id=uuid.uuid4().hex)
    # final_answer = ""
    # if response["final_answer"]:
    #     final_answer = response["final_answer"]

    return Command(goto=response["next"], update={"next": response["next"], "question": response["question"]})