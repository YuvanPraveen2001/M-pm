#!/usr/bin/env python3
"""
Test script to verify availability query generation without location criteria
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from availability_query_generator import AvailabilityQueryGenerator

def test_availability_query():
    """Test the availability query generation"""
    print("🧪 Testing Availability Query Generation (No Location Criteria)")
    print("=" * 60)
    
    # Initialize the generator
    generator = AvailabilityQueryGenerator()
    
    # Test data
    query_text = "need a list of available employees on this wednesday"
    metadata = {
        'gender': 'Male',
        'SiteId': 2,  # This should be ignored now
        "today's date": '2025-09-12',
        'target_date': 'wednesday'
    }
    
    print(f"📝 Query Text: {query_text}")
    print(f"📊 Metadata: {metadata}")
    print("\n🔍 Generated SQL Query:")
    print("-" * 60)
    
    try:
        # Generate the query
        sql_query = generator.generate_availability_query(query_text, metadata)
        print(sql_query)
        
        print("\n" + "=" * 60)
        print("✅ Query Generation Test Completed")
        
        # Check if location criteria is excluded
        if 'SiteId' not in sql_query and 'LocationName' not in sql_query:
            print("✅ SUCCESS: Location criteria successfully excluded")
        else:
            print("❌ WARNING: Location criteria might still be present")
            
        if 'wednesday' in sql_query.lower() or 'WeekDay = 3' in sql_query:
            print("✅ SUCCESS: Weekday filtering is working")
        else:
            print("❌ WARNING: Weekday filtering might not be working")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_availability_query()
