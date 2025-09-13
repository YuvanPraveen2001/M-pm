"""
Debug schema structure to understand column format
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dynamic_schema_manager import get_dynamic_schema_manager

def debug_schema_structure():
    """Debug the schema structure to understand column format"""
    
    print("🔍 Debugging Schema Structure")
    print("=" * 50)
    
    # Initialize schema manager
    try:
        manager = get_dynamic_schema_manager()
        print("✅ Schema manager initialized\n")
        
        # Get schema for a simple query
        result = manager.get_schema_for_query("employee availability query")
        
        print(f"🔍 Search method: {result['search_method']}")
        print(f"📊 Tables found: {len(result['tables'])}\n")
        
        # Examine the first few tables to understand structure
        for i, table in enumerate(result['tables'][:3]):
            print(f"📋 Table {i+1}: {table['table_name']}")
            
            # Show table structure
            print(f"   Keys in table dict: {list(table.keys())}")
            
            if 'columns' in table:
                print(f"   📝 Columns ({len(table['columns'])}):")
                
                # Show first few columns to understand structure
                for j, column in enumerate(table['columns'][:3]):
                    print(f"      Column {j+1}: {type(column)} - {column}")
                    if isinstance(column, dict):
                        print(f"         Keys: {list(column.keys())}")
                    
            print() # Empty line for readability
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_schema_structure()
