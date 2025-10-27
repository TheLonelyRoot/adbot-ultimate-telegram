#!/data/data/com.termux/files/usr/bin/bash
# Termux setup helper for Hybrid Ad Bot
# Usage: chmod +x termux_setup.sh && ./termux_setup.sh
#
# Credit: All code and logic by @TheLonelyRoot
set -euo pipefail

echo "Updating packages..."
pkg update -y && pkg upgrade -y

echo "Installing required system packages..."
pkg install -y python git clang openssl-tool libffi-dev make pkg-config

# Optional: rust if building some wheels
# pkg install -y rust

echo "Setting up virtual environment..."
python -m venv .venv
. .venv/bin/activate

echo "Upgrading pip and installing Python requirements..."
pip install --upgrade pip
if [ -f requirements.txt ]; then
  pip install -r requirements.txt
else
  pip install telethon rich
fi

echo "Setup complete. To run the bot:"
echo "  . .venv/bin/activate"
echo "  python hybrid_bot.py"

# Keep script idempotent
exit 0
