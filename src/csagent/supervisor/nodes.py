from csagent.supervisor.state import SupervisorWorkflowState
from csagent.configuration import Configuration
from langchain_core.runnables import RunnableConfig
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage,ToolMessage
import os
from typing import Literal, TypedDict, Optional
from pathlib import Path
from langgraph.graph import END
from langgraph.types import Command
from pydantic import Field
from csagent.product.graph import product_graph
from csagent.location.graph import location_graph
import logging

logger = logging.getLogger(__name__)

TEAMS = ["product_team", "location_team", "customer_service_team"]
TEAMS_DESC = ["Product Team in charge of answering questions about products. Available products are: Mahsuri, Man, Orchid, Spirit I, Spirit II, Three Wishes, Violet.", "Location Team in charge of answering questions about locations.", "Customer Service Team is the customer facing team. Send your final answer to the customer service team and the team will format the final answer and pass it to the user. Do not pass any tasks to the customer service team."]

class Router(TypedDict):
    """Team to route to next."""
    next: Literal[*TEAMS]
    question: str = Field(description="The question for this team.")
    reason: str = Field(description="The reason for routing to this team.")

def supervisor_node(state: SupervisorWorkflowState, config: RunnableConfig) -> Command[Literal[*TEAMS]]:
    users_question = state["users_question"]
    messages = state["messages"]

    # Prepare messages for the LLM
    if len(messages) == 0:
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
        # messages.append(HumanMessage(content=question))
    
    instruction_prompt = HumanMessage(content="Now as a supervisor, analyze the steps that have been done and think about what to do next. If you can answer the user's question using the past steps, then pass your answer to the summary agent. Otherwise, break it down into delegated tasks.")
    llm = init_chat_model("google_genai:gemini-2.5-flash", temperature=0).with_structured_output(Router)
    response = llm.invoke(messages + [instruction_prompt])


    return Command(goto=response["next"], update={"next": response["next"], "question": response["question"], "messages": AIMessage(content=response["reason"], name="supervisor")})


def call_product_team(state: SupervisorWorkflowState, config: RunnableConfig):
    response = product_graph.invoke({"users_question": state["question"]})
    return Command(goto="supervisor_node", update={"messages": [AIMessage(content=response["response"], name="product_team")]})


def call_location_team(state: SupervisorWorkflowState, config: RunnableConfig):
    response = location_graph.invoke({"users_question": state["question"]})
    return Command(goto="supervisor_node", update={"messages": [AIMessage(content=response["response"], name="location_team")]})


def customer_service_team(state: SupervisorWorkflowState, config: RunnableConfig):
    question = state["users_question"]
    system_prompt = "You are a customer service agent, your task is to answer the customer's question based on the given conversation. Answer the customer's question as if you are talking directly to the customer. Make sure to be concise and to the point. Whenever possible, limit your response to under 200 words. Do not end your response with a question. Be friendly and helpful. Here is the question: {question}."
    messages = state["messages"][1:] + [HumanMessage(content=system_prompt.format(question=question))]

    llm = init_chat_model(config["configurable"]["model"], temperature=0)   
    response = llm.invoke(messages)

    return {"response": response.content}