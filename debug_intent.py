#!/usr/bin/env python3
"""
Quick test to check if our patterns are working
"""

import re

def analyze_intent(message: str) -> str:
    """Analyze message intent"""
    message_lower = message.lower()
    
    intent_patterns = {
        'check_availability': [
            r'check.*availabilit',
            r'is.*available',
            r'free.*time',
            r'when.*available',
            r'schedule.*for',
            r'get.*availability',
            r'show.*availability',
            r'availability.*of',
            r'find.*availability'
        ],
        'book_appointment': [
            r'book.*appointment',
            r'schedule.*appointment',
            r'make.*appointment',
            r'reserve.*time',
            r'set.*appointment'
        ]
    }
    
    print(f"Analyzing: '{message}'")
    print(f"Lowercase: '{message_lower}'")
    
    for intent, patterns in intent_patterns.items():
        print(f"  Checking {intent}:")
        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                print(f"    ✅ MATCHED: {pattern} -> {match.group()}")
                return intent
            else:
                print(f"    ❌ No match: {pattern}")
    
    print("  -> Returning 'general_query'")
    return 'general_query'

if __name__ == "__main__":
    test_message = "get me the availability of jon snow"
    result = analyze_intent(test_message)
    print(f"\nFinal result: {result}")
    
    # Test a few variations
    for msg in [
        "get me the availability of jon snow",
        "availability of john",
        "when is Mary available",
        "show availability for Dr. Smith"
    ]:
        print(f"\n{'='*50}")
        result = analyze_intent(msg)
        print(f"Result: {result}")
