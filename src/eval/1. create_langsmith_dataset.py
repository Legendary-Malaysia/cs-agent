import os
from utils import create_langsmith_dataset_from_json
from dotenv import load_dotenv

load_dotenv()

current_dir = os.getcwd()
file_path = os.path.join(current_dir, "data.json")
dataset_name = "CS Agent Evaluation"
description = "A dataset of CS Agent Evaluation"

create_langsmith_dataset_from_json(file_path, dataset_name, description)
