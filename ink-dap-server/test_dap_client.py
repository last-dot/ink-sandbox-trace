#!/usr/bin/env python3
"""
Simple DAP client for testing the debug adapter
"""

import json
import subprocess
import time
import sys
import os
from typing import Dict, Any


class TestDAPClient:
    """Simple DAP client for testing."""

    def __init__(self):
        self.process = None
        self.sequence = 1

    def start_adapter(self):
        """Start the debug adapter process."""
        print("Starting debug adapter...")

        # Use the same Python interpreter as current script
        python_exe = sys.executable

        # Get the directory of this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        main_py = os.path.join(script_dir, "main.py")

        print(f"Python: {python_exe}")
        print(f"Main.py: {main_py}")
        print(f"Working dir: {script_dir}")

        self.process = subprocess.Popen(
            [python_exe, main_py],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=script_dir
        )
        time.sleep(1)  # Give it time to start

        # Check if process is still running
        if self.process.poll() is not None:
            # Process died, read stderr
            stderr = self.process.stderr.read()
            print(f"Debug adapter crashed! Error:\n{stderr}")
            raise RuntimeError("Debug adapter failed to start")

    def send_request(self, command: str, arguments: Dict[str, Any] = None):
        """Send a DAP request."""
        # Check if process is still alive
        if self.process.poll() is not None:
            print("Error: Debug adapter is not running!")
            return

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
        try:
            message_bytes = message.encode('utf-8')
            self.process.stdin.write(message_bytes)
            self.process.stdin.flush()
        except Exception as e:
            print(f"Error sending request: {e}")
            stderr = self.process.stderr.read()
            if stderr:
                print(f"Debug adapter error:\n{stderr}")

    def read_response(self, timeout=10):
        """Read a response from the adapter."""
        import threading

        result = [None]
        exception = [None]

        def read_func():
            try:
                # Read headers
                headers = {}
                while True:
                    line = self.process.stdout.readline().decode('utf-8')
                    if not line or line == "\r\n":
                        break
                    if ":" in line:
                        key, value = line.split(":", 1)
                        headers[key.strip()] = value.strip()

                # Read body
                if "Content-Length" in headers:
                    length = int(headers["Content-Length"])
                    body_bytes = self.process.stdout.read(length)
                    body = body_bytes.decode('utf-8')
                    response = json.loads(body)
                    result[0] = response
            except Exception as e:
                exception[0] = e

        thread = threading.Thread(target=read_func)
        thread.daemon = True
        thread.start()
        thread.join(timeout)

        if thread.is_alive():
            print(f"Timeout: No response within {timeout} seconds")
            # Check stderr for errors
            try:
                stderr = self.process.stderr.read(100)  # Read first 100 chars
                if stderr:
                    print(f"Debug adapter stderr: {stderr}")
            except:
                pass
            return None

        if exception[0]:
            print(f"Error reading response: {exception[0]}")
            return None

        if result[0]:
            print(f"\n← Received: {result[0].get('command', result[0].get('event', 'unknown'))}")
            print(f"  {result[0]}")

        return result[0]

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
            "program": "contracts/flipper.contract",
            "stopOnEntry": True
        })

        response = self.read_response()

    def test_set_breakpoints(self):
        """Test setting breakpoints."""
        print("\n=== Testing Set Breakpoints ===")

        self.send_request("setBreakpoints", {
            "source": {
        "path": "contracts/lib.rs"
        },
        "breakpoints": [
            {"line": 12},  # constructor new
            {"line": 17},  # flip method
            {"line": 22}   # get method
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

            # Read all stderr logs
            if self.process:
                remaining_stderr = self.process.stderr.read()
                if remaining_stderr:
                    print("\n=== Full Debug Adapter Logs ===")
                    print(remaining_stderr.decode('utf-8', errors='replace'))

        finally:
            if self.process:
                self.process.terminate()
                print("\nDebug adapter terminated")


if __name__ == "__main__":
    client = TestDAPClient()
    client.run_tests()