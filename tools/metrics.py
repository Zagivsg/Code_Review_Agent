# Multi-dimensional reward function 
# This is the complete, multi-dimensional reward function with full support
# for both Python and JavaScript analysis.

import subprocess
import json
import tempfile
import os
import re
from radon.visitors import ComplexityVisitor
from config.settings import REWARD_WEIGHTS

def _run_tool_with_stdin(command, code):
    """Helper to run a command-line tool by passing code via stdin for efficiency."""
    try:
        process = subprocess.run(
            command,
            input=code,
            capture_output=True,
            text=True,
            check=False
        )
        return process.stdout
    except FileNotFoundError:
        return ""

def get_style_issues(code, language):
    """Get style issues from flake8 (Python) or eslint (JavaScript)."""
    if language == "python":
        output = _run_tool_with_stdin(['flake8', '--stdin-display-name', 'style_check', '-'], code)
        return len(output.strip().splitlines())
    elif language == "javascript":
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".js") as tmp:
            tmp.write(code)
            tmp_path = tmp.name
        try:
            eslint_path = os.path.join('.', 'node_modules', '.bin', 'eslint')
            result = subprocess.run(
                [eslint_path, tmp_path, '--format', 'json'],
                capture_output=True, text=True, check=False
            )
            os.unlink(tmp_path)
            if result.stdout:
                output = json.loads(result.stdout)
                return len(output[0]['messages']) if output else 0
            return 0
        except (FileNotFoundError, IndexError, json.JSONDecodeError):
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            return 0
    return 0

def get_security_issues(code, language):
    """Get security issues from bandit (Python) or njsscan (JavaScript)."""
    if language == "python":
        output = _run_tool_with_stdin(['bandit', '-f', 'json', '-'], code)
        try:
            results = json.loads(output)
            return len(results.get("results", []))
        except json.JSONDecodeError:
            return 0
    elif language == "javascript":
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".js") as tmp:
            tmp.write(code)
            tmp_path = tmp.name
        try:
            njsscan_path = os.path.join('.', 'node_modules', '.bin', 'njsscan')
            result = subprocess.run(
                [njsscan_path, '--json', '-f', tmp_path],
                capture_output=True, text=True, check=False
            )
            os.unlink(tmp_path)
            if result.stdout:
                # njsscan nests the findings
                scan_results = json.loads(result.stdout)
                total_issues = 0
                for file_key in scan_results:
                    total_issues += len(scan_results[file_key].get('findings', []))
                return total_issues
            return 0
        except (FileNotFoundError, json.JSONDecodeError):
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            return 0
    return 0

def get_readability_score(code, language):
    """Get readability score (cyclomatic complexity)."""
    if language == "python":
        try:
            visitor = ComplexityVisitor.from_code(code)
            return visitor.total_complexity
        except Exception:
            return 25 
    elif language == "javascript":
        return get_style_issues(code, language)
    return 0

def get_performance_score(code, language):
    """
    Calculates a performance score based on detecting inefficient patterns.
    A higher score indicates more potential issues.
    """
    score = 0
    if language == "python":
        score += len(re.findall(r'\n\s*for\s.*\s+.*\..*append\(', code))
        score += code.count("range(len(")
    elif language == "javascript":
        score += code.count("for (var") + code.count("for (let")
        score += code.count(".innerHTML") 
    return score

def calculate_reward(original_code, improved_code, language):
    """
    Computes a weighted reward score based on the delta of multiple metrics.
    """
    metrics = {}
    
    def get_delta(metric_func, original, improved, lang):
        original_score = metric_func(original, lang)
        improved_score = metric_func(improved, lang)
        # Calculate the percentage reduction in issues
        delta = (original_score - improved_score) / max(original_score, 1)
        return delta, original_score, improved_score

    # 1. Readability
    readability_delta, orig_read, imp_read = get_delta(get_readability_score, original_code, improved_code, language)
    metrics['readability'] = readability_delta * REWARD_WEIGHTS['readability']

    # 2. Performance
    performance_delta, orig_perf, imp_perf = get_delta(get_performance_score, original_code, improved_code, language)
    metrics['performance'] = performance_delta * REWARD_WEIGHTS['performance']

    # 3. Security
    security_delta, orig_sec, imp_sec = get_delta(get_security_issues, original_code, improved_code, language)
    metrics['security'] = security_delta * REWARD_WEIGHTS['security']

    # 4. Style
    style_delta, orig_style, imp_style = get_delta(get_style_issues, original_code, improved_code, language)
    metrics['style'] = style_delta * REWARD_WEIGHTS['style']

    total_reward = sum(metrics.values())
    clipped_reward = max(-1.0, min(1.0, total_reward))

    notes = (
        f"Reward: {clipped_reward:.3f} | "
        f"Readability: {orig_read}->{imp_read} | "
        f"Performance: {orig_perf}->{imp_perf} | "
        f"Security: {orig_sec}->{imp_sec} | "
        f"Style: {orig_style}->{imp_style}"
    )
    
    return clipped_reward, notes