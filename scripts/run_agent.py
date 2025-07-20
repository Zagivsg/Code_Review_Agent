# Entry script to run agent
from agent.agent import CodeReviewAgent

if __name__ == "__main__":
    agent = CodeReviewAgent()
    code = input("Enter code snippet: ")
    language = input ("Enter programming language type (python/javascript): ")
    result = agent.run(code)
    print(result)