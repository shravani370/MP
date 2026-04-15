#!/usr/bin/env python3
"""
Test AI generation for all role types
Verify MCQ, coding, and interview questions are all AI-generated
"""

import sys
sys.path.insert(0, '/Users/shravani/Documents/Interview-ProAI')

from utils.ai_engine import generate_question, generate_mcq_questions, generate_coding_questions

def test_role(role: str):
    """Test question generation for a specific role"""
    print(f"\n{'='*80}")
    print(f"TESTING ROLE: {role}")
    print(f"{'='*80}")
    
    # Test 1: MCQ Generation
    print(f"\n[1] MCQ Questions for {role}:")
    try:
        mcq_qs = generate_mcq_questions(role, n=3)
        if mcq_qs:
            print(f"    ✅ Generated {len(mcq_qs)} MCQ questions")
            for i, q in enumerate(mcq_qs, 1):
                print(f"       Q{i}: {q.get('q', 'N/A')[:60]}...")
        else:
            print(f"    ❌ MCQ generation returned empty")
    except Exception as e:
        print(f"    ❌ MCQ generation error: {e}")
    
    # Test 2: Coding Questions Generation
    print(f"\n[2] Coding Questions for {role}:")
    try:
        code_qs = generate_coding_questions(role, n=2)
        if code_qs:
            print(f"    ✅ Generated {len(code_qs)} coding questions")
            for i, q in enumerate(code_qs, 1):
                print(f"       Q{i}: {q.get('title', 'N/A')} ({q.get('difficulty', 'N/A')})")
        else:
            print(f"    ❌ Coding generation returned empty")
    except Exception as e:
        print(f"    ❌ Coding generation error: {e}")
    
    # Test 3: Interview Question Generation
    print(f"\n[3] Interview Question for {role}:")
    try:
        interview_q = generate_question(role)
        if interview_q and not interview_q.startswith("["):
            print(f"    ✅ Generated interview question")
            print(f"       Q: {interview_q[:100]}...")
        else:
            print(f"    ❌ Interview generation failed or unavailable")
            print(f"       Response: {interview_q[:80] if interview_q else 'None'}...")
    except Exception as e:
        print(f"    ❌ Interview generation error: {e}")

# Test various roles
TEST_ROLES = [
    "Software Engineer",
    "Data Scientist",
    "Data Analyst",
    "Frontend Developer",
    "Backend Developer", 
    "DevOps Engineer",
    "ML Engineer",
    "Cybersecurity Analyst",
    "Full Stack Developer",
    "Random Unknown Role"
]

print("\n" + "="*80)
print("AI QUESTION GENERATION TEST")
print("="*80)
print("Testing that ALL roles use AI for question generation")

for role in TEST_ROLES:
    test_role(role)

print(f"\n{'='*80}")
print("TEST COMPLETE")
print("="*80)
print("✅ If you see questions generated for all roles, AI integration is working!")
