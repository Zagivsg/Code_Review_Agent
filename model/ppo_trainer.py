# PPO training main flow using TRL library
import torch
from tqdm import tqdm
from transformers import AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import PPOTrainer, PPOConfig, AutoModelForCausalLMWithValueHead

from config.settings import PPO_CONFIG, LORA_CONFIG, MODEL_NAME, DEVICE, DATASET_PATH, TRAINING_LOG_PATH
from data.load_dataset import load_code_review_data
from tools.metrics import calculate_reward
from utils.code_parser import extract_code_block

def get_prompt(code, language):
    """
    Generates a standardized prompt for the code review agent.
    """
    return f"""
[INST] You are an expert programmer. Rewrite the following {language} code to improve its readability, performance, and style.
Your response must contain *only* the complete, final code block, with no explanations or conversational text.

**Original Code:**
```{language}
{code}
```
[/INST]
"""

def train_ppo_qlora(dataset_path = DATASET_PATH):
    """
    Main function to train the code review agent using PPO with a QLoRA-configured model.
    """
    # 1. Configure PPO from settings
    ppo_config = PPOConfig(**PPO_CONFIG)

    # 2. Define QLoRA configuration for 4-bit quantization
    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,                  # Enable 4-bit quantization
        bnb_4bit_quant_type="nf4",          # Use the "nf4" quantization type
        bnb_4bit_compute_dtype=torch.bfloat16, # Set the compute dtype for better performance
        bnb_4bit_use_double_quant=True,     # Use a nested quantization for memory savings
    )

    # 3. Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(ppo_config.model_name)
    tokenizer.pad_token = tokenizer.eos_token

    # 4. Load and configure the model for QLoRA training
    model = AutoModelForCausalLMWithValueHead.from_pretrained(
        ppo_config.model_name,
        quantization_config=quantization_config,
        peft_config=LoraConfig(**LORA_CONFIG),
        device_map="auto" # Automatically distribute model across available devices
    )
    
    # Prepare the quantized model for training
    model = prepare_model_for_kbit_training(model)

    # 5. Initialize PPOTrainer
    ppo_trainer = PPOTrainer(
        config=ppo_config,
        model=model,
        ref_model=None, # TRL creates a reference model from the base model automatically
        tokenizer=tokenizer,
    )

    # 6. Load the dataset
    dataset = load_code_review_data(TRAINING_LOG_PATH)
    
    # 7. Training loop
    generation_kwargs = {"max_new_tokens": 250, "temperature": 0.1, "top_p": 0.95, "do_sample": True}

    for epoch in range(ppo_config.ppo_epochs):
        print(f"--- Epoch {epoch+1}/{ppo_config.ppo_epochs} ---")
        for original_code, language in tqdm(dataset, desc=f"Epoch {epoch+1} Batch"):
            
            query_prompt = get_prompt(original_code, language)
            query_tensor = tokenizer.encode(query_prompt, return_tensors="pt").to(model.device)

            # Generate the improved code from the model
            response_tensor = ppo_trainer.generate(query_tensor.squeeze(), **generation_kwargs)
            
            # Decode the response and extract the code block
            response_text = tokenizer.decode(response_tensor.squeeze(), skip_special_tokens=True)
            improved_code = extract_code_block(response_text.split("[/INST]")[-1], language)

            if not improved_code.strip():
                print("Warning: Model generated an empty or invalid response. Skipping.")
                continue

            # Calculate reward based on the improvement
            reward_score, reward_notes = calculate_reward(original_code, improved_code, language)
            reward_tensor = torch.tensor([reward_score], dtype=torch.float).to(model.device)
            
            print(f"\nReward: {reward_score:.3f} | Notes: {reward_notes}")

            # Perform PPO optimization step
            stats = ppo_trainer.step([query_tensor.squeeze()], [response_tensor.squeeze()], [reward_tensor])
            ppo_trainer.log_stats(stats, {"query": query_prompt}, [reward_tensor])

    # 8. Save the trained LoRA adapters
    print("--- Training complete. Saving LoRA model adapters. ---")
    ppo_trainer.save_model("ppo_qlora_code_review_agent")
    print("Model adapters saved to 'ppo_qlora_code_review_agent'")

if __name__ == "__main__":
    train_ppo_qlora()