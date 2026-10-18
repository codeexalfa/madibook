#!/bin/bash
# Phase 6: Deploy all 11 MediBook Lambdas in us-east-1
# Runtime: python3.12
# Architecture: x86_64

python "$(dirname "$0")/06_lambdas.py"
