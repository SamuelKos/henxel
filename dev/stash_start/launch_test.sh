#!/usr/bin/env bash

# Get return code of last command for osascript

p=$(git rev-parse --show-toplevel)

python $p/dev/launch_test.py

var=$?

echo $var
