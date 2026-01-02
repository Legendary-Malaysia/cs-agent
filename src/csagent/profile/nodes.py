import logging
from pathlib import Path

from langchain.chat_models import init_chat_model
from langgraph.runtime import Runtime
from langchain_core.messages import HumanMessage
from langgraph.config import get_stream_writer

from csagent.configuration import Configuration, get_model_info
from csagent.profile.state import ProfileWorkflowState

logger = logging.getLogger(__name__)


def profile_team_node(state: ProfileWorkflowState, runtime: Runtime[Configuration]):
    logger.info("Call profile team")
    writer = get_stream_writer()
    writer({"custom_key": "Checking company profile..."})

    try:
        task = state["task"]
        model_info = get_model_info(runtime.context.model_medium)

        current_dir = Path(__file__).parent

        prompt_path = (
            current_dir
            / "resources"
            / "prompts"
            / f"prompts_{runtime.context.language}.md"
        )
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        with open(prompt_path, "r") as f:
            system_prompt = f.read()

        profile_path = (
            current_dir
            / "resources"
            / "profiles"
            / f"company_profile_{runtime.context.language}.md"
        )
        if not profile_path.exists():
            raise FileNotFoundError(f"Profile file not found: {profile_path}")
        with open(profile_path, "r") as f:
            profile = f.read()

        instruction = f"""Your task is:{task}"""

        messages = [
            # Using HumanMessage to support Gemma model
            HumanMessage(content=system_prompt),
            HumanMessage(content=profile),
            HumanMessage(content=instruction),
        ]

        llm = init_chat_model(
            **model_info,
            temperature=0,
        )

        response = llm.invoke(messages)

        logger.info(f"Response from profile team: {response.content}")

        response.name = "profile_team"
        return {"response": response.content}
    except Exception:
        logger.exception("Error in profile team node")
        return {"response": "Unexpected error occurred. Please try again later."}
