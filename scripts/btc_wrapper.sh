#!/usr/bin/env bash
set -euo pipefail
REPO_DIR="${REPO_DIR:-$HOME/Desktop/coinglass-v4-batch3}"
cd "$REPO_DIR"
DATA_MODE="${DATA_MODE:-free}" python3 batch_system/btc_cli.py
