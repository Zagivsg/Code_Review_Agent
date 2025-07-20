# Overall Agent workflow
from model.base_model import CodeReviewLLM
from agent.planner import Planner
from agent.actor import Actor
from agent.reflector import Reflector

class CodeReviewAgent:
    def __init__(self):
        self.llm = CodeReviewLLM()
        self.planner = Planner(self.llm)
        self.actor = Actor(self.llm)
        self.reflector = Reflector()

    def run(self, code_snippet, language = "python"):
        print(f"--- Running agent for {language.upper()} ---")
        
        plan = self.planner.plan(code_snippet, language)
        print(f"\n[PLAN]\n{plan}\n")
        
        improved_code = self.actor.act(code_snippet, plan, language)
        print(f"\n[IMPROVED CODE]\n{improved_code}\n")
        
        reward, notes = self.reflector.reflect(code_snippet, improved_code, language)
        print(f"\n[REFLECTION]\n{notes}\n")

        return {
            "plan": plan,
            "original_code": code_snippet,
            "improved_code": improved_code,
            "reward": reward,
            "notes": notes
        }