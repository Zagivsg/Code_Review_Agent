# Planning module: Analyze code and identify issues
from model.base_model import CodeReviewLLM
from tools.static_analysis import analyze_code

class Planner:
    def __init__(self, llm: CodeReviewLLM):
        self.llm = llm

    def plan(self, code_snippet, language):
        analysis_results = analyze_code(code_snippet, language)
        
        prompt = f"""
[INST]
You are a code quality expert. Analyze the following {language} code and the report from its static analysis tool.
Based on this information, create a concise, high-level plan with bullet points on how to improve the code. Focus on readability, performance, security, and style.

**Static Analysis Report:**
{analysis_results if analysis_results else "No issues found."}

**Code Snippet:**
```python
{code_snippet}
What is your improvement plan?
[/INST]
"""
        response = self.llm.generate(prompt)
        plan_text = response.split("[/INST]")[-1].strip()
        return plan_text