#!/usr/bin/env bash
# TSIS 2: Run Judge Agent (Gemini CLI alternative — uses Python script with env)
# Ensure GOOGLE_API_KEY or OPENAI_API_KEY is set in .env, then:
#   bash judge.sh
# Or with inline env:
#   GOOGLE_API_KEY=xxx bash judge.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

python judge.py
