#!/usr/bin/env bash
# ==============================================================================
# Caliper: Universal Sewing Machine Setup & Calibration Agent
# Zero-Config macOS Localhost Launcher (Double-Click or "bash START_HERE_MAC.command")
# ==============================================================================

cd "$(dirname "$0")" || exit 1

echo "=================================================================="
echo " 🌸 Caliper: The Sewing & Calibration Atelier"
echo " Universal Sewing Machine Setup & Calibration Agent"
echo "=================================================================="
echo ""

# 1. Verify Python 3 is installed
if ! command -v python3 &>/dev/null; then
    echo "❌ [ERROR] Python 3 was not found on your Mac."
    echo "Please download and install Python 3.10+ from:"
    echo "👉 https://www.python.org/downloads/macos/"
    echo ""
    read -n 1 -s -r -p "Press any key to exit..."
    echo ""
    exit 1
fi

# 2. Setup isolated virtual environment in .venv
if [ ! -d ".venv" ]; then
    echo "📦 [Caliper] Creating isolated virtual environment in .venv..."
    python3 -m venv .venv || {
        echo "❌ [ERROR] Failed to create virtual environment."
        exit 1
    }
fi

# 3. Activate virtual environment
source .venv/bin/activate || {
    echo "❌ [ERROR] Failed to activate virtual environment."
    exit 1
}

# 4. Install dependencies if marker is missing
if [ ! -f ".venv/.deps_installed" ]; then
    echo "🧵 [Caliper] First-time setup: installing dependencies from requirements.txt..."
    python -m pip install --upgrade pip --quiet
    pip install -r requirements.txt || {
        echo "❌ [ERROR] Failed to install dependencies."
        exit 1
    }
    touch .venv/.deps_installed
    echo "✨ [Caliper] Dependencies successfully installed!"
    echo ""
fi

# 5. Start Caliper Web Application
echo "🪡 [Caliper] Starting Caliper Atelier server on http://127.0.0.1:7860..."
python app.py &
SERVER_PID=$!

cleanup() {
    echo ""
    echo "🧵 [Caliper] Shutting down server (PID $SERVER_PID)..."
    kill "$SERVER_PID" 2>/dev/null
    wait "$SERVER_PID" 2>/dev/null
    exit 0
}
trap cleanup INT TERM EXIT

# 6. Poll health check until database is ready, then open browser
echo "🔍 [Caliper] Pre-loading 50-machine hardware database..."
READY=0
for i in $(seq 1 30); do
    if curl -s -f "http://127.0.0.1:7860/api/machines" >/dev/null 2>&1; then
        READY=1
        break
    fi
    sleep 0.5
done

if [ $READY -eq 1 ]; then
    echo "✨ [Caliper] Hardware database loaded! Opening browser..."
    open "http://127.0.0.1:7860"
else
    echo "⚠️  [Caliper] Server is taking longer to respond. Please open http://127.0.0.1:7860 manually."
fi

echo ""
echo "=================================================================="
echo " 🌟 Caliper Atelier is live at: http://127.0.0.1:7860"
echo " (Keep this Terminal window open. Press Ctrl+C to stop the server)"
echo "=================================================================="
echo ""

wait "$SERVER_PID"

