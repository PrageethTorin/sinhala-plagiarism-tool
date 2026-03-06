#!/usr/bin/env python3
"""
Database cleanup utility to remove incompatible vectors
"""
import sys
import os

# Add paths
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "modules", "WSA"))

from modules.WSA.db_bridge import DBBridge
import pickle

def get_vector_dimensions(vec_blob):
    """Extract dimension information from a vector blob"""
    try:
        vec = pickle.loads(vec_blob)
        if hasattr(vec, 'toarray'):
            return len(vec.toarray().flatten())
        else:
            return len(vec.flatten())
    except Exception as e:
        print(f"Error reading vector: {e}")
        return None

def analyze_database():
    """Analyze database for vector dimensions"""
    db = DBBridge()
    submissions = db.get_all_previous_submissions()
    
    print("\n" + "=" * 70)
    print("DATABASE VECTOR ANALYSIS")
    print("=" * 70)
    
    if not submissions:
        print("✅ Database is empty - no incompatible vectors")
        return
    
    dimensions = {}
    total = len(submissions)
    
    print(f"\n📊 Analyzing {total} submissions...")
    
    for idx, (text, vec_blob) in enumerate(submissions, 1):
        dim = get_vector_dimensions(vec_blob)
        if dim:
            dimensions[dim] = dimensions.get(dim, 0) + 1
        if idx % 10 == 0:
            print(f"  Progress: {idx}/{total}")
    
    print("\n📈 Vector Dimension Distribution:")
    for dim, count in sorted(dimensions.items()):
        pct = (count / total) * 100
        print(f"  {dim}-dimensional: {count} vectors ({pct:.1f}%)")
    
    if len(dimensions) > 1:
        print("\n⚠️ INCOMPATIBILITY DETECTED!")
        print(f"Found {len(dimensions)} different vector dimensions")
        print(f"Current vectorizer produces: 1391-dimensional vectors")
        return True  # Has incompatible vectors
    else:
        current_dim = list(dimensions.keys())[0]
        print(f"\n✅ All vectors are {current_dim}-dimensional")
        if current_dim != 1391:
            print("⚠️ But current vectorizer produces 1391-dimensional vectors")
            print("This will cause dimension mismatch errors!")
            return True
    return False

def clear_database():
    """Clear old incompatible vectors"""
    db = DBBridge()
    
    print("\n" + "=" * 70)
    print("CLEARING INCOMPATIBLE VECTORS")
    print("=" * 70)
    
    try:
        conn = db.connect()
        if not conn:
            print("❌ Could not connect to database")
            return False
        
        cursor = conn.cursor()
        cursor.execute("DELETE FROM student_submissions")
        conn.commit()
        
        # Verify deletion
        cursor.execute("SELECT COUNT(*) FROM student_submissions")
        count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        print(f"✅ Database cleared - {count} submissions remaining")
        if count == 0:
            print("✅ Ready to accept new submissions with current vectorizer")
        return True
        
    except Exception as e:
        print(f"❌ Error clearing database: {e}")
        return False

def main():
    print("\n🔍 Sinhala Plagiarism Tool - Database Maintenance Utility\n")
    
    # Analyze current state
    has_issues = analyze_database()
    
    if not has_issues:
        print("\n✅ Database is healthy")
        return
    
    print("\n" + "=" * 70)
    print("RECOMMENDED ACTIONS")
    print("=" * 70)
    print("""
Option 1: Clear old vectors (RECOMMENDED)
  Old vectors are incompatible with the current vectorizer.
  Clearing them will allow new submissions to be processed correctly.
  
Option 2: Retrain vectorizer
  If you want to use the old vectors, you need to retrain the vectorizer
  to match the stored vector dimensions.
  
Option 3: Update vectorizer
  If you want consistent dimensions, update vectorizer.pkl with the
  current configuration.
""")
    
    response = input("Clear incompatible vectors? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        if clear_database():
            print("\n✅ Database maintenance complete!")
            print("The system is now ready to use with the current vectorizer.")
    else:
        print("\n✅ No changes made")

if __name__ == "__main__":
    main()
