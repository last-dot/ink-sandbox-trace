#!/usr/bin/env python3
"""
Ink! v6 Debug Adapter for VS Code
Main entry point for the debug adapter server
"""

import sys
import logging
from pathlib import Path
import asyncio

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import modules
from adapter.debug_adapter import DebugAdapter
from utils.logger import setup_logger


def main():
    """Main entry point for the debug adapter."""
    # Setup logging
    logger = setup_logger("InkDebugAdapter")
    logger.info("Starting Ink! Debug Adapter...")

    try:
        # Create and run debug adapter
        adapter = DebugAdapter()
        asyncio.run(adapter.run())
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        # Run the main function
        main()
    except KeyboardInterrupt:
        print("\nDebug adapter terminated by user", file=sys.stderr)
        sys.exit(0)