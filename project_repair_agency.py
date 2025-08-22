"""
Project Repair Agency - Specialized agents to fix and improve the lead generation system
"""
import os
import sys
import json
import subprocess
import ast
import re
from pathlib import Path
from agency_swarm import Agent, Agency, set_openai_key
from agency_swarm.tools import BaseTool
from pydantic import Field
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set OpenAI API key
set_openai_key(os.getenv("OPENAI_API_KEY"))

# ==================== ANALYSIS & REPAIR TOOLS ====================

class CodeAuditTool(BaseTool):
    """
    Audits code files to identify issues, bugs, and improvement opportunities.
    """
    file_path: str = Field(..., description="Path to the file to audit")
    audit_type: str = Field("comprehensive", description="Type of audit: comprehensive, security, performance, structure")
    
    def run(self):
        try:
            issues = []
            
            if not os.path.exists(self.file_path):
                return {"status": "error", "message": f"File not found: {self.file_path}"}
            
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for common Python issues
            if self.file_path.endswith('.py'):
                # Check for missing error handling
                if 'try:' not in content and ('requests.' in content or 'open(' in content):
                    issues.append({
                        "type": "error_handling",
                        "severity": "high",
                        "message": "Missing try-except blocks for I/O operations"
                    })
                
                # Check for hardcoded credentials
                credential_patterns = [
                    r'api_key\s*=\s*["\'][^"\']+["\']',
                    r'password\s*=\s*["\'][^"\']+["\']',
                    r'secret\s*=\s*["\'][^"\']+["\']'
                ]
                for pattern in credential_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        issues.append({
                            "type": "security",
                            "severity": "critical",
                            "message": "Possible hardcoded credentials detected"
                        })
                
                # Check for unused imports
                import_lines = re.findall(r'^import\s+(\w+)|^from\s+[\w.]+\s+import\s+(\w+)', content, re.MULTILINE)
                for imp in import_lines:
                    module = imp[0] or imp[1]
                    if module and content.count(module) == 1:  # Only appears in import
                        issues.append({
                            "type": "unused_code",
                            "severity": "low",
                            "message": f"Possibly unused import: {module}"
                        })
                
                # Check for SQL injection vulnerabilities
                if 'execute(' in content and '%s' not in content and '?' not in content:
                    if re.search(r'execute\([^)]*\+[^)]*\)', content):
                        issues.append({
                            "type": "security",
                            "severity": "critical",
                            "message": "Potential SQL injection vulnerability"
                        })
                
                # Check for missing docstrings
                functions = re.findall(r'^def\s+(\w+)\s*\([^)]*\):', content, re.MULTILINE)
                for func in functions:
                    func_pattern = f'def {func}.*?:\\n\\s*"""'
                    if not re.search(func_pattern, content, re.DOTALL):
                        issues.append({
                            "type": "documentation",
                            "severity": "low",
                            "message": f"Missing docstring for function: {func}"
                        })
            
            return {
                "status": "success",
                "file": self.file_path,
                "issues_count": len(issues),
                "issues": issues
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

class FixCodeIssueTool(BaseTool):
    """
    Fixes specific issues in code files.
    """
    file_path: str = Field(..., description="Path to the file to fix")
    issue_type: str = Field(..., description="Type of issue to fix")
    fix_description: str = Field(..., description="Description of the fix to apply")
    
    def run(self):
        try:
            if not os.path.exists(self.file_path):
                return {"status": "error", "message": f"File not found: {self.file_path}"}
            
            # Create backup
            backup_path = f"{self.file_path}.backup"
            with open(self.file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            # Apply fixes based on issue type
            fixed_content = original_content
            changes_made = []
            
            if self.issue_type == "error_handling":
                # Add try-except blocks around risky operations
                patterns = [
                    (r'(requests\.\w+\([^)]+\))', r'try:\n    \1\nexcept Exception as e:\n    print(f"Error: {e}")\n    return None'),
                    (r'(open\([^)]+\))', r'try:\n    \1\nexcept IOError as e:\n    print(f"File error: {e}")\n    return None')
                ]
                for pattern, replacement in patterns:
                    if re.search(pattern, fixed_content):
                        fixed_content = re.sub(pattern, replacement, fixed_content)
                        changes_made.append("Added error handling")
            
            elif self.issue_type == "imports":
                # Remove unused imports
                lines = fixed_content.split('\n')
                new_lines = []
                for line in lines:
                    if line.startswith('import ') or line.startswith('from '):
                        module = re.search(r'import\s+(\w+)|from\s+[\w.]+\s+import\s+(\w+)', line)
                        if module:
                            mod_name = module.group(1) or module.group(2)
                            if fixed_content.count(mod_name) > 1:  # Used elsewhere
                                new_lines.append(line)
                            else:
                                changes_made.append(f"Removed unused import: {mod_name}")
                    else:
                        new_lines.append(line)
                fixed_content = '\n'.join(new_lines)
            
            # Write fixed content
            if changes_made:
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
            
            return {
                "status": "success",
                "file": self.file_path,
                "backup": backup_path,
                "changes": changes_made
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

class RefactorCodeTool(BaseTool):
    """
    Refactors code to improve structure and maintainability.
    """
    file_path: str = Field(..., description="Path to the file to refactor")
    refactor_type: str = Field(..., description="Type of refactoring: extract_function, simplify, modularize")
    
    def run(self):
        try:
            if not os.path.exists(self.file_path):
                return {"status": "error", "message": f"File not found: {self.file_path}"}
            
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            suggestions = []
            
            # Analyze code complexity
            functions = re.findall(r'def\s+(\w+)\s*\([^)]*\):[^}]+?(?=\ndef|\Z)', content, re.DOTALL)
            for func_content in functions:
                lines = func_content.split('\n')
                if len(lines) > 50:
                    suggestions.append({
                        "type": "complexity",
                        "message": f"Function is too long ({len(lines)} lines). Consider breaking it down."
                    })
                
                # Check for nested loops
                if content.count('for ') > 2 or content.count('while ') > 1:
                    suggestions.append({
                        "type": "nested_loops",
                        "message": "Multiple nested loops detected. Consider extracting to separate functions."
                    })
            
            # Check for duplicate code
            lines = content.split('\n')
            for i in range(len(lines) - 10):
                block = '\n'.join(lines[i:i+5])
                if block and content.count(block) > 1:
                    suggestions.append({
                        "type": "duplication",
                        "message": f"Duplicate code detected at line {i+1}. Extract to a function."
                    })
                    break
            
            return {
                "status": "success",
                "file": self.file_path,
                "suggestions": suggestions
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

class RunTestsTool(BaseTool):
    """
    Runs tests to verify fixes and improvements.
    """
    test_type: str = Field("all", description="Type of tests to run: all, unit, integration, specific")
    test_file: Optional[str] = Field(None, description="Specific test file to run")
    
    def run(self):
        try:
            # Check for test files
            test_files = []
            for root, dirs, files in os.walk('.'):
                for file in files:
                    if file.startswith('test_') and file.endswith('.py'):
                        test_files.append(os.path.join(root, file))
            
            if not test_files:
                return {
                    "status": "warning",
                    "message": "No test files found. Creating basic tests recommended."
                }
            
            # Run tests
            results = []
            for test_file in test_files:
                if self.test_file and test_file != self.test_file:
                    continue
                
                try:
                    result = subprocess.run(
                        ['python', '-m', 'pytest', test_file, '-v'],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    results.append({
                        "file": test_file,
                        "passed": result.returncode == 0,
                        "output": result.stdout if result.returncode == 0 else result.stderr
                    })
                except subprocess.TimeoutExpired:
                    results.append({
                        "file": test_file,
                        "passed": False,
                        "output": "Test timed out"
                    })
            
            return {
                "status": "success",
                "tests_run": len(results),
                "results": results
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

class OptimizePerformanceTool(BaseTool):
    """
    Analyzes and optimizes code performance.
    """
    file_path: str = Field(..., description="Path to analyze for performance")
    
    def run(self):
        try:
            if not os.path.exists(self.file_path):
                return {"status": "error", "message": f"File not found: {self.file_path}"}
            
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            optimizations = []
            
            # Check for inefficient patterns
            patterns = [
                (r'for .+ in range\(len\((.+)\)\):', "Use enumerate() instead of range(len())"),
                (r'\.append\(.+\) for .+ in', "Consider using list comprehension"),
                (r'time\.sleep\(', "Avoid blocking sleep in production code"),
                (r'SELECT \* FROM', "Avoid SELECT *, specify columns explicitly"),
                (r'except:\s*\n\s*pass', "Avoid bare except with pass"),
                (r'global\s+\w+', "Avoid global variables, use class attributes or return values"),
            ]
            
            for pattern, suggestion in patterns:
                if re.search(pattern, content):
                    optimizations.append({
                        "pattern": pattern,
                        "suggestion": suggestion
                    })
            
            # Check for missing caching
            if 'def ' in content and 'cache' not in content.lower():
                if 'database' in content.lower() or 'api' in content.lower():
                    optimizations.append({
                        "pattern": "No caching detected",
                        "suggestion": "Consider adding caching for database/API calls"
                    })
            
            return {
                "status": "success",
                "file": self.file_path,
                "optimizations": optimizations
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

class CreateDocumentationTool(BaseTool):
    """
    Creates or updates documentation for the project.
    """
    doc_type: str = Field(..., description="Type of documentation: readme, api, setup, architecture")
    
    def run(self):
        try:
            # Analyze project structure
            project_info = {
                "python_files": [],
                "has_tests": False,
                "has_requirements": os.path.exists("requirements.txt"),
                "has_env_example": os.path.exists(".env.example")
            }
            
            for root, dirs, files in os.walk('.'):
                if 'agency-swarm' in root or '__pycache__' in root:
                    continue
                for file in files:
                    if file.endswith('.py'):
                        project_info["python_files"].append(os.path.join(root, file))
                    if file.startswith('test_'):
                        project_info["has_tests"] = True
            
            doc_content = ""
            
            if self.doc_type == "readme":
                doc_content = f"""# Lead Generation System

## Overview
Advanced lead generation system with multiple data providers and automation capabilities.

## Features
- Multi-provider lead search (Hybrid, Pure, Free scrapers)
- Data enrichment and verification
- Email campaign management
- Automated scheduling
- Agency Swarm AI integration

## Setup
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and configure API keys
4. Run the application: `python app.py`

## Project Structure
- `/src` - Core source code
  - `/providers` - Data provider implementations
  - `email_generator.py` - Email generation logic
  - `instantly_integration.py` - Email campaign integration
- `/data` - Database and data files
- `/templates` - HTML templates
- `agency_integration.py` - AI agency system

## Files Found
Total Python files: {len(project_info['python_files'])}
Has tests: {project_info['has_tests']}
Has requirements.txt: {project_info['has_requirements']}
"""
            
            # Save documentation
            doc_path = f"{self.doc_type.upper()}.md"
            with open(doc_path, 'w', encoding='utf-8') as f:
                f.write(doc_content)
            
            return {
                "status": "success",
                "created": doc_path,
                "content_preview": doc_content[:500]
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

# ==================== SPECIALIZED REPAIR AGENTS ====================

# Project Manager Agent - Oversees the repair process
project_manager = Agent(
    name="ProjectManager",
    description="Manages the project repair and improvement process",
    instructions="""You are the Project Manager responsible for fixing and improving this lead generation system.

Your responsibilities:
1. Coordinate the repair team to identify and fix all issues
2. Prioritize critical bugs and security vulnerabilities
3. Ensure code quality and maintainability
4. Oversee testing and validation
5. Track progress and report status

Start by running a comprehensive audit, then create a repair plan based on findings.
Focus on stability, security, and performance in that order.""",
    temperature=0.7,
    max_prompt_tokens=25000,
)

# Code Auditor Agent
code_auditor = Agent(
    name="CodeAuditor",
    description="Identifies bugs, security issues, and code quality problems",
    instructions="""You are a Code Auditor specializing in Python applications.

Your expertise includes:
1. Identifying bugs and potential crashes
2. Finding security vulnerabilities
3. Detecting performance bottlenecks
4. Evaluating code quality and structure
5. Checking for missing error handling

Perform thorough audits and provide detailed reports with severity levels.
Priority order: Critical security issues > Crashes > Data loss risks > Performance > Code quality.""",
    tools=[CodeAuditTool],
    temperature=0.3,
)

# Bug Fixer Agent
bug_fixer = Agent(
    name="BugFixer",
    description="Fixes identified bugs and issues in the codebase",
    instructions="""You are a Bug Fixer specializing in Python debugging and repair.

Your skills include:
1. Fixing runtime errors and crashes
2. Resolving security vulnerabilities
3. Adding proper error handling
4. Fixing logic errors
5. Resolving dependency issues

Always create backups before making changes.
Test your fixes thoroughly.
Document what was changed and why.""",
    tools=[FixCodeIssueTool],
    temperature=0.3,
)

# Refactoring Specialist Agent
refactoring_specialist = Agent(
    name="RefactoringSpecialist",
    description="Improves code structure and maintainability",
    instructions="""You are a Refactoring Specialist focused on code quality.

Your expertise:
1. Simplifying complex functions
2. Removing code duplication
3. Improving naming and readability
4. Optimizing imports and dependencies
5. Implementing design patterns

Follow Python best practices and PEP 8.
Make code more maintainable without breaking functionality.
Create modular, reusable components.""",
    tools=[RefactorCodeTool],
    temperature=0.3,
)

# Test Engineer Agent
test_engineer = Agent(
    name="TestEngineer",
    description="Creates and runs tests to ensure code quality",
    instructions="""You are a Test Engineer ensuring code reliability.

Your responsibilities:
1. Creating comprehensive test suites
2. Running existing tests
3. Validating bug fixes
4. Performance testing
5. Integration testing

Use pytest for testing.
Aim for high code coverage.
Test edge cases and error conditions.""",
    tools=[RunTestsTool],
    temperature=0.3,
)

# Performance Optimizer Agent
performance_optimizer = Agent(
    name="PerformanceOptimizer",
    description="Optimizes code for better performance",
    instructions="""You are a Performance Optimization Specialist.

Your focus areas:
1. Identifying performance bottlenecks
2. Optimizing database queries
3. Implementing caching strategies
4. Reducing API calls
5. Improving algorithm efficiency

Use profiling data to guide optimizations.
Balance performance with code readability.
Document performance improvements.""",
    tools=[OptimizePerformanceTool],
    temperature=0.3,
)

# Documentation Writer Agent
documentation_writer = Agent(
    name="DocumentationWriter",
    description="Creates and maintains project documentation",
    instructions="""You are a Technical Documentation Specialist.

Your tasks:
1. Creating comprehensive README files
2. Writing API documentation
3. Documenting setup procedures
4. Creating architecture diagrams
5. Writing code comments and docstrings

Make documentation clear and concise.
Include examples and use cases.
Keep documentation up-to-date with code changes.""",
    tools=[CreateDocumentationTool],
    temperature=0.5,
)

# ==================== PROJECT REPAIR AGENCY ====================

project_repair_agency = Agency(
    [
        project_manager,  # Project Manager as the entry point
        [project_manager, code_auditor],           # Manager initiates audits
        [project_manager, bug_fixer],              # Manager assigns bug fixes
        [project_manager, refactoring_specialist], # Manager requests refactoring
        [project_manager, test_engineer],          # Manager orders testing
        [project_manager, performance_optimizer],  # Manager requests optimization
        [project_manager, documentation_writer],   # Manager requests documentation
        [code_auditor, bug_fixer],                # Auditor identifies issues for fixer
        [bug_fixer, test_engineer],               # Fixer requests testing
        [refactoring_specialist, test_engineer],  # Refactoring needs testing
        [performance_optimizer, test_engineer],   # Optimization needs validation
    ],
    shared_instructions="""This is the Project Repair Agency for the lead generation system.

CRITICAL OBJECTIVES:
1. Make the system stable and reliable
2. Fix all security vulnerabilities
3. Improve code quality and maintainability
4. Optimize performance
5. Create comprehensive documentation

PRIORITY ORDER:
1. Critical bugs and security issues
2. Data integrity problems
3. Performance bottlenecks
4. Code quality improvements
5. Documentation

STANDARDS:
- All fixes must be tested
- Create backups before changes
- Document all modifications
- Follow Python best practices
- Maintain backwards compatibility

Work systematically through the codebase to transform this into a production-ready system.""",
    temperature=0.5,
    max_prompt_tokens=25000
)

def run_repair_agency():
    """Run the project repair agency"""
    print("=" * 60)
    print("PROJECT REPAIR AGENCY - FIXING YOUR LEAD GENERATION SYSTEM")
    print("=" * 60)
    print("\nCapabilities:")
    print("✓ Comprehensive code auditing")
    print("✓ Automated bug fixing")
    print("✓ Code refactoring and optimization")
    print("✓ Test creation and execution")
    print("✓ Performance optimization")
    print("✓ Documentation generation")
    print("\n" + "=" * 60)
    print("\nExample Commands:")
    print("• 'Run a full audit of the project'")
    print("• 'Fix all critical security issues'")
    print("• 'Refactor the provider modules for better structure'")
    print("• 'Optimize database queries for performance'")
    print("• 'Create comprehensive documentation'")
    print("• 'Run all tests and fix failures'")
    print("\n" + "=" * 60)
    print("\nStarting repair agency...\n")
    
    # Run the terminal demo
    project_repair_agency.run_demo()

if __name__ == "__main__":
    run_repair_agency()