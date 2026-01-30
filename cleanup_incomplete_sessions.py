#!/usr/bin/env python3
"""
Cleanup utility for incomplete PRD refinement sessions
"""
import json
from pathlib import Path
from datetime import datetime

def cleanup_incomplete_sessions(dry_run=True):
    """Remove incomplete sessions (those without convergence reports)"""

    base_dir = Path("data/prds")
    index_file = base_dir / "prd_index.json"

    if not index_file.exists():
        print("No index file found. Nothing to clean up.")
        return

    # Load index
    index_data = json.loads(index_file.read_text())
    sessions = index_data.get("sessions", [])

    incomplete_sessions = []
    complete_sessions = []

    # Find incomplete sessions
    for session in sessions:
        session_id = session["session_id"]
        session_dir = base_dir / session_id
        report_file = session_dir / "convergence_report.json"

        if not report_file.exists():
            incomplete_sessions.append(session)
            if dry_run:
                print(f"[DRY RUN] Would delete: {session_id} ({session['title']})")
            else:
                print(f"Deleting: {session_id} ({session['title']})")
                # Delete directory
                import shutil
                shutil.rmtree(session_dir)
        else:
            complete_sessions.append(session)

    # Update index if not dry run
    if not dry_run and incomplete_sessions:
        index_data["sessions"] = complete_sessions
        index_file.write_text(json.dumps(index_data, indent=2))
        print(f"\nUpdated index file. Removed {len(incomplete_sessions)} incomplete sessions.")

    # Summary
    print(f"\n{'=' * 60}")
    print(f"Summary:")
    print(f"  Complete sessions: {len(complete_sessions)}")
    print(f"  Incomplete sessions: {len(incomplete_sessions)}")

    if dry_run and incomplete_sessions:
        print(f"\nThis was a DRY RUN. No files were deleted.")
        print(f"Run with --execute to actually delete incomplete sessions.")
    elif incomplete_sessions:
        print(f"\n✓ Cleanup complete. {len(incomplete_sessions)} sessions removed.")

def main():
    import sys

    print("PRD Refinement Session Cleanup Utility")
    print("=" * 60)
    print()

    # Check for --execute flag
    if "--execute" in sys.argv or "-e" in sys.argv:
        print("⚠️  EXECUTING CLEANUP (files will be deleted)")
        response = input("Are you sure? Type 'yes' to continue: ")
        if response.lower() != 'yes':
            print("Cleanup cancelled.")
            return
        cleanup_incomplete_sessions(dry_run=False)
    else:
        print("Running in DRY RUN mode (no files will be deleted)")
        print()
        cleanup_incomplete_sessions(dry_run=True)

if __name__ == "__main__":
    main()
