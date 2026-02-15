#!/bin/bash
# Stripe License Poller - Cron Wrapper
# 
# This script runs the poller and handles basic error cases.
# Add to crontab to run automatically.
#
# Example crontab entries:
# 
# # Run every hour
# 0 * * * * /Users/ripley/.openclaw/workspace/file_organizer/poll_stripe.sh >> ~/.openclaw/logs/stripe_poller.log 2>&1
#
# # Run every 4 hours (less frequent)
# 0 */4 * * * /Users/ripley/.openclaw/workspace/file_organizer/poll_stripe.sh >> ~/.openclaw/logs/stripe_poller.log 2>&1
#
# # Run twice daily
# 0 9,21 * * * /Users/ripley/.openclaw/workspace/file_organizer/poll_stripe.sh >> ~/.openclaw/logs/stripe_poller.log 2>&1

WORKSPACE="/Users/ripley/.openclaw/workspace/file_organizer"
LOG_DIR="$HOME/.openclaw/logs"
PYTHON="$WORKSPACE/.venv/bin/python"
POLLER="$WORKSPACE/src/core/stripe_poller.py"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Check if virtual environment exists
if [ ! -f "$PYTHON" ]; then
    PYTHON="python3"
fi

# Run poller
echo "[$(date)] Running Stripe poller..."
cd "$WORKSPACE"

# Run with timeout (5 minutes max)
timeout 300 "$PYTHON" "$POLLER" --hours 4

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date)] Poller completed successfully"
elif [ $EXIT_CODE -eq 124 ]; then
    echo "[$(date)] ⚠️ Poller timed out after 5 minutes"
    # Could send alert here
else
    echo "[$(date)] ❌ Poller failed with exit code $EXIT_CODE"
    # Could send alert here
fi

exit $EXIT_CODE
