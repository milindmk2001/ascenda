#!/usr/bin/env bash
# Wrapper to run sync_chapter1_dev_from_prod.py from an Anaconda shell
# (Anaconda Prompt on Windows with bash/Git Bash/WSL, or macOS/Linux terminal).
#
# Usage:
#   chmod +x run_sync.sh
#   ./run_sync.sh
#
# Prompts for the two DB connection strings at runtime (not echoed to screen,
# not saved anywhere) rather than hardcoding them in a file.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY_SCRIPT="$SCRIPT_DIR/sync_chapter1_dev_from_prod.py"

if [ ! -f "$PY_SCRIPT" ]; then
    echo "ERROR: sync_chapter1_dev_from_prod.py not found in $SCRIPT_DIR"
    echo "Make sure both files are in the same folder."
    exit 1
fi

# Activate a conda env if one is named via CONDA_ENV_NAME, otherwise use
# whatever's already active (e.g. 'base').
if [ "${CONDA_ENV_NAME:-}" != "" ]; then
    # shellcheck disable=SC1091
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate "$CONDA_ENV_NAME"
fi

echo "Using Python: $(which python3 || which python)"

# Ensure dependency is present
python3 -c "import psycopg2" 2>/dev/null || pip install psycopg2-binary

# Prompt for connection strings if not already exported in this shell
if [ -z "${PROD_DATABASE_URL:-}" ]; then
    read -r -p "Enter PROD (ascenda) DATABASE_URL: " PROD_DATABASE_URL
    export PROD_DATABASE_URL
fi

if [ -z "${DEV_DATABASE_URL:-}" ]; then
    read -r -p "Enter DEV (ascenda-dev) DATABASE_URL: " DEV_DATABASE_URL
    export DEV_DATABASE_URL
fi

echo ""
echo "Running sync script..."
python3 "$PY_SCRIPT"

# Clear the vars from this shell once done
unset PROD_DATABASE_URL
unset DEV_DATABASE_URL
