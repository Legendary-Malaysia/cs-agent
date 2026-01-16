import os
from pathlib import Path
import logging
from typing import Literal
from langchain_core.tools import tool
from langgraph.config import get_stream_writer

logger = logging.getLogger(__name__)


def get_resources_dir():
    cwd = Path(os.getcwd())
    resources_path = cwd / "src" / "csagent" / "resources"
    
    if resources_path.exists():
        return resources_path
    
    return cwd / "resources"


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
        return f"Error in read_location tool: {e!s}"


def get_products():
    products_dir = get_resources_dir() / "products"
    if not products_dir.exists():
        logger.warning(f"Products directory not found: {products_dir}")
        return []
    # Get unique product names by removing the .md extension
    products = {
        file.rsplit(".", 1)[0]
        for file in os.listdir(products_dir)
        if file.endswith(".md")
    }
    return list(products)


PRODUCTS = get_products()


@tool(description="Use this tool to read product information.")
def read_product(product: Literal[*PRODUCTS]) -> str:
    writer = get_stream_writer()
    writer({"custom_key": "A fresh fragrance emerges from " + product})

    if product not in PRODUCTS:
        return (
            f"Product '{product}' not found. Available products: {', '.join(PRODUCTS)}"
        )

    try:
        product_info = read_product_file(product)
    except Exception as e:
        logger.exception("Error in read_product tool")
        return f"Error in read_product tool: {e!s}"
    else:
        return product_info


def read_product_file(product: Literal[*PRODUCTS]) -> str:
    products_dir = get_resources_dir() / "products"
    file_path = products_dir / f"{product}.md"
    if not file_path.exists():
        return f"Product information for '{product}' not available"
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


@tool(
    description="Use this tool to read the company profile, history, core values, contact information, and general information."
)
def read_company_profile() -> str:
    writer = get_stream_writer()
    writer({"custom_key": "The character settles into harmony..."})
    try:
        profiles_dir = get_resources_dir() / "profiles"
        file_path = profiles_dir / "company_profile.md"
        if not file_path.exists():
            return "Company profile not available"
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.exception("Error in read_company_profile tool")
        return f"Error in read_company_profile tool: {e!s}"
