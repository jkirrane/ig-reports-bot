"""
Quick test script to validate the setup
"""

import sys
import os

print("=" * 60)
print("IG Reports Bot - Setup Validation")
print("=" * 60)

# Test 1: Check Python version
print("\n1. Checking Python version...")
if sys.version_info >= (3, 11):
    print(f"   ✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
else:
    print(f"   ⚠️  Python {sys.version_info.major}.{sys.version_info.minor} (3.11+ recommended)")

# Test 2: Check dependencies
print("\n2. Checking dependencies...")
try:
    import requests
    import bs4
    from dotenv import load_dotenv
    print("   ✅ Core dependencies installed")
except ImportError as e:
    print(f"   ❌ Missing dependency: {e}")
    print("   Run: pip install -r requirements.txt")
    sys.exit(1)

# Test 3: Check optional dependencies
print("\n3. Checking optional dependencies...")
try:
    import openai
    print("   ✅ OpenAI SDK installed")
    openai_available = True
except ImportError:
    print("   ⚠️  OpenAI SDK not installed (run: pip install openai)")
    openai_available = False

try:
    import atproto
    print("   ✅ atproto installed")
except ImportError:
    print("   ⚠️  atproto not installed (run: pip install atproto)")

# Test 4: Check database
print("\n4. Checking database...")
try:
    from database import initialize_database, get_stats
    
    if not os.path.exists('database/ig_reports.db'):
        initialize_database()
    
    stats = get_stats()
    print(f"   ✅ Database initialized ({stats['total_reports']} reports)")
except Exception as e:
    print(f"   ❌ Database error: {e}")
    sys.exit(1)

# Test 5: Check environment variables
print("\n5. Checking environment variables...")
load_dotenv()

openai_key = os.getenv('OPENAI_API_KEY')
bluesky_handle = os.getenv('BLUESKY_HANDLE')
bluesky_password = os.getenv('BLUESKY_APP_PASSWORD')

if openai_key and openai_key.startswith('sk-'):
    print("   ✅ OPENAI_API_KEY configured")
elif openai_available:
    print("   ⚠️  OPENAI_API_KEY not configured (set in .env)")
else:
    print("   ℹ️  OPENAI_API_KEY not needed (OpenAI not installed)")

if bluesky_handle and bluesky_password:
    print("   ✅ Bluesky credentials configured")
else:
    print("   ⚠️  Bluesky credentials not configured (set in .env)")

# Test 6: Test scraper
print("\n6. Testing scraper...")
try:
    from scrapers import BaseScraper
    
    scraper = BaseScraper()
    html = scraper.fetch_page('https://www.oversight.gov')
    
    if html and len(html) > 1000:
        print(f"   ✅ Scraper working ({len(html)} bytes fetched)")
    else:
        print("   ⚠️  Scraper returned unexpected result")
except Exception as e:
    print(f"   ❌ Scraper error: {e}")

# Test 7: Test LLM (if configured)
if openai_available and openai_key:
    print("\n7. Testing LLM integration...")
    try:
        from llm import call_gpt
        
        response = call_gpt(
            "Say 'test successful' in JSON format with a 'message' field",
            max_tokens=20,
            response_format={"type": "json_object"}
        )
        
        if response:
            print(f"   ✅ LLM working: {response[:50]}")
        else:
            print("   ⚠️  LLM returned no response")
    except Exception as e:
        print(f"   ❌ LLM error: {e}")
else:
    print("\n7. Skipping LLM test (not configured)")

# Summary
print("\n" + "=" * 60)
print("VALIDATION COMPLETE")
print("=" * 60)

print("\n✅ Core functionality working")
print("\n📝 Next steps:")
print("   1. Configure .env with your API keys")
print("   2. Test scraper: python -m scrapers.oversight_gov")
print("   3. Run pipeline: python run_daily.py --dry-run --days-back 2")
print("   4. Implement Bluesky posting in bot/bluesky_poster.py")

print("\n💡 Quick commands:")
print("   python run_daily.py --dry-run  # Test without saving")
print("   python run_daily.py            # Full pipeline")
print("   python -m database.db          # View database stats")
print("   python test_setup.py           # Run this test again")
