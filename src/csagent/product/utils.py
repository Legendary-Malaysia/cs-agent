from langchain_core.tools import tool
from langgraph.config import get_stream_writer
from typing import Literal
import os
from pathlib import Path
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
