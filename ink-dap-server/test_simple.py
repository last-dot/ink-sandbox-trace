#!/usr/bin/env python3
"""
Simple test to check if DAP protocol works
"""

import sys
import json

# Send a simple DAP message
message = {
    "seq": 1,
    "type": "request",
    "command": "initialize",
    "arguments": {
        "clientID": "test",
        "adapterID": "ink"
    }
}

body = json.dumps(message)
sys.stdout.write(f"Content-Length: {len(body)}\r\n\r\n{body}")
sys.stdout.flush()

print("\nSent initialize request to stdout", file=sys.stderr)
print("Waiting for any input from stdin...", file=sys.stderr)

# Try to read anything from stdin
try:
    line = sys.stdin.readline()
    print(f"Got from stdin: {line}", file=sys.stderr)
except Exception as e:
    print(f"Error reading stdin: {e}", file=sys.stderr)