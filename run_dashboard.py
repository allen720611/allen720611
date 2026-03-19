"""
Run the AI Investment Signals web dashboard.
Usage: python run_dashboard.py
Then open: http://127.0.0.1:8050
"""
import subprocess
import sys
import os

def check_flask():
    try:
        import flask
        return True
    except ImportError:
        return False

if not check_flask():
    print("Installing flask...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "flask"])

# Run from web_app directory so templates resolve correctly
os.chdir(os.path.join(os.path.dirname(__file__), "web_app"))
os.environ.setdefault("PORT", "8050")

import app as dashboard_app
port = int(os.environ.get("PORT", 8050))
print(f"\n AI Investment Dashboard")
print(f"   開啟瀏覽器前往: http://127.0.0.1:{port}\n")
dashboard_app.app.run(debug=False, host="0.0.0.0", port=port)
