#!/usr/bin/env python3
"""
QUICK START: Verify AI Generation Setup
Run this to ensure Ollama is running and AI questions are being generated
"""

import sys
import os
sys.path.insert(0, '/Users/shravani/Documents/Interview-ProAI')

from utils.ai_engine import generate_question, generate_mcq_questions
from utils.ai_backends import get_ai_manager

print("\n" + "="*80)
print("INTERVIEW-PROAI: AI INTEGRATION VERIFICATION")
print("="*80)

# Test 1: Check AI Backend connection
print("\n[1] Checking AI Backend Connection...")
try:
    ai = get_ai_manager()
    test_response = ai.generate("Say 'OK' only.")
    if test_response and not test_response.startswith("["):
        print(f"    ✅ AI backend is running and responding")
        print(f"       Response: {test_response[:50]}")
    else:
        print(f"    ⚠️  AI backend response seems incorrect")
        print(f"       Response: {test_response[:60]}")
except Exception as e:
    print(f"    ❌ AI backend connection failed: {e}")
    print("    💡 Check OPENAI_API_KEY or ensure Ollama is running: `ollama serve`")

# Test 2: MCQ Generation
print("\n[2] Testing MCQ Generation for 'Software Engineer'...")
try:
    mcq = generate_mcq_questions("Software Engineer", n=1)
    if mcq and len(mcq) > 0:
        q = mcq[0]
        print(f"    ✅ MCQ generated successfully")
        print(f"       Q: {q.get('q', '')[:70]}...")
        print(f"       Options: {len(q.get('options', []))} choices")
        print(f"       Answer: {q.get('answer', 'N/A')}")
    else:
        print(f"    ❌ MCQ generation returned empty")
        print("    💡 Check Ollama logs or try again")
except Exception as e:
    print(f"    ❌ MCQ generation error: {e}")

# Test 3: Interview Question Generation
print("\n[3] Testing Interview Question Generation...")
try:
    question = generate_question("Data Scientist")
    if question and not question.startswith("[") and len(question) > 10:
        print(f"    ✅ Interview question generated")
        print(f"       Q: {question[:80]}...")
    else:
        print(f"    ⚠️  Response might be error message or too short")
        print(f"       Response: {question[:60]}")
except Exception as e:
    print(f"    ❌ Interview question error: {e}")

print("\n" + "="*80)
print("VERIFICATION COMPLETE")
print("="*80)
print("""
Key Points:
✅ If all tests pass, AI integration is working for ALL roles
✅ Questions now work for: Software Engineer, Data Scientist, Frontend Dev, etc.
✅ Both screening levels (MCQ & Coding) use AI
✅ Interview questions use AI for all roles

Troubleshooting:
- If Ollama connection fails, start: ollama serve
- If questions are empty, check Ollama model: ollama list
- Logs are written to console and through Python logging module
""")
