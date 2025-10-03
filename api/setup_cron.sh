#!/bin/bash
# Setup cron job for automated data updates
# Run this script to set up automated updates every 3 hours

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH=$(which python3)

echo "Setting up automated data updates..."

# Create the cron job entry
CRON_ENTRY="0 */3 * * * cd $SCRIPT_DIR && $PYTHON_PATH auto_data_updater.py >> data_update.log 2>&1"

# Add to crontab
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

echo "✅ Cron job added successfully!"
echo "📅 Data will update every 3 hours"
echo "📝 Logs will be saved to: $SCRIPT_DIR/data_update.log"
echo ""
echo "To view current cron jobs: crontab -l"
echo "To remove this job: crontab -e (then delete the line)"

