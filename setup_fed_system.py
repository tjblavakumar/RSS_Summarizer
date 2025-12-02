#!/usr/bin/env python3
"""Complete setup script for Federal Reserve RSS Summary System"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from migrate_db import migrate_database
from init_categories import init_default_categories
from init_feeds import init_default_feeds

def main():
    """Complete system setup"""
    print("=== Federal Reserve RSS Summary System Setup ===\n")
    
    print("1. Migrating database schema...")
    migrate_database()
    
    print("\n2. Initializing categories and topics...")
    init_default_categories()
    
    print("\n3. Initializing RSS feeds...")
    init_default_feeds()
    
    print("\n=== Setup Complete! ===")
    print("\nYour system is now configured with:")
    print("• 7 Federal Reserve focused categories")
    print("• 7 topics with comprehensive keyword mapping")
    print("• 8 financial news RSS feeds")
    print("\nNext steps:")
    print("1. Run: python app.py")
    print("2. Visit: http://localhost:5000")
    print("3. Click 'Refresh News' to start processing")
    print("4. Scheduler will run daily at 4:00 AM PT")

if __name__ == "__main__":
    main()