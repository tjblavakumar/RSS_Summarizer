#!/usr/bin/env python3
"""Test script to verify scheduler functionality"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scheduler import RSSScheduler
import pytz
from datetime import datetime

def test_scheduler():
    print("Testing RSS Scheduler functionality...")
    
    # Create scheduler instance
    scheduler = RSSScheduler()
    
    # Schedule for 4 AM PT
    scheduler.schedule_daily(hour=4, minute=0)
    
    # Start scheduler
    scheduler.start()
    
    # Get next run time
    next_run = scheduler.get_next_run_time()
    
    print(f"Scheduler Status: {'Running' if scheduler.is_running else 'Stopped'}")
    print(f"Next Run Time: {next_run}")
    
    # Convert to PT for display
    if next_run:
        pt_tz = pytz.timezone('US/Pacific')
        next_run_pt = next_run.astimezone(pt_tz)
        print(f"Next Run Time (PT): {next_run_pt.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    print(f"Current Time (PT): {datetime.now(pt_tz).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    # Stop scheduler
    scheduler.stop()
    print("Test completed successfully!")

if __name__ == "__main__":
    test_scheduler()