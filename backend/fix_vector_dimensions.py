#!/usr/bin/env python3
"""
Simple database cleanup - removes old incompatible vectors
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "modules", "WSA"))

from modules.WSA.db_bridge import DBBridge

def clear_old_vectors():
    """Clear old 768-dim vectors to match current 1391-dim vectorizer"""
    db = DBBridge()
    
    print("\n" + "=" * 70)
    print("CLEARING OLD VECTORS")
    print("=" * 70)
    
    try:
        conn = db.connect()
        if not conn:
            print("❌ Could not connect to database")
            return False
        
        cursor = conn.cursor()
        
        # Get count before
        cursor.execute("SELECT COUNT(*) FROM student_submissions")
        before = cursor.fetchone()[0]
        print(f"\n📊 Before: {before} vectors in database")
        
        # Delete all
        cursor.execute("DELETE FROM student_submissions")
        conn.commit()
        
        # Get count after
        cursor.execute("SELECT COUNT(*) FROM student_submissions")
        after = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        print(f"📊 After: {after} vectors in database")
        print(f"\n✅ Removed {before - after} old {768}-dimensional vectors")
        print(f"✅ System is now ready for new vectors ({1391}-dimensional)")
        print("\n🎯 New submissions will be stored correctly going forward.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n🔧 Sinhala Plagiarism Tool - Vector Dimension Resolver\n")
    print("Issue: Database has 768-dim vectors, but vectorizer uses 1391-dim")
    print("Solution: Clear old vectors to match current vectorizer\n")
    
    confirm = input("Continue with cleanup? (yes/no): ").strip().lower()
    
    if confirm in ['yes', 'y']:
        if clear_old_vectors():
            print("\n" + "=" * 70)
            print("✅ READY TO USE")
            print("=" * 70)
            print("\nThe plagiarism detection tool is now operational.")
            print("Dimension mismatch errors should be resolved.")
    else:
        print("✅ No changes made")
        print("\n⚠️ If you want the error to go away, run this script again.")
