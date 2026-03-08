"""
Run the Phase 7 FastAPI backend (uvicorn).

Usage: python -m phase7_backend.run_server
Or: uvicorn phase7_backend.app:app --reload --host 0.0.0.0 --port 8000
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "phase7_backend.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
