#!/usr/bin/env python3
"""
Run the PRD Refinement API Server
"""
import uvicorn
from dotenv import load_dotenv

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()

    # Run server
    print("Starting PRD Refinement API Server...")
    print("Dashboard: http://localhost:8000/")
    print("API Docs: http://localhost:8000/docs")
    print("")

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disabled reload to fix import issues
        log_level="info"
    )
