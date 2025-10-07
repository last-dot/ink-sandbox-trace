"""
Debug Adapter Protocol implementation for Ink! v6
Handles communication between VS Code and the Rust debugger
With enhanced logging and error handling
"""

import sys
import json
import logging
import threading
from typing import Dict, Any, Optional
from .dap_protocol import DAPProtocol
import time
import asyncio
from bridge.rust_bridge import RustBridge


class DebugAdapter:
    """Main debug adapter class implementing DAP protocol."""

    def __init__(self):
        self.logger = logging.getLogger("InkDebugAdapter.Adapter")
        self.protocol = DAPProtocol()
        self.is_running = False
        self.rust_bridge = None

        # Track debug state
        self.is_initialized = False
        self.is_configured = False
        self.breakpoints = {}
        self.current_thread_id = 1

        # DAP capabilities
        self.capabilities = {
            "supportsConfigurationDoneRequest": True,
            "supportsFunctionBreakpoints": False,
            "supportsConditionalBreakpoints": False,
            "supportsEvaluateForHovers": True,
            "supportsStepBack": False,
            "supportsSetVariable": False,
            "supportsRestartFrame": False,
            "supportsStepInTargetsRequest": False,
            "supportsGotoTargetsRequest": False,
            "supportsCompletionsRequest": False,
            "supportsRestartRequest": False,
            "supportsExceptionOptions": False,
            "supportsValueFormattingOptions": True,
            "supportsExceptionInfoRequest": False,
            "supportTerminateDebuggee": True,
            "supportsDelayedStackTraceLoading": False,
            "supportsLoadedSourcesRequest": False,
            "supportsLogPoints": False,
            "supportsTerminateThreadsRequest": False,
            "supportsSetExpression": False,
            "supportsTerminateRequest": True,
            "supportsDataBreakpoints": False,
            "supportsReadMemoryRequest": False,
            "supportsDisassembleRequest": False,
            "supportsCancelRequest": False,
            "supportsBreakpointLocationsRequest": False,
        }

        self.logger.info("Debug adapter initialized")

    def log_to_console(self, message: str, level: str = "INFO"):
        """Send log message to VS Code Debug Console."""
        formatted_msg = f"[{level}] {message}"
        self.protocol.send_output(formatted_msg, category="console")
        # Также пишем в файл
        if level == "ERROR":
            self.logger.error(message)
        elif level == "WARNING":
            self.logger.warning(message)
        else:
            self.logger.info(message)


    async def run(self):
        """Main loop for the debug adapter - async version."""
        self.is_running = True
        self.logger.info("Debug adapter started, waiting for DAP messages...")
        self.log_to_console("Debug adapter started, waiting for DAP messages...")

        # Start reading in separate task
        await self._read_loop()

    async def _read_loop(self):
        """Async loop for reading DAP messages."""
        loop = asyncio.get_event_loop()

        while self.is_running:
            try:
                self.logger.debug("Waiting for DAP message...")
                # Read synchronously in executor
                message = await loop.run_in_executor(None, self.protocol.read_message)
                if message:
                    self.logger.info(f"Received DAP message: {message.get('command', 'unknown')}")
                    self.log_to_console(f"Received DAP message: {message.get('command', 'unknown')}")
                    await self._handle_message(message)
                else:
                    self.logger.debug("No message received, continuing...")
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}", exc_info=True)

    async def _handle_message(self, message: Dict[str, Any]):
        """Handle a DAP message."""
        msg_type = message.get("type")

        if msg_type == "request":
            await self._handle_request(message)
        else:
            self.logger.warning(f"Unknown message type: {msg_type}")

    async def _handle_request(self, request: Dict[str, Any]):
        """Handle a DAP request."""
        command = request.get("command")
        seq = request.get("seq", 0)

        self.logger.info(f"Handling request #{seq}: {command}")

        # Route to appropriate handler
        handlers = {
            "initialize": self._handle_initialize,
            "launch": self._handle_launch,
            "setBreakpoints": self._handle_set_breakpoints,
            "configurationDone": self._handle_configuration_done,
            "threads": self._handle_threads,
            "stackTrace": self._handle_stack_trace,
            "scopes": self._handle_scopes,
            "variables": self._handle_variables,
            "continue": self._handle_continue,
            "next": self._handle_next,
            "stepIn": self._handle_step_in,
            "stepOut": self._handle_step_out,
            "pause": self._handle_pause,
            "terminate": self._handle_terminate,
            "disconnect": self._handle_disconnect,
        }

        handler = handlers.get(command)
        if handler:
            try:
                await handler(request)
                self.logger.info(f"Successfully handled {command}")
            except Exception as e:
                self.logger.error(f"Error handling {command}: {e}", exc_info=True)
                self.protocol.send_response(request, success=False)
        else:
            self.logger.warning(f"Unknown command: {command}")
            self.protocol.send_response(request, success=False)

    async def _handle_initialize(self, request: Dict[str, Any]):
        """Handle 'initialize' request."""
        self.logger.info("Initializing debug adapter...")
        self.log_to_console("Initializing debug adapter...")

        try:
            # Send capabilities
            self.logger.info("Sending capabilities to VS Code...")
            self.protocol.send_response(request, body=self.capabilities)
            self.logger.info("Capabilities sent successfully")
            self.log_to_console("Capabilities sent successfully")

            # Mark as initialized
            self.is_initialized = True
            self.logger.info("Debug adapter marked as initialized")

            # Send initialized event
            self.logger.info("Sending 'initialized' event to VS Code...")
            self.protocol.send_event("initialized")
            self.logger.info("'Initialized' event sent successfully")
            self.log_to_console("'Initialized' event sent successfully")

        except Exception as e:
            self.logger.error(f"Error in initialize: {e}", exc_info=True)
            raise

    async def _handle_launch(self, request: Dict[str, Any]):
        """Handle 'launch' request."""
        args = request.get("arguments", {})
        self.logger.info(f"Launch request with args: {args}")

        # Get contract path
        program = args.get("program")
        if not program:
            self.logger.error("No program specified in launch request")
            self.protocol.send_response(request, success=False)
            return

        self.logger.info(f"Launching debugger for contract: {program}")
        self.log_to_console(f"Launching debugger for contract: {program}")

        # Initialize Rust bridge
        self.logger.info("Initializing Rust bridge...")
        self.rust_bridge = RustBridge()

        try:
            self.logger.info("Starting Rust bridge connection...")
            await self.rust_bridge.start()

            # Initialize with contract path
            self.logger.info(f"Sending initialize to Rust with program: {program}")
            result = await self.rust_bridge.call_method("initialize", {
                "path": program
            })
            self.logger.info(f"Rust initialized successfully: {result}")

        except Exception as e:
            self.logger.warning(f"Rust bridge connection failed (continuing work): {e}")
            # Don't interrupt DAP server work if Rust is unavailable

        self.protocol.send_response(request)
        self.stop_on_entry = args.get("stopOnEntry", False)
        self.logger.info(f"Launch completed, stopOnEntry: {self.stop_on_entry}")
        self.log_to_console("Launch completed")

    async def _handle_set_breakpoints(self, request: Dict[str, Any]):
        """Handle 'setBreakpoints' request."""
        args = request.get("arguments", {})
        source = args.get("source", {})
        source_path = source.get("path", "")
        breakpoints = args.get("breakpoints", [])

        self.logger.info(f"Setting {len(breakpoints)} breakpoints in {source_path}")
        for i, bp in enumerate(breakpoints):
            self.logger.info(f"   Breakpoint {i+1}: line {bp.get('line')}")

        # Store breakpoints
        self.breakpoints[source_path] = breakpoints

        # Send breakpoints to Rust (with fake addresses for now)
        if self.rust_bridge:
            addresses = [0x1000 * (i + 1) for i, bp in enumerate(breakpoints)]
            self.logger.info(f"Sending breakpoints to Rust: {addresses}")
            try:
                result = await self.rust_bridge.call_method("setBreakpoints", {
                    "addresses": addresses
                })
                self.logger.info(f"Rust accepted breakpoints: {result}")
            except Exception as e:
                self.logger.warning(f"Error sending breakpoints to Rust: {e}")
        else:
            self.logger.warning("Rust bridge not available, breakpoints stored locally only")

        # Acknowledge all breakpoints as verified
        verified_breakpoints = []
        for i, bp in enumerate(breakpoints):
            line = bp.get("line")
            verified_breakpoints.append({
                "id": i + 1,
                "verified": True,
                "line": line
            })

        self.logger.info(f"Verified {len(verified_breakpoints)} breakpoints")

        self.protocol.send_response(request, body={
            "breakpoints": verified_breakpoints
        })

    async def _handle_configuration_done(self, request: Dict[str, Any]):
        """Handle 'configurationDone' request."""
        self.logger.info("Configuration done")
        self.is_configured = True
        self.protocol.send_response(request)

        # Start execution or stop on entry
        if hasattr(self, 'stop_on_entry') and self.stop_on_entry:
            self.logger.info("Stopping on entry")
            self.protocol.send_event("stopped", {
                "reason": "entry",
                "threadId": self.current_thread_id,
                "allThreadsStopped": True
            })
        else:
            self.logger.info("Starting execution without stopping")

    async def _handle_threads(self, request: Dict[str, Any]):
        """Handle 'threads' request."""
        self.logger.info("Returning thread information")
        # Ink! contracts are single-threaded
        self.protocol.send_response(request, body={
            "threads": [
                {"id": self.current_thread_id, "name": "Contract Main Thread"}
            ]
        })

    async def _handle_stack_trace(self, request: Dict[str, Any]):
        """Handle 'stackTrace' request."""
        args = request.get("arguments", {})
        thread_id = args.get("threadId", 1)
        self.logger.info(f"Getting stack trace for thread {thread_id}")

        # TODO: Get actual stack trace from Rust
        self.logger.info("Returning empty stack trace (not implemented)")
        self.protocol.send_response(request, body={
            "stackFrames": [],
            "totalFrames": 0
        })

    async def _handle_scopes(self, request: Dict[str, Any]):
        """Handle 'scopes' request."""
        self.logger.info("Getting variable scopes")
        self.protocol.send_response(request, body={
            "scopes": []
        })

    async def _handle_variables(self, request: Dict[str, Any]):
        """Handle 'variables' request."""
        self.logger.info("Getting variables")
        self.protocol.send_response(request, body={
            "variables": []
        })

    async def _handle_continue(self, request: Dict[str, Any]):
        """Handle 'continue' request."""
        self.logger.info("Continue execution")
        if self.rust_bridge:
            try:
                await self.rust_bridge.call_method("continue", {})
                self.logger.info("Continue sent to Rust")
            except Exception as e:
                self.logger.warning(f"Error sending continue to Rust: {e}")
        else:
            self.logger.warning("Rust bridge not available")

        self.protocol.send_response(request, body={
            "allThreadsContinued": True
        })

    async def _handle_next(self, request: Dict[str, Any]):
        """Handle 'next' (step over) request."""
        self.logger.info("Step over")
        if self.rust_bridge:
            try:
                await self.rust_bridge.call_method("next", {})
                self.logger.info("Step over sent to Rust")
            except Exception as e:
                self.logger.warning(f"Error sending step over to Rust: {e}")
        self.protocol.send_response(request)

    async def _handle_step_in(self, request: Dict[str, Any]):
        """Handle 'stepIn' request."""
        self.logger.info("Step in")
        if self.rust_bridge:
            try:
                await self.rust_bridge.call_method("stepIn", {})
                self.logger.info("Step in sent to Rust")
            except Exception as e:
                self.logger.warning(f"Error sending step in to Rust: {e}")
        self.protocol.send_response(request)

    async def _handle_step_out(self, request: Dict[str, Any]):
        """Handle 'stepOut' request."""
        self.logger.info("Step out")
        if self.rust_bridge:
            try:
                await self.rust_bridge.call_method("stepOut", {})
                self.logger.info("Step out sent to Rust")
            except Exception as e:
                self.logger.warning(f"Error sending step out to Rust: {e}")
        self.protocol.send_response(request)

    async def _handle_pause(self, request: Dict[str, Any]):
        """Handle 'pause' request."""
        self.logger.info("Pause execution")
        if self.rust_bridge:
            try:
                await self.rust_bridge.call_method("pause", {})
                self.logger.info("Pause sent to Rust")
            except Exception as e:
                self.logger.warning(f"Error sending pause to Rust: {e}")
        self.protocol.send_response(request)

    async def _handle_terminate(self, request: Dict[str, Any]):
        """Handle 'terminate' request."""
        self.logger.info("Terminating debuggee...")

        if self.rust_bridge:
            try:
                # Tell Rust to terminate the contract execution
                await self.rust_bridge.call_method("terminate", {})
                self.logger.info("Terminate sent to Rust")
            except Exception as e:
                self.logger.warning(f"Error sending terminate to Rust: {e}")

        self.protocol.send_response(request)

        # VS Code expects a 'terminated' event after successful termination
        self.protocol.send_event("terminated")
        self.logger.info("Sent 'terminated' event to VS Code")

    async def _handle_disconnect(self, request: Dict[str, Any]):
        """Handle 'disconnect' request."""
        self.logger.info("Disconnecting debugger...")

        if self.rust_bridge:
            try:
                await self.rust_bridge.call_method("disconnect", {})
                await self.rust_bridge.shutdown()
                self.logger.info("Disconnected from Rust")
            except Exception as e:
                self.logger.warning(f"Error disconnecting from Rust: {e}")

        self.protocol.send_response(request)
        self.stop()

    def stop(self):
        """Stop the debug adapter."""
        self.is_running = False
        self.logger.info("Debug adapter stopped")

