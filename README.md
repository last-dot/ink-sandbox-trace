# ink-sandbox-trace
Debugger for smart contracts for ink!

---

## Project overview :page_facing_up:

### Overview

- **Tagline**: An IDE-integrated step-debugger for Ink! v6 smart contracts using the Debug Adapter Protocol (DAP)
- **Brief description**: Developer tool that enables step-by-step debugging of Ink! v6 smart contracts directly inside VS Code, using a custom Debug Adapter built for PolkaVM and pallet-revive. This allows developers to set breakpoints, step through execution, and inspect state—without running a node.

---

### Project details

1. **Core functionality & data flow**
    1. **Data models / API specs**:
        - Uses the **tracing APIs** of `pallet-revive` and **PolkaVM debug symbols** to observe execution and pause at breakpoints.
        - Executes contracts in an **off-chain sandbox** (DRink! or similar) without requiring a full node.
        - Implements the **Debug Adapter Protocol (DAP)** to connect with VS Code or other IDEs.
    2. **Architecture overview**:
        - **VS Code Extension**: Minimal shell for launching debug sessions via launch.json.
        - **Rust-based Debug Adapter**: Bridges VS Code and the PolkaVM sandbox, managing execution and state.
        - **Ink! execution backend**: Uses DRink! with PolkaVM interpreter mode.
2. **Technology stack**:
    - **DAP**: Debug Adapter Protocol (JSON over stdio)
    - **Rust**: For the adapter and runtime integration
    - **VS Code**: For UI
    - **PolkaVM + pallet-revive**: Target execution engine
    - **Ink! v6**: Target contract language

> - We do not support old Ink! versions or Substrate Wasm contracts. This is strictly for Ink! v6 and pallet-revive.

---

## Development roadmap :nut_and_bolt:

### Overview

### Month 1 — Design and Prototype Execution Engine

- Research DRink!, PolkaVM, and tracing APIs. Set up sandbox execution. Define core architecture of the adapter.

| **Number** | **Deliverable** | **Specification** |
| --- | --- | --- |
| **1.** | License | Publish code under **MIT** license |
| **2.** | Docs | Document architecture, sandbox setup, debugging process |
| **3.** | Adapter prototype | Can launch debug session and execute a contract to completion |
| **4.** | Breakpoint architecture | Implement file:line -> instruction address mapping, planning for future |
| **5.** | Contract run | DRink!-based or custom PolkaVM sandbox for isolated execution |

---

### Month 2 — Implement Breakpoints, Stepping, and State Inspection

- Implement debug session lifecycle, stepping, call stack tracking, and state inspection logic.

| **Number** | **Deliverable** | **Specification** |
| --- | --- | --- |
| **6.** | Breakpoint hit | Stop execution at breakpoint, notify DAP client |
| **7.** | Step execution | Support step over, into, out with temporary breakpoints or trace tracking |
| **8.** | Call stack | Show function call hierarchy from CallTrace or PolkaVM stack info |
| **9.** | Variable scope | Basic contract storage and function params inspection |
| **10.** | Integration tests | Contracts for test cases: breakpoints, stepping, nested calls |

---

### Month 3 — VS Code Integration, Stability, and Documentation

- Finalize extension packaging, cross-platform polish, and write usage guide.

| **Number** | **Deliverable** | **Specification** |
| --- | --- | --- |
| **11.** | VS Code extension | Publish a usable debugger integrated with DAP client in VS Code |
| **12.** | Debug session UX | Launch.json templates, smooth F5 experience, readable variables |
| **13.** | Variable pretty-printers | Format common types like Balance, AccountId nicely |
| **14.** | Usage guide | Step-by-step doc with screenshots and limitations |
| **15.** | Final demo | Showcase contract with working debugger, recorded or live |

---

## Future Plans

Once MVP is complete, future phases may include:

1. **Advanced variable inspection**: DWARF parsing to show local vars
2. **Expression evaluation & watch**: REPL and dynamic watches
3. **Conditional breakpoints**: Pause when variables match conditions
4. **Custom GUI**: Interactive visualization of state, execution flow
5. **Replay on-chain transactions**: Load historical traces and replay
6. **Multi-contract debugging**: Cross-contract call tracking and stepping
7. **Attach to node (future)**: RPC-based tracing from actual chain
8. **Broad editor support**: JetBrains, Emacs, etc. via DAP
9. **Community feedback loop**: Feature voting and community engagement
