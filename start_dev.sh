#!/bin/bash
trap "kill 0" EXIT

echo "Starting Backend..."
python3 -m server.main &

echo "Starting Frontend..."
cd client && npm run dev &

wait
