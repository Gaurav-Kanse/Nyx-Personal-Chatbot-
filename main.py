#!/usr/bin/env python3
import sys
from ui.window import NyxUI
from core.config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)

def main():
    logger.info("=== Nyx Starting ===")

    try:
        app  = NyxUI(user_name="Gaurav")
        logger.info("UI initialized successfully")
        app.run()

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
