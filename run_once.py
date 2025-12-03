#!/usr/bin/env python3
"""Run RSS summary once immediately"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scheduler import rss_scheduler

def main():
    print("Running RSS summary once (immediate execution)...")
    rss_scheduler.run_once_now()
    print("RSS summary execution completed!")

if __name__ == "__main__":
    main()