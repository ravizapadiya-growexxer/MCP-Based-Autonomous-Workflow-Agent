#!/usr/bin/env bash
set -e

echo "=== MCP Workflow Agent Setup ==="

# Create virtualenv
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium

# Create directories
mkdir -p logs/morning logs/evening logs/error logs/screenshots data

# Copy env template
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env — please fill in your credentials"
fi

echo ""
echo "✅ Setup complete."
echo ""
echo "Next steps:"
echo "  1. Edit .env with your Jira URL, API token, timesheet URL, etc."
echo "  2. Find your Jira transition IDs:"
echo "       make list-transitions"
echo "  3. Store passwords securely in keyring:"
echo "       python -c \"import keyring; keyring.set_password('mcp-agent','JIRA_API_TOKEN','token_here')\""
echo "       python -c \"import keyring; keyring.set_password('mcp-agent','TIMESHEET_PASSWORD','pwd_here')\""
echo "  4. Setup WhatsApp (CallMeBot):"
echo "       - Add +34 644 59 71 28 to WhatsApp"
echo "       - Send: I allow callmebot to send me messages"
echo "       - You'll receive WHATSAPP_APIKEY via WhatsApp"
echo "       - Set WHATSAPP_PHONE and WHATSAPP_APIKEY in .env"
echo "  5. Test dry run:"
echo "       make dry-morning"
echo "  6. Start agent:"
echo "       make run"
