import re

def extract_code_block(text, language):
    pattern = f"```{language}\\n(.*?)\\n```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # Fallback for code that isn't in a markdown block
    if text.startswith("def ") or text.startswith("function "):
         return text.strip()
         
    return text # Return original text if no block found