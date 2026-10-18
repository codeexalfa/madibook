#!/usr/bin/env bash
set -e
echo "MediBook Resource Cleanup"
python "$(dirname "$0")/99_cleanup.py"
