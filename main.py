#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
from ai_orchestrator.orchestration.looping_orchestrator import LoopingOrchestrator
from dotenv import load_dotenv

def main():
    # Load environment
    load_dotenv()

    # Parse arguments
    parser = argparse.ArgumentParser(description="Looping PRD Refinement Agent")
    parser.add_argument("--input", required=True, help="Path to initial PRD file")
    parser.add_argument("--title", help="PRD title (default: filename)")
    parser.add_argument("--max-iterations", type=int, default=3, help="Max refinement iterations (default: 3)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging (show LLM outputs)")

    args = parser.parse_args()

    # Read initial PRD
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: File not found: {args.input}")
        sys.exit(1)

    initial_content = input_path.read_text(encoding="utf-8")
    title = args.title or input_path.stem

    print(f"Starting PRD Refinement")
    print(f"   Title: {title}")
    print(f"   Max Iterations: {args.max_iterations}")
    print(f"   Verbose: {args.verbose}")
    print()

    # Run orchestrator
    orchestrator = LoopingOrchestrator(max_iterations=args.max_iterations, verbose=args.verbose)
    final_prd, report = orchestrator.run(title, initial_content)

    # Print summary
    print("\n" + "="*60)
    print("REFINEMENT COMPLETE")
    print("="*60)
    print(f"Final Version: {final_prd.version}")
    print(f"Converged: {report['converged']}")
    print(f"Reason: {report['convergence_reason']}")
    print(f"Final Issues: {report['final_issue_count']['high']} high, "
          f"{report['final_issue_count']['medium']} medium, "
          f"{report['final_issue_count']['low']} low")

    # Token usage
    if 'token_usage' in report:
        total_tokens = sum(report['token_usage'].values())
        print(f"\nToken Usage:")
        for agent, tokens in report['token_usage'].items():
            print(f"  {agent}: {tokens:,} tokens")
        print(f"  TOTAL: {total_tokens:,} tokens")

    print(f"\nSession: {report['session_id']}")
    print(f"Detailed logs: data/prds/{report['session_id']}/refinement.log")
    print()

if __name__ == "__main__":
    main()
