#!/usr/bin/env bash
# One-shot setup: create a venv and install dependencies (Unix / Git Bash).
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="C:/Users/19473/.workbuddy/binaries/python/versions/3.13.12/python.exe"
VENV="C:/Users/19473/.workbuddy/binaries/python/envs/default"

"$PY" -m venv "$VENV"
source "$VENV/Scripts/activate"
pip install --upgrade pip
pip install -r "$ROOT/requirements.txt"
echo "Install complete. Activate with: source $VENV/Scripts/activate"
