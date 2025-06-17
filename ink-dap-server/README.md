Ink! v6 Debug Adapter
Step-by-step debugger for Ink! v6 smart contracts, implementing the Debug Adapter Protocol (DAP) for VS Code integration.
Overview
This Python server acts as a bridge between:

VS Code Debug UI (via DAP protocol)
Rust-based PolkaVM execution environment

Architecture
VS Code <--(DAP)--> Python Server <--(JSON-RPC)--> Rust Debugger
Development Setup

Install dependencies:

bashpip install -r requirements.txt

Run the debug adapter:

bashpython main.py
Project Structure
ink-debugger-python/
├── src/
│   ├── adapter/      # DAP protocol implementation
│   ├── bridge/       # Communication with Rust process
│   ├── mapping/      # Source code to instruction mapping
│   └── utils/        # Logging and helpers
├── tests/            # Unit tests
├── docs/             # Documentation
└── main.py           # Entry point
Tasks

 Init basic Python debug framework
 Implement start of Sandbox/Debugger
 Implement DAP handshake with VSCode extension
 Implement line-intruction mapping
 Implement contract execution via Sandbox/Debugger

Team

Python Server: Mark
Rust Backend: Maliketh
VS Code Extension: TBD