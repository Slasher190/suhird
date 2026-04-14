#!/usr/bin/env bash
# Apply Suhird configuration to OpenClaw
# Usage: bash scripts/apply_openclaw_config.sh
#
# This script:
# 1. Backs up current openclaw.json
# 2. Updates dmPolicy to "open"
# 3. Adds suhird-bot as a model provider
# 4. Restarts the OpenClaw gateway

set -euo pipefail

OPENCLAW_CONFIG="$HOME/.openclaw/openclaw.json"
BACKUP="$OPENCLAW_CONFIG.bak.suhird"

echo "=== Suhird OpenClaw Configuration ==="

if [ ! -f "$OPENCLAW_CONFIG" ]; then
    echo "ERROR: OpenClaw config not found at $OPENCLAW_CONFIG"
    exit 1
fi

# Backup
cp "$OPENCLAW_CONFIG" "$BACKUP"
echo "Backed up config to $BACKUP"

# Use Python to merge the config since jq may not be available
python3 << 'PYEOF'
import json
import sys
from pathlib import Path

config_path = Path.home() / ".openclaw" / "openclaw.json"
config = json.loads(config_path.read_text())

# 1. Change dmPolicy to "open"
if "channels" not in config:
    config["channels"] = {}
if "whatsapp" not in config["channels"]:
    config["channels"]["whatsapp"] = {}
config["channels"]["whatsapp"]["dmPolicy"] = "open"
print("  Updated dmPolicy to 'open'")

# 2. Add suhird-bot model provider
if "models" not in config:
    config["models"] = {}
if "providers" not in config["models"]:
    config["models"]["providers"] = {}

config["models"]["providers"]["suhird-bot"] = {
    "baseUrl": "http://localhost:8000/v1",
    "apiKey": "${SUHIRD_API_TOKEN}",
    "api": "openai-responses",
    "models": [
        {
            "id": "matchmaker",
            "name": "Suhird Matchmaker",
            "reasoning": False,
            "input": ["text"],
            "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0},
            "contextWindow": 4096,
            "maxTokens": 4096,
        }
    ],
}
print("  Added suhird-bot model provider")

# 3. Add agent config for unknown numbers
if "agents" not in config:
    config["agents"] = {}
if "list" not in config["agents"]:
    config["agents"]["list"] = []

# Check if suhird agent already exists
existing = [a for a in config["agents"]["list"] if a.get("id") == "suhird-matchmaker"]
if not existing:
    config["agents"]["list"].append({
        "id": "suhird-matchmaker",
        "model": "suhird-bot/matchmaker",
        "description": "Suhird matchmaker for unknown WhatsApp numbers",
    })
    print("  Added suhird-matchmaker agent")

config_path.write_text(json.dumps(config, indent=2))
print("  Config saved successfully")
PYEOF

echo ""
echo "Configuration applied! You may need to restart OpenClaw:"
echo "  launchctl stop ai.openclaw.gateway"
echo "  launchctl start ai.openclaw.gateway"
echo ""
echo "Or if running manually, restart the gateway process."
