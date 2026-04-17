#!/usr/bin/env python3
"""
Test ATS JSON parsing logic
Verify that various AI response formats can be correctly parsed
"""

import json
import sys

def test_json_parsing(raw_response: str, test_name: str) -> dict:
    """Test JSON parsing with multiple strategies"""
    print(f"\n{'='*80}")
    print(f"TEST: {test_name}")
    print(f"{'='*80}")
    print(f"Input: {raw_response[:100]}...")
    
    data = None
    
    # Strategy 1: Direct parse
    try:
        data = json.loads(raw_response)
        print("✅ SUCCESS: Direct JSON parse")
        return data
    except Exception as e:
        print(f"❌ Direct parse failed: {e}")
    
    # Strategy 2: Strip markdown code blocks
    if not data:
        try:
            clean = raw_response.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
                clean = clean.strip()
            data = json.loads(clean)
            print("✅ SUCCESS: Markdown strip parse")
            return data
        except Exception as e:
            print(f"❌ Markdown strip failed: {e}")
    
    # Strategy 3: Extract JSON from text
    if not data:
        try:
            start = raw_response.index("{")
            end = raw_response.rindex("}") + 1
            data = json.loads(raw_response[start:end])
            print("✅ SUCCESS: Extract JSON parse")
            return data
        except Exception as e:
            print(f"❌ Extract JSON failed: {e}")
    
    # Strategy 4: Fix truncated JSON
    if not data:
        try:
            fixed = raw_response.strip()
            open_brackets = fixed.count("[") - fixed.count("]")
            open_braces = fixed.count("{") - fixed.count("}")
            for _ in range(open_brackets):
                fixed += "]"
            for _ in range(open_braces):
                fixed += "}"
            data = json.loads(fixed)
            print("✅ SUCCESS: Fixed truncated JSON")
            return data
        except Exception as e:
            print(f"❌ Fix truncated failed: {e}")
    
    # All strategies failed
    if not data:
        print("❌ ALL PARSING STRATEGIES FAILED")
        return None
    
    return data


# Test cases with various AI response formats
test_cases = [
    # Test 1: Perfect JSON response
    (
        '{"score": 75, "matched_skills": ["Python", "AWS"], "missing_skills": ["Kubernetes"], "suggestions": ["Learn Kubernetes", "Improve AWS skills", "Get AWS certification"]}',
        "Perfect JSON response"
    ),
    
    # Test 2: JSON with markdown code block
    (
        "```json\n{\"score\": 82, \"matched_skills\": [\"Java\", \"Spring\"], \"missing_skills\": [\"Kubernetes\"], \"suggestions\": [\"Learn Kubernetes\", \"Master Docker\", \"Study microservices\"]}\n```",
        "JSON with markdown code block"
    ),
    
    # Test 3: JSON with extra text before
    (
        "Here is the analysis:\n{\"score\": 65, \"matched_skills\": [\"JavaScript\"], \"missing_skills\": [\"TypeScript\", \"React\"], \"suggestions\": [\"Learn TypeScript\", \"Study React\", \"Practice testing\"]}",
        "JSON with extra text before"
    ),
    
    # Test 4: JSON with extra text after
    (
        "{\"score\": 88, \"matched_skills\": [\"Python\", \"Django\"], \"missing_skills\": [\"FastAPI\"], \"suggestions\": [\"Learn FastAPI\", \"Master async\", \"Study ASGI\"]} That's the analysis!",
        "JSON with extra text after"
    ),
    
    # Test 5: Incomplete JSON (missing closing braces)
    (
        '{"score": 45, "matched_skills": ["SQL"], "missing_skills": ["MongoDB", "Redis"], "suggestions": ["Learn NoSQL", "Study caching", "Master databases"',
        "Incomplete JSON (missing closing braces)"
    ),
    
    # Test 6: Incomplete JSON array (missing closing bracket)
    (
        '{"score": 55, "matched_skills": ["C++", "Python"], "missing_skills": ["Rust", "Go"], "suggestions": ["Learn systems programming", "Study Rust", "Master low-level optimization"]}',
        "Valid JSON (testing as control)"
    ),
]

def main():
    print("\n" + "="*80)
    print("ATS JSON PARSING TEST SUITE")
    print("="*80)
    
    passed = 0
    failed = 0
    
    for raw_response, test_name in test_cases:
        result = test_json_parsing(raw_response, test_name)
        if result:
            passed += 1
            print("Result:", result)
        else:
            failed += 1
    
    print("\n" + "="*80)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*80)
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
