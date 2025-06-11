"""
Clipboard Image Capture Application

This is the main entry point for the Clipboard Image Capture application.
It sets up and runs the main application window.
"""

import os
import sys
from app import ClipboardImageApp


def main():
    """Main function to initialize and run the application"""
    # Ensure we're in the correct working directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Start the application
    app = ClipboardImageApp()
    app.mainloop()


if __name__ == "__main__":
    main()
