# Configuration file 
import os

# Model settings
MODEL_NAME = "codellama/CodeLlama-7b-Instruct-hf"  # Or "Salesforce/codet5p-220m"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# PPO Training settings for the TRL library
PPO_CONFIG = {
    "model_name": MODEL_NAME,
    "learning_rate": 1.41e-5,
    "ppo_epochs": 4,          # Number of optimization epochs per batch
    "mini_batch_size": 4,     # Mini-batch size for PPO updates
    "batch_size": 16,         # Number of queries to process before an optimization step
    "log_with": None,         # Set to "wandb" to log with Weights & Biases
}

# QLoRA configuration for PEFT (Parameter-Efficient Fine-Tuning)
LORA_CONFIG = {
    "r": 16,                  # The dimension of the low-rank matrices
    "lora_alpha": 32,         # The scaling factor for the low-rank matrices
    "lora_dropout": 0.05,     # Dropout probability for LoRA layers
    "bias": "none",           # Whether to train bias parameters
    "task_type": "CAUSAL_LM", # Specifies the task type for the model
}

# Reward function weights for different dimensions of code quality.
# The weights should sum to 1.0 for a balanced evaluation.
REWARD_WEIGHTS = {
    "readability": 0.3,
    "performance": 0.2,
    "security": 0.3,
    "style": 0.2,
}


# Data paths
DATASET_PATH = "data/code_review_dataset.json"  # Path to dataset,support json and csv files

#Training Data Log Path, used to record interation
TRAINING_LOG_PATH = "training_logs/interactions.csv"
