# This file contains the logic for semantic normalization.
import ast
import esprima # For JavaScript
import hashlib

class PythonNormalizer(ast.NodeTransformer):
    """
    Normalizes a Python AST by replacing names of variables, functions,
    and arguments with generic, numbered placeholders.
    """
    def __init__(self):
        self.name_map = {}
        self.counter = 0

    def get_generic_name(self, name):
        if name not in self.name_map:
            self.name_map[name] = f"VAR_{self.counter}"
            self.counter += 1
        return self.name_map[name]

    def visit_Name(self, node):
        # Handles variables and function calls
        node.id = self.get_generic_name(node.id)
        return node

    def visit_FunctionDef(self, node):
        # Handles function definitions
        node.name = self.get_generic_name(node.name)
        self.generic_visit(node)
        return node

    def visit_arg(self, node):
        # Handles function arguments
        node.arg = self.get_generic_name(node.arg)
        return node

def normalize_python(code: str) -> str:
    """Parses, normalizes, and unparses Python code."""
    try:
        tree = ast.parse(code)
        normalizer = PythonNormalizer()
        normalized_tree = normalizer.visit(tree)
        # ast.unparse requires Python 3.9+
        return ast.unparse(normalized_tree)
    except (SyntaxError, TypeError):
        # If parsing fails, fall back to the original code for hashing
        return code

def normalize_javascript(code: str) -> str:
    """
    Normalizes JavaScript code by replacing identifiers.
    Note: This is a simplified example. A full implementation would be more complex.
    """
    try:
        tree = esprima.parse(code)
        # This is a basic normalization; a real-world version would be more thorough
        # by recursively replacing all identifier names.
        # For simplicity, we'll just serialize the structure.
        def remove_names(node):
            if isinstance(node, dict):
                new_node = {}
                for key, value in node.items():
                    if key == 'name':
                        new_node[key] = 'IDENTIFIER'
                    else:
                        new_node[key] = remove_names(value)
                return new_node
            elif isinstance(node, list):
                return [remove_names(item) for item in node]
            return node
        
        normalized_tree = remove_names(tree.toDict())
        return str(normalized_tree)
    except esprima.error.Error:
        return code


def get_semantic_hash(code: str, language: str) -> str:
    """
    Generates a hash based on the semantic structure of the code,
    not its superficial text.
    """
    normalized_code = ""
    if language == "python":
        normalized_code = normalize_python(code)
    elif language == "javascript":
        normalized_code = normalize_javascript(code)
    else:
        # Fallback for unsupported languages
        normalized_code = code

    return hashlib.sha256(normalized_code.encode('utf-8')).hexdigest()
