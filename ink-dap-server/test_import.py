#!/usr/bin/env python3
"""
Simple DAP client for testing the debug adapter
"""

import json
import subprocess
import time
from typing import Dict, Any


class TestDAPClient:
    """Simple DAP client for testing."""

    def __init__(self):
        self.process = None
        self.sequence = 1

    def start_adapter(self):
        """Start the debug adapter process."""
        print("Starting debug adapter...")
        self.process = subprocess.Popen(
            ["python", "main.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        time.sleep(1)  # Give it time to start

    def send_request(self, command: str, arguments: Dict[str, Any] = None):
        """Send a DAP request."""
        request = {
            "seq": self.sequence,
            "type": "request",
            "command": command
        }
        if arguments:
            request["arguments"] = arguments

        self.sequence += 1

        # Encode message
        body = json.dumps(request)
        message = f"Content-Length: {len(body)}\r\n\r\n{body}"

        print(f"\n→ Sending: {command}")
        print(f"  {request}")

        # Send to adapter
        self.process.stdin.write(message)
        self.process.stdin.flush()

    def read_response(self):
        """Read a response from the adapter."""
        # Read headers
        headers = {}
        while True:
            line = self.process.stdout.readline()
            if not line or line == "\r\n":
                break
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip()] = value.strip()

        # Read body
        if "Content-Length" in headers:
            length = int(headers["Content-Length"])
            body = self.process.stdout.read(length)
            response = json.loads(body)

            print(f"\n← Received: {response.get('command', response.get('event', 'unknown'))}")
            print(f"  {response}")

            return response
        return None

    def test_initialize(self):
        """Test initialize sequence."""
        print("\n=== Testing Initialize ===")

        # Send initialize request
        self.send_request("initialize", {
            "clientID": "test-client",
            "clientName": "Test DAP Client",
            "adapterID": "ink-debugger",
            "pathFormat": "path",
            "linesStartAt1": True,
            "columnsStartAt1": True
        })

        # Read response
        response = self.read_response()

        # Read initialized event
        event = self.read_response()

    def test_launch(self):
        """Test launch sequence."""
        print("\n=== Testing Launch ===")

        self.send_request("launch", {
            "program": "/path/to/contract.wasm",
            "stopOnEntry": True
        })

        response = self.read_response()

    def test_set_breakpoints(self):
        """Test setting breakpoints."""
        print("\n=== Testing Set Breakpoints ===")

        self.send_request("setBreakpoints", {
            "source": {
                "path": "/path/to/contract.rs"
            },
            "breakpoints": [
                {"line": 10},
                {"line": 20},
                {"line": 30}
            ]
        })

        response = self.read_response()

    def test_threads(self):
        """Test threads request."""
        print("\n=== Testing Threads ===")

        self.send_request("threads")
        response = self.read_response()

    def run_tests(self):
        """Run all tests."""
        try:
            self.start_adapter()

            # Run test sequence
            self.test_initialize()
            time.sleep(0.5)

            self.test_launch()
            time.sleep(0.5)

            self.test_set_breakpoints()
            time.sleep(0.5)

            self.test_threads()
            time.sleep(0.5)

            # Disconnect
            print("\n=== Disconnecting ===")
            self.send_request("disconnect")
            time.sleep(1)

        finally:
            if self.process:
                self.process.terminate()
                print("\nDebug adapter terminated")


if __name__ == "__main__":
    client = TestDAPClient()
    client.run_tests()