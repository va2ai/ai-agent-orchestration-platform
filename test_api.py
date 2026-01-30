#!/usr/bin/env python3
"""
Test script for PRD Refinement API
"""
import requests
import json
import time
from pathlib import Path

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    print(f"✓ Health check: {response.json()}")

def test_list_sessions():
    """Test list sessions"""
    print("\nTesting list sessions...")
    response = requests.get(f"{BASE_URL}/api/sessions/")
    assert response.status_code == 200
    data = response.json()
    print(f"✓ Found {data['total']} sessions")
    return data['sessions']

def test_start_refinement():
    """Test starting a refinement"""
    print("\nTesting start refinement...")

    # Read test PRD
    prd_file = Path("test_api_prd.md")
    if not prd_file.exists():
        print("✗ test_api_prd.md not found")
        return None

    content = prd_file.read_text()

    # Start refinement
    response = requests.post(
        f"{BASE_URL}/api/refinement/start",
        json={
            "title": "User Profile Management",
            "content": content,
            "max_iterations": 2  # Use 2 for faster testing
        }
    )

    assert response.status_code == 200
    data = response.json()
    print(f"✓ Refinement started: {data['session_id']}")
    return data['session_id']

def test_get_status(session_id):
    """Test getting refinement status"""
    print(f"\nTesting status for {session_id}...")

    # Poll status
    max_attempts = 60  # Wait up to 5 minutes
    for i in range(max_attempts):
        response = requests.get(f"{BASE_URL}/api/refinement/status/{session_id}")
        assert response.status_code == 200
        data = response.json()

        print(f"  Iteration {data['current_iteration']}/{data['max_iterations']} - Status: {data['status']}")

        if data['status'] == 'completed':
            print(f"✓ Refinement completed!")
            print(f"  Converged: {data['converged']}")
            print(f"  Reason: {data['convergence_reason']}")
            return data

        if data['status'] == 'failed':
            print(f"✗ Refinement failed: {data.get('convergence_reason', 'Unknown error')}")
            return None

        time.sleep(5)

    print("✗ Timeout waiting for completion")
    return None

def test_get_final_prd(session_id, version):
    """Test getting final PRD"""
    print(f"\nTesting get PRD v{version}...")
    response = requests.get(f"{BASE_URL}/api/sessions/{session_id}/prd/{version}")
    assert response.status_code == 200
    data = response.json()
    print(f"✓ PRD retrieved: {len(data['content'])} characters")
    print(f"\nFirst 500 chars of refined PRD:")
    print("-" * 60)
    print(data['content'][:500])
    print("-" * 60)
    return data

def test_get_report(session_id):
    """Test getting convergence report"""
    print(f"\nTesting convergence report...")
    response = requests.get(f"{BASE_URL}/api/sessions/{session_id}/report")
    assert response.status_code == 200
    data = response.json()
    print(f"✓ Report retrieved")
    print(f"  Iterations: {data['iterations']}")
    print(f"  Converged: {data['converged']}")
    print(f"  Final issues: {data['final_issue_count']['high']} high, {data['final_issue_count']['medium']} medium")

    total_tokens = sum(data['token_usage'].values())
    print(f"  Total tokens: {total_tokens:,}")
    return data

def main():
    print("=" * 60)
    print("PRD Refinement API Test Suite")
    print("=" * 60)

    try:
        # Test 1: Health
        test_health()

        # Test 2: List sessions
        sessions = test_list_sessions()

        # Test 3: Start refinement
        session_id = test_start_refinement()
        if not session_id:
            print("\n✗ Failed to start refinement")
            return

        # Test 4: Monitor status
        status = test_get_status(session_id)
        if not status:
            print("\n✗ Failed to complete refinement")
            return

        # Test 5: Get final PRD
        final_version = status['current_version']
        prd = test_get_final_prd(session_id, final_version)

        # Test 6: Get report
        report = test_get_report(session_id)

        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        print(f"\nView results in dashboard:")
        print(f"  http://localhost:8000/")
        print(f"\nSession ID: {session_id}")

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
    except requests.exceptions.ConnectionError:
        print("\n✗ Connection failed. Is the server running?")
        print("  Start with: python run_api.py")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
