"""
Debug Adapter Protocol implementation for Ink! v6
Handles communication between VS Code and the Rust debugger
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

    async def run(self):
        """Main loop for the debug adapter - async version."""
        self.is_running = True
        self.logger.info("Debug adapter started, waiting for DAP messages...")

        # Запускаем чтение в отдельной задаче
        await self._read_loop()

    async def _read_loop(self):
        """Async loop for reading DAP messages."""
        loop = asyncio.get_event_loop()

        while self.is_running:
            try:
                # Читаем синхронно в executor
                message = await loop.run_in_executor(None, self.protocol.read_message)
                if message:
                    await self._handle_message(message)
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
            "disconnect": self._handle_disconnect,
        }

        handler = handlers.get(command)
        if handler:
            try:
               await handler(request)
            except Exception as e:
                self.logger.error(f"Error handling {command}: {e}", exc_info=True)
                self.protocol.send_response(request, success=False)
        else:
            self.logger.warning(f"Unknown command: {command}")
            self.protocol.send_response(request, success=False)

    async def _handle_initialize(self, request: Dict[str, Any]):
        """Handle 'initialize' request."""
        self.logger.info("Initializing debug adapter")

        # Send capabilities
        self.protocol.send_response(request, body=self.capabilities)

        # Mark as initialized
        self.is_initialized = True

        # Send initialized event
        self.protocol.send_event("initialized")

    async def _handle_launch(self, request: Dict[str, Any]):
        """Handle 'launch' request."""
        args = request.get("arguments", {})

        # Get contract path
        program = args.get("program")
        if not program:
            self.logger.error("No program specified in launch request")
            self.protocol.send_response(request, success=False)
            return

        self.logger.info(f"Launching debugger for: {program}")

        # Инициализируем мост к Rust
        self.rust_bridge = RustBridge()
        try:
            await self.rust_bridge.start()

            # Инициализируем с путем к контракту
            result = await self.rust_bridge.call_method("initialize", {
                "path": program
            })
            self.logger.info(f"Rust инициализирован: {result}")
        except Exception as e:
            self.logger.error(f"Ошибка подключения к Rust: {e}")
            self.protocol.send_response(request, success=False)
            return

        self.protocol.send_response(request)
        self.stop_on_entry = args.get("stopOnEntry", False)






    async def _handle_set_breakpoints(self, request: Dict[str, Any]):
        """Handle 'setBreakpoints' request."""
        args = request.get("arguments", {})
        source = args.get("source", {})
        source_path = source.get("path", "")
        breakpoints = args.get("breakpoints", [])

        self.logger.info(f"Setting {len(breakpoints)} breakpoints in {source_path}")


        # Store breakpoints
        self.breakpoints[source_path] = breakpoints

        # Отправляем breakpoints в Rust (пока с фейковыми адресами)
        if self.rust_bridge:
            addresses = [0x1000 * (i + 1) for i, bp in enumerate(breakpoints)]
            try:
                result = await self.rust_bridge.call_method("setBreakpoints", {
                    "addresses": addresses
                })
                self.logger.info(f"Rust breakpoints: {result}")
            except Exception as e:
                self.logger.error(f"Ошибка установки breakpoints: {e}")

        # TODO: Map line numbers to instruction addresses using source_mapper
        # For now, just acknowledge all breakpoints as verified
        verified_breakpoints = []
        for i, bp in enumerate(breakpoints):
            line = bp.get("line")
            # Try to map line to address
            address = None

            verified_breakpoints.append({
                "id": i + 1,
                "verified": True,
                "line": line
            })


        self.logger.info(f"Verified breakpoints: {verified_breakpoints}")

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
            self.protocol.send_event("stopped", {
                "reason": "entry",
                "threadId": self.current_thread_id,
                "allThreadsStopped": True
            })

        # TODO: Start execution if not stopOnEntry

    async def _handle_threads(self, request: Dict[str, Any]):
        """Handle 'threads' request."""
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

        # TODO: Get actual stack trace from Rust
        # For now, return empty stack
        self.protocol.send_response(request, body={
            "stackFrames": [],
            "totalFrames": 0
        })

    async def _handle_scopes(self, request: Dict[str, Any]):
        """Handle 'scopes' request."""
        # TODO: Get actual scopes from Rust
        self.protocol.send_response(request, body={
            "scopes": []
        })

    async def _handle_variables(self, request: Dict[str, Any]):
        """Handle 'variables' request."""
        # TODO: Get actual variables from Rust
        self.protocol.send_response(request, body={
            "variables": []
        })

    async def _handle_continue(self, request: Dict[str, Any]):
        """Handle 'continue' request."""
        self.logger.info("Continuing execution")
        if self.rust_bridge:
            try:
                await self.rust_bridge.call_method("continue", {})
            except Exception as e:
                self.logger.error(f"Ошибка continue: {e}")

        self.protocol.send_response(request, body={
            "allThreadsContinued": True
        })

    async def _handle_next(self, request: Dict[str, Any]):
        """Handle 'next' (step over) request."""
        self.logger.info("Step over")
        if self.rust_bridge:
            try:
                await self.rust_bridge.call_method("next", {})
            except Exception as e:
                self.logger.error(f"Ошибка next: {e}")
        self.protocol.send_response(request)

    async def _handle_step_in(self, request: Dict[str, Any]):
        """Handle 'stepIn' request."""
        self.logger.info("Step in")
        if self.rust_bridge:
            try:
                await self.rust_bridge.call_method("stepIn", {})
            except Exception as e:
                self.logger.error(f"Ошибка stepIn: {e}")
        self.protocol.send_response(request)

    async def _handle_step_out(self, request: Dict[str, Any]):
        """Handle 'stepOut' request."""
        self.logger.info("Step out")
        if self.rust_bridge:
            try:
                await self.rust_bridge.call_method("stepOut", {})
            except Exception as e:
                self.logger.error(f"Ошибка stepOut: {e}")
        self.protocol.send_response(request)

    async def _handle_pause(self, request: Dict[str, Any]):
        """Handle 'pause' request."""
        self.logger.info("Pausing execution")
        if self.rust_bridge:
            try:
                await self.rust_bridge.call_method("pause", {})
            except Exception as e:
                self.logger.error(f"Ошибка pause: {e}")
        self.protocol.send_response(request)

    async def _handle_disconnect(self, request: Dict[str, Any]):
        """Handle 'disconnect' request."""
        if self.rust_bridge:
            try:
                await self.rust_bridge.call_method("disconnect", {})
            except Exception as e:
                self.logger.error(f"Ошибка disconnect: {e}")
        self.logger.info("Disconnecting debugger")
        self.protocol.send_response(request)
        self.stop()

    def stop(self):
        """Stop the debug adapter."""
        self.is_running = False
        self.logger.info("Debug adapter stopped")