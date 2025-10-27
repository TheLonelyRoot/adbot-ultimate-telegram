#!/bin/bash
# Sanitize repository for sale/distribution: deletes session files and audit DB, and clears credentials.
set -e
FILES=(
  "hybrid_bot.session" "hybrid_bot.session-journal" "main.session" "main.session-journal"
  "pure_user_session.session" "test_bot.session" "audit.db"
)
for f in "${FILES[@]}"; do
  if [ -f "$f" ]; then
    echo "Removing $f"
    rm -f "$f"
  fi
done

echo "Clearing credentials.csv"
cat > credentials.csv <<'CSV'
credential_type,api_id,api_hash,bot_token,phone,session_name,description,active
# Add your credentials here. Example:
# telegram_api,123456,abcdef1234567890,,+1234567890,my_session,Main Telegram API credentials for user client,true
CSV

echo "Sanitization complete. Verify no session or audit files remain."
exit 0
