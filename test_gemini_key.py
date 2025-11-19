#!/usr/bin/env python3
"""
Test script to verify if your Gemini API key is valid
"""
import os
import sys
from dotenv import load_dotenv
import google.generativeai as genai

# Load .env file
load_dotenv()

# Get API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ Error: GEMINI_API_KEY not found in .env file")
    sys.exit(1)

api_key = api_key.strip()
print(f"API Key found: {api_key[:10]}...{api_key[-5:]}")
print(f"Length: {len(api_key)} characters")
print(f"Starts with 'AIza': {api_key.startswith('AIza')}")

if not api_key.startswith('AIza'):
    print("\n[WARNING] API key format looks incorrect!")
    print("Gemini API keys should start with 'AIza'")
    sys.exit(1)

# Test the API key
try:
    genai.configure(api_key=api_key)
    # Try Gemini 2.5 Flash model first, fallback to others if not available
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
    except:
        try:
            model = genai.GenerativeModel("gemini-2.0-flash-exp")
        except:
            try:
                model = genai.GenerativeModel("gemini-2.0-flash")
            except:
                model = genai.GenerativeModel("gemini-1.5-flash")
    
    print("\nTesting API key...")
    response = model.generate_content("Say 'Hello' if you can read this.")
    
    if response.text:
        print("[SUCCESS] Your Gemini API key is VALID!")
        print(f"Response: {response.text}")
        sys.exit(0)
    else:
        print("[WARNING] API responded but with no text")
        sys.exit(1)
        
except Exception as e:
    error_msg = str(e)
    print(f"\n[ERROR] API key test failed!")
    print(f"Error: {error_msg}")
    
    if "API_KEY_INVALID" in error_msg or "API key not valid" in error_msg:
        print("\n" + "="*60)
        print("Your API key is INVALID. Please get a new one:")
        print("="*60)
        print("1. Go to: https://aistudio.google.com/apikey")
        print("2. Sign in with your Google account")
        print("3. Click 'Create API Key'")
        print("4. Copy the new API key")
        print("5. Update your .env file with:")
        print("   GEMINI_API_KEY=your_new_key_here")
        print("="*60)
    
    sys.exit(1)

