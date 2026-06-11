"""
AppSec Orchestrator - Run this file to start the application.

Usage:
    python run.py

Then open: http://localhost:5000
"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    print("\n" + "="*50)
    print("  AppSec Orchestrator")
    print("  http://localhost:5000")
    print("="*50 + "\n")
    app.run(host="127.0.0.1", port=5000, debug=True)
