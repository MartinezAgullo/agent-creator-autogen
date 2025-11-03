"""
Code validation for dynamically generated agents.
Prevents execution of potentially dangerous or malformed code.
"""
import ast
from typing import Tuple, List


class CodeValidator:
    """Validates generated agent code before execution."""
    
    # Imports that could be dangerous in sandbox
    FORBIDDEN_IMPORTS = {
        'subprocess', 'os.system', 'eval', 'exec', 'compile',
        '__import__', 'socket', 'urllib', 'requests', 'httpx',
        'sys.exit', 'shutil', 'pickle', 'shelve'
    }
    
    # Function calls that should not be allowed
    FORBIDDEN_CALLS = {
        'eval', 'exec', 'compile', '__import__', 'open'
    }
    
    MAX_CODE_LENGTH = 15000  # characters
    MIN_CODE_LENGTH = 500    # characters
    
    @staticmethod
    def validate(code: str) -> Tuple[bool, List[str]]:
        """
        Validate generated code.
        
        Args:
            code: Python code to validate
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check code length
        if len(code) > CodeValidator.MAX_CODE_LENGTH:
            issues.append(f"Code too long: {len(code)} chars (max {CodeValidator.MAX_CODE_LENGTH})")
        
        if len(code) < CodeValidator.MIN_CODE_LENGTH:
            issues.append(f"Code too short: {len(code)} chars (min {CodeValidator.MIN_CODE_LENGTH})")
        
        # Check for markdown code blocks (LLM sometimes includes these)
        if '```python' in code or '```' in code:
            issues.append("Code contains markdown formatting (```). Must be pure Python.")
        
        # Parse AST
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            issues.append(f"Syntax error at line {e.lineno}: {e.msg}")
            return False, issues
        
        # Check for forbidden imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if any(forbidden in alias.name for forbidden in CodeValidator.FORBIDDEN_IMPORTS):
                        issues.append(f"Forbidden import: {alias.name}")
            
            elif isinstance(node, ast.ImportFrom):
                if node.module and any(forbidden in node.module for forbidden in CodeValidator.FORBIDDEN_IMPORTS):
                    issues.append(f"Forbidden import from: {node.module}")
            
            # Check for forbidden function calls
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in CodeValidator.FORBIDDEN_CALLS:
                        issues.append(f"Forbidden function call: {node.func.id}")
        
        # Verify required class structure
        has_agent_class = False
        has_routed_agent_base = False
        has_init_method = False
        has_handler_method = False
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == 'Agent':
                has_agent_class = True
                
                # Check if it inherits from RoutedAgent
                for base in node.bases:
                    if isinstance(base, ast.Name) and base.id == 'RoutedAgent':
                        has_routed_agent_base = True
                
                # Check for required methods
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        if item.name == '__init__':
                            has_init_method = True
                        if item.name == 'handle_message':
                            has_handler_method = True
        
        if not has_agent_class:
            issues.append("Missing required 'Agent' class")
        
        if not has_routed_agent_base:
            issues.append("Agent class must inherit from RoutedAgent")
        
        if not has_init_method:
            issues.append("Agent class missing __init__ method")
        
        if not has_handler_method:
            issues.append("Agent class missing handle_message method")
        
        return len(issues) == 0, issues
    
    @staticmethod
    def clean_code(code: str) -> str:
        """
        Clean common LLM formatting issues from code.
        
        Args:
            code: Raw code that may contain markdown or other formatting
            
        Returns:
            Cleaned Python code
        """
        # Remove markdown code blocks
        if '```python' in code:
            code = code.split('```python')[1]
            if '```' in code:
                code = code.split('```')[0]
        elif '```' in code:
            parts = code.split('```')
            if len(parts) >= 3:
                code = parts[1]
        
        # Strip leading/trailing whitespace
        code = code.strip()
        
        return code