"""
Debug Adapter Protocol (DAP) implementation
Handles low-level DAP message reading and writing
"""

import json
import sys
import os
from typing import Dict, Any, Optional
import logging


class DAPProtocol:
    """Handles DAP message encoding/decoding over stdin/stdout."""

    def __init__(self):
        self.logger = logging.getLogger("InkDebugAdapter.DAPProtocol")
        self._sequence = 1

        # Set stdin to non-blocking mode on Windows
        if sys.platform == 'win32':
            import msvcrt
            msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
            msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)

    def read_message(self) -> Optional[Dict[str, Any]]:
        """
        Read a DAP message from stdin.

        DAP messages format:
        Content-Length: <length>\r\n
        \r\n
        <json-content>
        """
        try:
            # Read headers byte by byte until we find \r\n\r\n
            headers_bytes = b''
            while True:
                byte = sys.stdin.buffer.read(1)
                if not byte:
                    return None
                headers_bytes += byte
                if headers_bytes.endswith(b'\r\n\r\n'):
                    break

            # Parse headers
            headers_str = headers_bytes[:-4].decode('utf-8')  # Remove \r\n\r\n
            headers = {}
            for line in headers_str.split('\r\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip()] = value.strip()

            # Get content length
            if 'Content-Length' not in headers:
                self.logger.error("No Content-Length header found")
                return None

            content_length = int(headers['Content-Length'])

            # Read exact number of bytes for body
            body_bytes = b''
            while len(body_bytes) < content_length:
                chunk = sys.stdin.buffer.read(content_length - len(body_bytes))
                if not chunk:
                    break
                body_bytes += chunk

            if len(body_bytes) < content_length:
                self.logger.error(f"Expected {content_length} bytes, got {len(body_bytes)}")
                return None

            # Parse JSON
            body_str = body_bytes.decode('utf-8')
            message = json.loads(body_str)
            self.logger.debug(f"Received: {message}")
            return message

        except Exception as e:
            self.logger.error(f"Error reading message: {e}", exc_info=True)
            return None

    def send_message(self, message: Dict[str, Any]):
        """Send a DAP message to stdout."""
        try:
            # Convert to JSON
            body = json.dumps(message, separators=(',', ':'))
            body_bytes = body.encode('utf-8')

            # Create header
            header = f"Content-Length: {len(body_bytes)}\r\n\r\n"
            header_bytes = header.encode('ascii')

            # Write header and body
            sys.stdout.buffer.write(header_bytes)
            sys.stdout.buffer.write(body_bytes)
            sys.stdout.buffer.flush()

            self.logger.debug(f"Sent: {message}")

        except Exception as e:
            self.logger.error(f"Error sending message: {e}", exc_info=True)

    def send_response(self, request: Dict[str, Any], body: Optional[Dict[str, Any]] = None, success: bool = True):
        """Send a response to a DAP request."""
        response = {
            "seq": self._next_seq(),
            "type": "response",
            "request_seq": request.get("seq", 0),
            "success": success,
            "command": request.get("command", "")
        }

        if body is not None:
            response["body"] = body

        if not success and body is None:
            response["body"] = {}

        self.send_message(response)

    def send_event(self, event: str, body: Optional[Dict[str, Any]] = None):
        """Send a DAP event."""
        message = {
            "seq": self._next_seq(),
            "type": "event",
            "event": event
        }

        if body is not None:
            message["body"] = body

        self.send_message(message)

    def send_output(self, text: str, category: str = "console"):
            """Send output to VS Code Debug Console via DAP output event."""
            if not text.endswith('\n'):
                text += '\n'

            self.send_event("output", {
                "category": category,
                "output": text
            })

    def _next_seq(self) -> int:
        """Get next sequence number."""
        seq = self._sequence
        self._sequence += 1
        return seq