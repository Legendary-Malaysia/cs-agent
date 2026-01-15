import os
import json
from logging import getLogger
from datetime import datetime
from typing import Callable
from langsmith import Client
from langsmith.schemas import Dataset


logger = getLogger(__name__)


def load_data_from_json(file_path: str) -> list[dict]:
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
) -> Dataset:
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


def add_new_examples_to_dataset(
    client: Client, dataset_id: str, all_items: list[dict]
) -> None:
    """Adds new examples to the specified dataset."""

    # 1. Fetch existing examples (inputs) to compare
    # Note: list_examples returns an iterator of Example objects
    existing_examples = client.list_examples(dataset_id=dataset_id)

    # 2. Create a set of "fingerprints" for existing items
    # We use a JSON string of the inputs as a unique key
    existing_fingerprints = {
        json.dumps(ex.inputs, sort_keys=True) for ex in existing_examples
    }

    # 3. Filter all_items to find truly new items
    new_items = []
    for item in all_items:
        # 'item' should match the structure {"inputs": {...}, "outputs": {...}}
        fingerprint = json.dumps(item["inputs"], sort_keys=True)
        if fingerprint not in existing_fingerprints:
            new_items.append(item)
            # Add to set immediately to prevent duplicates within the new batch itself
            existing_fingerprints.add(fingerprint)

    # 4. Add only the filtered items
    if new_items:
        client.create_examples(dataset_id=dataset_id, examples=new_items)
        logger.info("Added %d new examples to dataset.", len(new_items))
    else:
        logger.info("No new unique examples to add.")


def create_langsmith_dataset_from_json(
    file_path: str, dataset_name: str, description: str
) -> bool:
    """Orchestrate the creation of a LangSmith dataset from a file."""

    try:
        all_items = load_data_from_json(file_path)
    except (FileNotFoundError, json.JSONDecodeError):
        logger.exception("Failed to load data from %s", file_path)
        return False

    client = Client()

    dataset = get_or_create_langsmith_dataset(client, dataset_name, description)
    add_new_examples_to_dataset(client, dataset.id, all_items)

    logger.info("Dataset operation complete for %s.", dataset_name)

    return True


def run_langsmith_eval(
    target_function: Callable,
    dataset_name: str,
    evaluators: list,
    model: str,
    split_name: str = None,
) -> None:
    """
    Run langsmith evaluation pipeline for the specified dataset.
    """

    client = Client()

    # If a split is provided, fetch only those examples
    # Otherwise, use the dataset name string to run on all examples
    if split_name:
        data = client.list_examples(dataset_name=dataset_name, splits=[split_name])
        experiment_prefix = (
            f"{model} {split_name} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
    else:
        data = dataset_name
        experiment_prefix = f"{model} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    experiment_results_workflow = client.evaluate(
        # Run agent
        target_function,
        # Dataset name
        data=data,
        # Evaluator
        evaluators=evaluators,
        # Name of the experiment
        experiment_prefix=experiment_prefix,
        # Number of concurrent evaluations
        max_concurrency=1,
        # upload_results=False,
    )

    logger.info("Evaluation operation complete: %s", experiment_results_workflow)
