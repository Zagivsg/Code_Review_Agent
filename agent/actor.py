# Acting module: Generate improvement suggestions
from model.base_model import CodeReviewLLM
from utils.code_parser import extract_code_block

class Actor:
    def __init__(self, llm: CodeReviewLLM):
        self.llm = llm

    def act(self, code_snippet, plan, language):
        prompt = f"""
[INST]
You are an expert programmer. Based on the following plan, rewrite the given {language} code snippet to implement the suggested improvements.
Your response must contain *only* the complete, final code block, with no explanations or conversational text.

**Improvement Plan:**
{plan}

**Original Code:**
```python
{code_snippet}
Provide the improved code now.
[/INST]
"""
        suggestion = self.llm.generate(prompt)
        raw_code = suggestion.split("[/INST]")[-1].strip()
        improved_code = extract_code_block(raw_code, language)
        return improved_code