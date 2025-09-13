#!/usr/bin/env python3
"""
Test intent detection
"""

import re

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

def test_intent_detection(message: str):
    print(f"Testing message: '{message}'")
    message_lower = message.lower()
    
    for intent, patterns in intent_patterns.items():
        print(f"  Checking {intent}:")
        for pattern in patterns:
            if re.search(pattern, message_lower):
                print(f"    ✅ MATCH: {pattern}")
                return intent
            else:
                print(f"    ❌ No match: {pattern}")
    
    print("  🔍 No patterns matched, returning 'general_query'")
    return 'general_query'

if __name__ == "__main__":
    test_queries = [
        "get me the availability of jon snow",
        "check availability for Dr. Smith",
        "show availability",
        "when is John available"
    ]
    
    for query in test_queries:
        result = test_intent_detection(query)
        print(f"Result: {result}\n")
