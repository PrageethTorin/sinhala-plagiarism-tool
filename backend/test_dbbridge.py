#!/usr/bin/env python3
"""
Test script to verify DBBridge functionality
"""
import sys
import os

# Add the correct path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "modules", "WSA"))

print("=" * 60)
print("TESTING DB BRIDGE FUNCTIONALITY")
print("=" * 60)

try:
    from db_bridge import DBBridge
    print("✅ Successfully imported DBBridge")
    
    # Create instance
    db = DBBridge()
    print("✅ Successfully instantiated DBBridge")
    
    # Check if methods exist
    if hasattr(db, 'get_all_previous_submissions'):
        print("✅ Method 'get_all_previous_submissions' EXISTS")
    else:
        print("❌ Method 'get_all_previous_submissions' NOT FOUND")
        
    if hasattr(db, 'save_new_submission'):
        print("✅ Method 'save_new_submission' EXISTS")
    else:
        print("❌ Method 'save_new_submission' NOT FOUND")
    
    if hasattr(db, 'connect'):
        print("✅ Method 'connect' EXISTS")
    else:
        print("❌ Method 'connect' NOT FOUND")
    
    if hasattr(db, 'init_db'):
        print("✅ Method 'init_db' EXISTS")
    else:
        print("❌ Method 'init_db' NOT FOUND")
    
    # List all methods
    print("\n--- All available methods in DBBridge ---")
    methods = [m for m in dir(db) if not m.startswith('_')]
    for method in methods:
        print(f"  - {method}")
    
    print("\n✅ ALL CHECKS PASSED!")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
