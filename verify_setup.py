#!/usr/bin/env python3
"""
Verification script for Looping PRD Refinement Agent
Checks all imports, models, and dependencies
"""

import sys
import os
from pathlib import Path

def check_imports():
    """Test all critical imports"""
    print("Checking imports...")
    try:
        from ai_orchestrator.agents.prd_critic import PRDCritic
        from ai_orchestrator.agents.engineering_critic import EngineeringCritic
        from ai_orchestrator.agents.ai_risk_critic import AIRiskCritic
        from ai_orchestrator.agents.moderator import Moderator
        from ai_orchestrator.models.prd_models import PRD, PRDReview, PRDIssue
        from ai_orchestrator.storage.prd_storage import PRDStorage
        from ai_orchestrator.utils.convergence import ConvergenceChecker
        from ai_orchestrator.orchestration.looping_orchestrator import LoopingOrchestrator
        from ai_orchestrator import run_roundtable, RoundtableConfig
        print("  All imports successful")
        return True
    except ImportError as e:
        print(f"  Import error: {e}")
        return False

def check_dependencies():
    """Check required dependencies"""
    print("\nChecking dependencies...")
    try:
        import langchain
        import langchain_openai
        import langchain_core
        import openai
        import pydantic
        import dotenv
        print("  All dependencies installed")
        return True
    except ImportError as e:
        print(f"  Missing dependency: {e}")
        return False

def check_api_key():
    """Check for OpenAI API key"""
    print("\nChecking OpenAI API key...")
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print(f"  API key found: {api_key[:10]}...{api_key[-4:]}")
        return True
    else:
        print("  WARNING: No OPENAI_API_KEY found in environment")
        return False

def check_directories():
    """Check required directories exist"""
    print("\nChecking directories...")
    required_dirs = [
        "src/ai_orchestrator/agents",
        "src/ai_orchestrator/models",
        "src/ai_orchestrator/orchestration",
        "src/ai_orchestrator/storage",
        "src/ai_orchestrator/prompts",
        "src/ai_orchestrator/utils",
        "data/prds"
    ]
    all_exist = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"  {dir_path}: OK")
        else:
            print(f"  {dir_path}: MISSING")
            all_exist = False
    return all_exist

def check_models():
    """Test Pydantic models"""
    print("\nChecking Pydantic models...")
    try:
        from ai_orchestrator.models.prd_models import PRD, PRDIssue, PRDReview

        # Create test issue
        issue = PRDIssue(
            category="product",
            description="Test issue",
            severity="High",
            suggested_fix="Fix it",
            reviewer="test_critic"
        )

        # Create test review
        review = PRDReview(
            reviewer="test_critic",
            issues=[issue],
            overall_assessment="Test assessment"
        )

        # Create test PRD
        prd = PRD(
            version=1,
            title="Test PRD",
            content="Test content",
            reviews=[review]
        )

        print("  Models validated successfully")
        print(f"    - PRDIssue: {issue.severity}")
        print(f"    - PRDReview: {len(review.issues)} issue(s)")
        print(f"    - PRD: v{prd.version}")
        return True
    except Exception as e:
        print(f"  Model validation error: {e}")
        return False

def check_storage():
    """Test storage functionality"""
    print("\nChecking storage...")
    try:
        from ai_orchestrator.storage.prd_storage import PRDStorage
        storage = PRDStorage()
        print(f"  Storage initialized: {storage.base_dir}")
        print(f"  Index file exists: {storage.index_file.exists()}")
        return True
    except Exception as e:
        print(f"  Storage error: {e}")
        return False

def main():
    """Run all verification checks"""
    print("="*60)
    print("Looping PRD Refinement Agent - Setup Verification")
    print("="*60)

    results = {
        "Imports": check_imports(),
        "Dependencies": check_dependencies(),
        "API Key": check_api_key(),
        "Directories": check_directories(),
        "Models": check_models(),
        "Storage": check_storage()
    }

    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)

    for check, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"{check:20} {status}")

    all_passed = all(results.values())

    print("="*60)
    if all_passed:
        print("All checks passed! System is ready to use.")
        print("\nRun: python main.py --input test_prd.md")
        return 0
    else:
        print("Some checks failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
