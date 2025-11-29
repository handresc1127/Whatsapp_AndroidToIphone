"""
WhatsApp Android to iOS Migration Tool - Launcher

This is a compatibility launcher that redirects to the new modular structure.
The actual implementation is in src/main.py

Usage:
    python main.py
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
    # Import and run the real main from src/
    from src.main import main
    sys.exit(main() or 0)
