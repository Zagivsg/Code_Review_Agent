import csv
import json
import os
from threading import Lock
from config.settings import TRAINING_LOG_PATH

# A lock to prevent race conditions when multiple workers write to the same file
file_lock = Lock()

# Training data log path is defined in config/settings.py
# For example: TRAINING_LOG_PATH = "training_logs/interactions.csv"

def log_interaction(data: dict):
    """
    Logs a single agent interaction to a file (CSV or JSON).
    The format is determined by the file extension in TRAINING_LOG_PATH.
    """
    if not TRAINING_LOG_PATH:
        print("Warning: TRAINING_LOG_PATH is not set. Skipping interaction logging.")
        return

    # Ensure the directory exists
    os.makedirs(os.path.dirname(TRAINING_LOG_PATH), exist_ok=True)
    
    file_extension = os.path.splitext(TRAINING_LOG_PATH)[1].lower()

    with file_lock:
        if file_extension == '.csv':
            # Check if file exists to determine if we need to write headers
            file_exists = os.path.isfile(TRAINING_LOG_PATH)
            with open(TRAINING_LOG_PATH, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=data.keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerow(data)
        
        elif file_extension == '.jsonl': # Using JSON Lines for efficient appending
            with open(TRAINING_LOG_PATH, 'a', encoding='utf-8') as f:
                f.write(json.dumps(data) + '\n')
        
        else:
            print(f"Warning: Unsupported log format '{file_extension}'. Please use '.csv' or '.jsonl'.")
