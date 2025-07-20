import subprocess
import json
import os
import tempfile

def run_pylint(code):
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".py") as tmp:
        tmp.write(code)
        tmp_path = tmp.name
    
    try:
        result = subprocess.run(
            ['pylint', tmp_path, '--output-format=json'],
            capture_output=True,
            text=True,
            check=False
        )
        os.unlink(tmp_path)
        if result.stdout:
            return json.loads(result.stdout)
        return []
    except (FileNotFoundError, json.JSONDecodeError):
        os.unlink(tmp_path)
        return []

def run_eslint(code):
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".js") as tmp:
        tmp.write(code)
        tmp_path = tmp.name
    
    try:
        eslint_path = os.path.join('.', 'node_modules', '.bin', 'eslint')
        result = subprocess.run(
            [eslint_path, tmp_path, '--format', 'json'],
            capture_output=True,
            text=True,
            check=False
        )
        os.unlink(tmp_path)
        if result.stdout:
            output = json.loads(result.stdout)
            return output[0].get('messages', []) if output else []
        return []
    except (FileNotFoundError, json.JSONDecodeError):
        os.unlink(tmp_path)
        return []

def analyze_code(code, language):
    if language == 'python':
        return run_pylint(code)
    elif language == 'javascript':
        return run_eslint(code)
    else:
        raise ValueError(f"Unsupported language: {language}")