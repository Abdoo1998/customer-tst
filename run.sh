#!/bin/bash

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "ngrok is not installed. Please install it first."
    exit 1
fi

# Check if uvicorn is installed
if ! command -v uvicorn &> /dev/null; then
    echo "uvicorn is not installed. Please install it first."
    exit 1
fi

# Start the uvicorn server in the background
uvicorn app:app --host 0.0.0.0 --port 5000 &
UVICORN_PID=$!

# Wait a few seconds for uvicorn to start
sleep 3

# Start ngrok
ngrok http 5000

# When ngrok is stopped (Ctrl+C), kill the uvicorn process
kill $UVICORN_PID 