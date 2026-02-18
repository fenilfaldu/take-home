#!/bin/bash

mkdir -p /logs/verifier

cd /app

python3 /tests/test_outputs.py 2>&1 | tee /logs/verifier/test_output.log
exit_code=${PIPESTATUS[0]}

if [ $exit_code -eq 0 ]; then
    echo 1 > /logs/verifier/reward.txt
else
    echo 0 > /logs/verifier/reward.txt
fi

cat /logs/verifier/reward.txt