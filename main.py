#!/usr/bin/env python3
import customtkinter as ctk
import sys
from ui.window import NyxUI
from core.config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)

def main():
    logger.info("=== Nyx Starting ===")

    try:
        root = ctk.CTk()
        app = NyxUI(root)
        logger.info("UI initialized successfully")

        app.add_message("Nyx", "Welcome to Nyx! I'm your local AI assistant.\n\nWhat can I help you with?")

        app.run()

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
