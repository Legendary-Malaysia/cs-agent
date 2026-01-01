import os
import json
from logging import getLogger
from datetime import datetime
from typing import Callable
from langsmith import Client


logger = getLogger(__name__)


def load_data_from_json(file_path: str):
    """Load data from a JSON file, raising an error if it doesn't exist."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File {file_path} does not exist")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.exception("Failed to decode JSON from %s", file_path)
        raise


def get_or_create_langsmith_dataset(
    client: Client, dataset_name: str, description: str
):
    """Checks for an existing dataset or creates a new one."""
    if client.has_dataset(dataset_name=dataset_name):
        logger.info("Dataset %s already exists", dataset_name)
        return client.read_dataset(dataset_name=dataset_name)
    else:
        dataset = client.create_dataset(
            dataset_name=dataset_name,
            description=description,
        )
        logger.info("Created dataset: %s", dataset_name)
        return dataset


def add_new_examples_to_dataset(client: Client, dataset_id, all_items):
    """Adds new examples to the specified dataset."""

    client.create_examples(dataset_id=dataset_id, examples=all_items)
    logger.info("Added %d examples to dataset.", len(all_items))


def create_langsmith_dataset_from_json(
    file_path: str, dataset_name: str, description: str
):
    """Orchestrate the creation of a LangSmith dataset from a file."""

    try:
        all_items = load_data_from_json(file_path)
    except (FileNotFoundError, json.JSONDecodeError):
        logger.exception(f"Failed to load data from {file_path}")
        return

    client = Client()

    dataset = get_or_create_langsmith_dataset(client, dataset_name, description)
    add_new_examples_to_dataset(client, dataset.id, all_items)

    logger.info("Dataset operation complete for %s.", dataset_name)


def run_langsmith_eval(
    target_function: Callable, dataset_name: str, evaluators: list, model: str
):
    """
    Run langsmith evaluation pipeline for the specified dataset.
    """

    client = Client()
    experiment_results_workflow = client.evaluate(
        # Run agent
        target_function,
        # Dataset name
        data=dataset_name,
        # Evaluator
        evaluators=evaluators,
        # Name of the experiment
        experiment_prefix=f"{model} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        # Number of concurrent evaluations
        max_concurrency=1,
        # upload_results=False,
    )

    print("Evaluation operation complete.", experiment_results_workflow)
