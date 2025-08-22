"""
Automated Project Repair Script
This script will automatically identify and fix issues in your lead generation project
"""
import os
import sys
from project_repair_agency import project_repair_agency
from agency_swarm import set_openai_key
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set OpenAI API key
set_openai_key(os.getenv("OPENAI_API_KEY"))

def automated_repair():
    """Run automated repair process"""
    print("=" * 70)
    print("AUTOMATED PROJECT REPAIR SYSTEM")
    print("=" * 70)
    print("\nInitializing repair agents...")
    print("This system will automatically:")
    print("1. Audit your entire codebase")
    print("2. Identify and prioritize issues")
    print("3. Fix critical bugs and security vulnerabilities")
    print("4. Refactor problematic code")
    print("5. Optimize performance")
    print("6. Create missing documentation")
    print("\n" + "=" * 70)
    
    # Automated repair commands to execute
    repair_tasks = [
        "Run a comprehensive audit of all Python files in the src directory",
        "Identify and list all critical security vulnerabilities",
        "Fix any SQL injection vulnerabilities found",
        "Add error handling to all file operations and API calls",
        "Check for hardcoded credentials and suggest fixes",
        "Analyze the provider modules for code duplication and suggest refactoring",
        "Optimize database queries for better performance",
        "Create unit tests for the main provider classes",
        "Generate a comprehensive README with setup instructions",
        "Run all existing tests and report failures"
    ]
    
    print("\nAutomated Repair Tasks:")
    for i, task in enumerate(repair_tasks, 1):
        print(f"{i}. {task}")
    
    print("\n" + "=" * 70)
    print("\nYou can either:")
    print("1. Type 'auto' to run all repair tasks automatically")
    print("2. Give specific repair instructions")
    print("3. Type 'quit' to exit")
    print("\n" + "=" * 70)
    
    # Get initial user input
    user_input = input("\nYour choice: ").strip().lower()
    
    if user_input == 'auto':
        print("\nStarting automated repair process...")
        print("The Project Manager will coordinate all repair activities.\n")
        
        # Send all tasks to the agency
        for task in repair_tasks:
            print(f"\n[TASK] Processing: {task}")
            result = project_repair_agency.get_completion(task)
            print(f"[DONE] Result: {result}\n")
            print("-" * 50)
    
    elif user_input == 'quit':
        print("Exiting repair system.")
        sys.exit(0)
    
    else:
        # Run interactive mode
        print("\nStarting interactive repair mode...")
        project_repair_agency.run_demo()

def quick_audit():
    """Run a quick audit to show immediate issues"""
    print("\n" + "=" * 70)
    print("QUICK PROJECT AUDIT")
    print("=" * 70)
    
    issues_found = []
    
    # Check for common issues
    print("\n[SCANNING] Checking for common issues...")
    
    # Check src/providers directory
    providers_dir = "src/providers"
    if os.path.exists(providers_dir):
        for file in os.listdir(providers_dir):
            if file.endswith('.py'):
                file_path = os.path.join(providers_dir, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Check for missing error handling
                    if 'requests.' in content and 'try:' not in content:
                        issues_found.append(f"[ERROR] {file}: Missing error handling for HTTP requests")
                    
                    # Check for hardcoded API keys
                    if 'api_key' in content.lower() and '=' in content and 'os.getenv' not in content:
                        issues_found.append(f"[WARNING] {file}: Possible hardcoded API key")
                    
                    # Check for print statements (should use logging)
                    if 'print(' in content:
                        issues_found.append(f"[INFO] {file}: Using print() instead of logging")
    
    # Check for test files
    test_count = 0
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.startswith('test_') and file.endswith('.py'):
                test_count += 1
    
    if test_count < 3:
        issues_found.append(f"[WARNING] Insufficient test coverage: Only {test_count} test files found")
    
    # Check for documentation
    if not os.path.exists('README.md'):
        issues_found.append("[DOC] Missing README.md documentation")
    
    # Check for requirements.txt
    if not os.path.exists('requirements.txt'):
        issues_found.append("[PACKAGE] Missing requirements.txt file")
    
    # Display findings
    if issues_found:
        print(f"\n[ALERT] Found {len(issues_found)} issues:\n")
        for issue in issues_found:
            print(f"  {issue}")
    else:
        print("\n[OK] No immediate issues found!")
    
    print("\n" + "=" * 70)
    
    return issues_found

if __name__ == "__main__":
    print("\nLEAD GENERATION PROJECT REPAIR SYSTEM")
    print("=" * 70)
    
    # Run quick audit first
    issues = quick_audit()
    
    if issues:
        print(f"\n[RECOMMENDATION] Run the automated repair to fix these {len(issues)} issues.")
    
    # Start the repair process
    automated_repair()