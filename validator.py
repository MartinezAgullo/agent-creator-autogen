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
        'shutil', 'pickle', 'shelve'
    }
    
    # Function calls that should not be allowed
    FORBIDDEN_CALLS = {
        'eval', 'exec', 'compile', '__import__'
    }
    
    MAX_CODE_LENGTH = 20000  # characters (relaxed from 15000)
    MIN_CODE_LENGTH = 300    # characters (relaxed from 500)
    
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
        
        # Parse AST
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            issues.append(f"Syntax error at line {e.lineno}: {e.msg}")
            return False, issues
        
        # Check for forbidden imports (CRITICAL)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if any(forbidden in alias.name for forbidden in CodeValidator.FORBIDDEN_IMPORTS):
                        issues.append(f"Forbidden import: {alias.name}")
            
            elif isinstance(node, ast.ImportFrom):
                if node.module and any(forbidden in node.module for forbidden in CodeValidator.FORBIDDEN_IMPORTS):
                    issues.append(f"Forbidden import from: {node.module}")
            
            # Check for forbidden function calls (CRITICAL)
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in CodeValidator.FORBIDDEN_CALLS:
                        issues.append(f"Forbidden function call: {node.func.id}")
        
        # Verify Agent class exists (RELAXED - only check class name)
        has_agent_class = False
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == 'Agent':
                has_agent_class = True
                break
        
        if not has_agent_class:
            issues.append("Missing required 'Agent' class")
        
        # That's it! No other structural requirements
        # Let AutoGen handle the rest at runtime
        
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