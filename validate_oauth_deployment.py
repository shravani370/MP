#!/usr/bin/env python3
"""
Quick script to validate your OAuth setup for deployment
Run this after updating environment variables
"""
import os
import sys
from dotenv import load_dotenv

print("\n" + "="*70)
print("GOOGLE OAUTH DEPLOYMENT VALIDATION")
print("="*70)

# Load from .env
load_dotenv()

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://127.0.0.1:5000/callback")

print("\n📋 CURRENT CONFIGURATION:")
print("-" * 70)
print(f"CLIENT_ID:      {CLIENT_ID[:30] + '...' if CLIENT_ID else '❌ NOT SET'}")
print(f"CLIENT_SECRET:  {'✅ SET' if CLIENT_SECRET else '❌ NOT SET'}")
print(f"REDIRECT_URI:   {REDIRECT_URI}")

print("\n✅ VERIFICATION CHECKS:")
print("-" * 70)

checks = {
    "CLIENT_ID is set": bool(CLIENT_ID),
    "CLIENT_SECRET is set": bool(CLIENT_SECRET),
    "REDIRECT_URI contains /callback": "/callback" in REDIRECT_URI,
    "REDIRECT_URI has no trailing slash": not REDIRECT_URI.endswith("/"),
    "For production, using HTTPS": REDIRECT_URI.startswith("https://") or REDIRECT_URI.startswith("http://127.0.0.1"),
}

all_pass = True
for check, result in checks.items():
    symbol = "✅" if result else "❌"
    print(f"{symbol} {check}")
    if not result:
        all_pass = False

print("\n" + "="*70)
if all_pass:
    print("✅ OAuth configuration looks good!")
    print("\nNEXT STEPS:")
    print("1. Verify these values match your Google Cloud Console settings")
    print("2. Make sure REDIRECT_URI matches your deployed domain")
    print("3. Test the login flow on your deployment")
else:
    print("❌ Fix the issues above before deploying!")
    print("\nHINTS:")
    print("- Make sure .env file has correct values")
    print("- For production, REDIRECT_URI should be https://your-domain/callback")
    print("- Add this redirect URI to Google Cloud Console authorized URIs")

print("="*70 + "\n")
