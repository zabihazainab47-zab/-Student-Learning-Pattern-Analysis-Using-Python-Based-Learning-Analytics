"""
run.py — Application runner script
Starts the FastAPI application using uvicorn.
"""

import sys
from pathlib import Path
import uvicorn

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main():
    print("Starting Student Learning Pattern Analysis backend...")
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    main()
