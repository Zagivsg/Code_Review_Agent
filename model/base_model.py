# LLM base model encapsulation
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from config.settings import MODEL_NAME, DEVICE

class CodeReviewLLM:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        self.model = AutoModelForCausalLM.from_pretrained(MODEL_NAME).to(DEVICE)
        self.tokenizer.pad_token = self.tokenizer.eos_token

    def generate(self, prompt, max_new_tokens=250):
        inputs = self.tokenizer(prompt, return_tensors="pt", padding=True, truncation=True).to(DEVICE)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                temperature=0.2,
                top_p=0.95,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response