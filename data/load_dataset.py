import json
import csv
import os
import logging
from config.settings import DATASET_PATH

'''
Expected format of the dataset file (.json/.csv)
sample_data = [
        {
            "code": """
import os
def check_path( path):
    if os.path.exists(path)==True:
        print("path exists")
    else:
        return False
""",
            "language": "python"
        },
        {
            "code": """
def calculate_average(numbers):
    total = 0
    for n in numbers:
        total += n
    return total / len(numbers)
""",
            "language": "python"
        },
        {
            "code": """
function greet( name ){
    var message = "Hello, " + name;
    console.log(message)
}
""",
            "language": "javascript"
        }
    ]
'''


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _load_from_csv(path):
    """Loads training data from a CSV log file."""
    dataset = []
    try:
        with open(path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # The PPO trainer expects a tuple of (query, response)
                # Here, we adapt it to our agent's needs: (original_code, language)
                dataset.append((row['original_code'], row['language']))
        logger.info(f"Successfully loaded {len(dataset)} records from {path}")
    except FileNotFoundError:
        logger.error(f"Training log file not found at {path}. Please ensure the service has run and generated logs.")
    except Exception as e:
        logger.error(f"Error loading data from CSV {path}: {e}")
    return dataset

def _load_from_jsonl(path):
    """Loads training data from a JSON Lines log file."""
    dataset = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    dataset.append((data['original_code'], data['language']))
                except json.JSONDecodeError:
                    logger.warning(f"Skipping malformed JSON line in {path}: {line.strip()}")
        logger.info(f"Successfully loaded {len(dataset)} records from {path}")
    except FileNotFoundError:
        logger.error(f"Training log file not found at {path}. Please ensure the service has run and generated logs.")
    except Exception as e:
        logger.error(f"Error loading data from JSONL {path}: {e}")
    return dataset

def load_code_review_data(path):
    """
    Loads the code review training data
    This function is called by `ppo_trainer.py`.
    """
    if not os.path.exists(path):
        logger.warning(f"No training log file found at '{path}'. Cannot start training.")
        return []

    file_extension = os.path.splitext(path)[1].lower()

    if file_extension == '.csv':
        return _load_from_csv(path)
    elif file_extension == '.jsonl':
        return _load_from_jsonl(path)
    else:
        raise ValueError(f"Unsupported log format: '{file_extension}'. Please use '.csv' or '.jsonl'.")
