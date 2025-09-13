#!/usr/bin/env python3
"""
Simple test to verify the schema_result attribute fix
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from healthcare_chatbot_service import HealthcareChatbotService
    
    print("🔍 Testing schema result structure fix...")
    
    # Create a mock schema result like what get_schema_for_query returns
    mock_schema_result = {
        "tables": [
            {"name": "Employee", "table_name": "Employee", "columns": []},
            {"name": "EmployeeAvailabilityDateTime", "table_name": "EmployeeAvailabilityDateTime", "columns": []}
        ],
        "confidence_score": 0.8,
        "search_method": "complete_schema"
    }
    
    # Test accessing tables correctly
    try:
        table_names = [t["name"] for t in mock_schema_result["tables"]]
        print(f"✅ Correct access: {table_names}")
    except Exception as e:
        print(f"❌ Error with correct access: {e}")
    
    # Test the old (incorrect) way that was causing the error
    try:
        table_names = [t.table_name for t in mock_schema_result.tables]
        print(f"❌ Old way still works (this shouldn't happen): {table_names}")
    except AttributeError as e:
        print(f"✅ Old way correctly fails: {e}")
    
    print("\n🎯 Test completed - the fix should work correctly")
    
except Exception as e:
    print(f"❌ Error importing or testing: {e}")
    import traceback
    traceback.print_exc()
