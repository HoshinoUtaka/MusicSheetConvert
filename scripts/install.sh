#!/usr/bin/env bash
# One-shot setup: create a venv and install dependencies (Unix / Git Bash).
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
set PY="path_to_your_python"
set VENV="path_to_your_venv"

"$PY" -m venv "$VENV"
source "$VENV/Scripts/activate"
pip install --upgrade pip
pip install -r "$ROOT/requirements.txt"
echo "Install complete. Activate with: source $VENV/Scripts/activate"
