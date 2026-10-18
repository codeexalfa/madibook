#!/usr/bin/env bash
set -e
echo "Executing Phase 13: System Verification Tests..."
python "$(dirname "$0")/13_system_tests.py"
