#!/usr/bin/env python3
"""
validate_google_oauth.py - Quick validation of Google OAuth setup
Run this before testing login to catch configuration issues early
"""
import os
import sys
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()
load_dotenv('.env.local')

def check_env_vars():
    """Verify all required environment variables are set"""
    print("\n" + "="*60)
    print("1. ENVIRONMENT VARIABLES CHECK")
    print("="*60)
    
    required_vars = {
        'GOOGLE_CLIENT_ID': 'OAuth Client ID',
        'GOOGLE_CLIENT_SECRET': 'OAuth Client Secret',
        'REDIRECT_URI': 'Callback Redirect URI',
    }
    
    all_set = True
    for var, desc in required_vars.items():
        value = os.getenv(var)
        if value:
            # Show first 20 chars for secrets
            display = value if len(value) < 30 else value[:20] + "..."
            print(f"✅ {var}: {display}")
        else:
            print(f"❌ {var}: NOT SET")
            all_set = False
    
    return all_set

def check_redirect_uri_format():
    """Validate redirect URI format"""
    print("\n" + "="*60)
    print("2. REDIRECT URI VALIDATION")
    print("="*60)
    
    redirect_uri = os.getenv('REDIRECT_URI', '')
    
    checks = {
        'Contains /callback': '/callback' in redirect_uri,
        'No trailing slash': not redirect_uri.endswith('/'),
        'HTTP protocol only (for dev)': redirect_uri.startswith('http://'),
        'No extra params': '?' not in redirect_uri and '#' not in redirect_uri,
    }
    
    all_passed = True
    for check, result in checks.items():
        status = "✅" if result else "❌"
        print(f"{status} {check}")
        if not result:
            all_passed = False
    
    if not all_passed:
        print(f"\n⚠️  Current URI: {redirect_uri}")
        print(f"✅ Expected format: http://127.0.0.1:5000/callback")
    
    return all_passed

def test_oauth_endpoints():
    """Test connectivity to Google OAuth endpoints"""
    print("\n" + "="*60)
    print("3. GOOGLE ENDPOINTS CONNECTIVITY")
    print("="*60)
    
    endpoints = {
        'Authorization': 'https://accounts.google.com/o/oauth2/v2/auth',
        'Token Exchange': 'https://oauth2.googleapis.com/token',
        'User Info': 'https://www.googleapis.com/oauth2/v2/userinfo',
    }
    
    all_reachable = True
    for name, url in endpoints.items():
        try:
            response = requests.head(url, timeout=5)
            print(f"✅ {name}: Reachable (HTTP {response.status_code})")
        except Exception as e:
            print(f"❌ {name}: Not reachable - {str(e)}")
            all_reachable = False
    
    return all_reachable

def check_credentials_format():
    """Validate credentials format"""
    print("\n" + "="*60)
    print("4. CREDENTIALS FORMAT")
    print("="*60)
    
    client_id = os.getenv('GOOGLE_CLIENT_ID', '')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET', '')
    
    checks = {
        'Client ID looks valid': '.apps.googleusercontent.com' in client_id,
        'Client Secret set': len(client_secret) > 20,
        'No quotes in values': '"' not in client_id and'"' not in client_secret,
    }
    
    all_valid = True
    for check, result in checks.items():
        status = "✅" if result else "⚠️ " if not result else "✅"
        print(f"{status} {check}")
        if not result:
            all_valid = False
    
    return all_valid

def generate_auth_url():
    """Generate and display authorization URL for manual testing"""
    print("\n" + "="*60)
    print("5. AUTHORIZATION URL")
    print("="*60)
    
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    redirect_uri = os.getenv('REDIRECT_URI', 'http://127.0.0.1:5000/callback')
    
    if not client_id:
        print("❌ Cannot generate URL - GOOGLE_CLIENT_ID not set")
        return
    
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        "&response_type=code"
        "&scope=openid email profile"
        "&access_type=offline"
        "&prompt=consent"
    )
    
    print("Use this URL to manually test authorization:")
    print(f"\n{auth_url}\n")
    print("Steps:")
    print("1. Copy the URL above")
    print("2. Paste into browser and authorize")
    print("3. You'll be redirected to callback URL")
    print("4. Copy the 'code' parameter from the URL")
    print("5. Use it in manual token exchange test (see GOOGLE_OAUTH_400_FIX.md)")

def main():
    """Run all checks"""
    print("\n" + "🔐 " + "="*56 + " 🔐")
    print("  GOOGLE OAUTH CONFIGURATION VALIDATOR")
    print("🔐 " + "="*56 + " 🔐")
    
    results = {
        'Environment Variables': check_env_vars(),
        'Redirect URI Format': check_redirect_uri_format(),
        'Google Endpoints': test_oauth_endpoints(),
        'Credentials Format': check_credentials_format(),
    }
    
    # Generate URL for testing
    generate_auth_url()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    all_passed = all(results.values())
    
    for check, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {check}")
    
    print("\n" + "="*60)
    
    if all_passed:
        print("✅ All checks passed! Your configuration looks good.")
        print("\nNext steps:")
        print("1. Start the Flask app: python app.py")
        print("2. Visit http://127.0.0.1:5000")
        print("3. Click 'Sign in with Google'")
        return 0
    else:
        print("❌ Some checks failed. Review the output above.")
        print("\nCommon fixes:")
        print("1. Check your .env file exists and has GOOGLE_CLIENT_ID set")
        print("2. Verify REDIRECT_URI exactly matches Google Console")
        print("3. Regenerate credentials if they're old")
        print("\nFor more help, see: GOOGLE_OAUTH_400_FIX.md")
        return 1

if __name__ == '__main__':
    sys.exit(main())
