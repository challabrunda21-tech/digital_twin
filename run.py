"""
Application Runner for AI-Based Digital Twin Monitoring Platform
Usage:=
    python run.py [--port 8000] [--host 127.0.0.1]
"""

import sys
import os
import argparse

# Seamless virtual environment auto-detection
venv_python = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv", "bin", "python")
if os.path.exists(venv_python) and os.path.abspath(sys.executable) != os.path.abspath(venv_python):
    try:
        import uvicorn
        import starlette
    except ImportError:
        os.execv(venv_python, [venv_python] + sys.argv)

import uvicorn

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start the AI-Based Digital Twin Platform")
    parser.add_argument("--host", default="127.0.0.1", help="Host IP to bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable hot reload")
    args = parser.parse_args()

    print("=" * 70)
    print(" AI-BASED DIGITAL TWIN FOR INDUSTRIAL EQUIPMENT MONITORING")
    print(" & PREDICTIVE MAINTENANCE")
    print("=" * 70)
    print(f" -> Serving at: http://{args.host}:{args.port}")
    print(f" -> Press CTRL+C to stop the server.")
    print("=" * 70)

    uvicorn.run("app:app", host=args.host, port=args.port, reload=args.reload)
