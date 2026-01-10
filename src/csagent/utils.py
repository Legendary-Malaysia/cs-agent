import os
from pathlib import Path
import logging
from typing import Literal
from langchain_core.tools import tool
from langgraph.config import get_stream_writer

logger = logging.getLogger(__name__)


def get_resources_dir():
    current_dir = Path(__file__).parent
    return current_dir / "resources"


def get_locations():
    locations_dir = get_resources_dir() / "locations"
    if not locations_dir.exists():
        logger.warning(f"Locations directory not found: {locations_dir}")
        return []
    locations = [
        file[:-3] for file in os.listdir(locations_dir) if file.endswith(".md")
    ]
    return locations


LOCATIONS = get_locations()


@tool(description="Use this tool to read location information")
def read_location(location: Literal[*LOCATIONS]):
    writer = get_stream_writer()
    writer({"custom_key": "Anchoring the scent into location..."})

    if location not in LOCATIONS:
        return f"Location {location} not found. Available locations: {', '.join(LOCATIONS)}"

    try:
        locations_dir = get_resources_dir() / "locations"
        with open(locations_dir / f"{location}.md", "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.exception("Error in read_location tool")
        return f"Error in read_location tool: {str(e)}"
