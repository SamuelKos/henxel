#!/usr/bin/env bash

# Get error message for osascript 

p=$(git rev-parse --show-toplevel)
result=$(python $p/dev/launch_test.py 2>&1 >/dev/null)

echo $result

