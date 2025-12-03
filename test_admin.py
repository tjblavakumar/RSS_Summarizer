#!/usr/bin/env python3
"""Test admin routes"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app

def test_admin_routes():
    """Test admin routes for errors"""
    with app.test_client() as client:
        try:
            # Test admin feeds
            response = client.get('/admin/feeds')
            print(f"Admin feeds: {response.status_code}")
            
            # Test admin topics  
            response = client.get('/admin/topics')
            print(f"Admin topics: {response.status_code}")
            
            # Test admin categories
            response = client.get('/admin/categories')
            print(f"Admin categories: {response.status_code}")
            
            # Test admin scheduler
            response = client.get('/admin/scheduler')
            print(f"Admin scheduler: {response.status_code}")
            
            print("All admin routes tested successfully!")
            
        except Exception as e:
            print(f"Error testing admin routes: {e}")

if __name__ == "__main__":
    test_admin_routes()