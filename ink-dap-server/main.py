#!/usr/bin/env python3
"""
Ink! v6 Debug Adapter for VS Code
Main entry point for the debug adapter server
With detailed logging to debug_adapter.log file
"""

import sys
import logging
from pathlib import Path
import asyncio
import traceback

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))


def main():
    """Main entry point for the debug adapter."""

    # Setup logging first (will create debug_adapter.log)
    from utils.logger import setup_logger
    logger = setup_logger("InkDebugAdapter")

    logger.info("=" * 60)
    logger.info("🚀 STARTING INK! DEBUG ADAPTER")
    logger.info("=" * 60)
    logger.info(f"📂 Working directory: {Path.cwd()}")
    logger.info(f"🐍 Python version: {sys.version}")
    logger.info(f"📄 Script path: {__file__}")
    logger.info(f"📁 Src path: {src_path}")

    try:
        # Import modules
        logger.info("📦 Importing modules...")
        from adapter.debug_adapter import DebugAdapter
        logger.info("✅ Modules imported successfully")

        # Create adapter
        logger.info("🏗️ Creating DebugAdapter instance...")
        adapter = DebugAdapter()
        logger.info("✅ DebugAdapter created successfully")

        # Check asyncio compatibility
        logger.info("🔄 Checking asyncio compatibility...")

        # For Windows compatibility
        if sys.platform == 'win32':
            logger.info("🪟 Windows detected, setting ProactorEventLoopPolicy")
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

        # Create new event loop
        logger.info("🔁 Creating new event loop...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        logger.info("✅ Event loop created successfully")

        # Run adapter
        logger.info("🎯 Starting debug adapter main loop...")
        loop.run_until_complete(adapter.run())
        logger.info("✅ Debug adapter finished normally")

    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        logger.error(f"📍 Import traceback:\n{traceback.format_exc()}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("⌨️ Debug adapter terminated by user (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        logger.error(f"📍 Full traceback:\n{traceback.format_exc()}")

        # Additional crash log for debugging
        try:
            # Write crash.log to root directory (next to debug_adapter.log)
            crash_log = Path(__file__).parent.parent / "crash.log"
            with open(crash_log, "w", encoding='utf-8') as f:
                f.write(f"CRASH TIMESTAMP: {sys.version}\n")
                f.write(f"ERROR: {e}\n")
                f.write(f"TRACEBACK:\n{traceback.format_exc()}")
            logger.error(f"💾 Crash details saved to: {crash_log}")
        except Exception as crash_error:
            logger.error(f"❌ Could not write crash log: {crash_error}")

        sys.exit(1)
    finally:
        logger.info("🏁 Debug adapter main() function ended")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Last resort error handling
        print(f"CRITICAL ERROR in main: {e}", file=sys.stderr)
        print(f"TRACEBACK: {traceback.format_exc()}", file=sys.stderr)
        sys.exit(1)