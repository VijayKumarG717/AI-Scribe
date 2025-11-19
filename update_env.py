#!/usr/bin/env python3
"""
Script to update .env file with correct AssemblyAI API key variable name
"""
import os
import shutil
from datetime import datetime

env_file = '.env'
backup_file = f'.env.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}'

print("Updating .env file...")

# Read existing .env if it exists
env_vars = {}
if os.path.exists(env_file):
    # Create backup
    try:
        shutil.copy2(env_file, backup_file)
        print(f"Created backup: {backup_file}")
    except Exception as e:
        print(f"Warning: Could not create backup: {e}")
    
    # Read existing values
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and '=' in line and not line.startswith('#'):
                parts = line.split('=', 1)
                key = parts[0].strip()
                value = parts[1].strip().strip('"\'')
                env_vars[key] = value

# Get AssemblyAI API key from any variation
assembly_key = (
    env_vars.get("ASSEMBLYAI_API_KEY") or 
    env_vars.get("ASSEMBLY_API_KEY") or 
    "29c2b594dcaf4c18ba93348005a9bc22"  # default from your original request
)

# Get Gemini API key
gemini_key = (
    env_vars.get("GEMINI_API_KEY") or 
    "AIzaSyAJA4yZOhNp0mzRvwmw5lDKJLM31rEGjE"  # default from your original request
)

# Try to read from api key.txt files
possible_files = ['api key.txt', 'api_key.txt', 'apikey.txt', 'api-keys.txt']
for api_file in possible_files:
    if os.path.exists(api_file):
        try:
            with open(api_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and '=' in line:
                        parts = line.split('=', 1)
                        key = parts[0].strip()
                        value = parts[1].strip().strip('"\'')
                        if 'ASSEMBLY' in key.upper() and not assembly_key:
                            assembly_key = value
                        elif 'GEMINI' in key.upper() and not gemini_key:
                            gemini_key = value
            print(f"Found API keys in {api_file}")
        except Exception as e:
            print(f"Error reading {api_file}: {e}")

# Write updated .env file
try:
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(f"ASSEMBLYAI_API_KEY={assembly_key}\n")
        f.write(f"GEMINI_API_KEY={gemini_key}\n")
    print(f"\n✅ Successfully updated {env_file}!")
    print(f"\nContents:")
    print(f"ASSEMBLYAI_API_KEY={assembly_key}")
    print(f"GEMINI_API_KEY={gemini_key}")
except PermissionError:
    print(f"\n❌ Error: Permission denied. Cannot write to {env_file}")
    print("\nPlease manually update your .env file with:")
    print(f"ASSEMBLYAI_API_KEY={assembly_key}")
    print(f"GEMINI_API_KEY={gemini_key}")
except Exception as e:
    print(f"\n❌ Error updating .env file: {e}")
    print("\nPlease manually update your .env file with:")
    print(f"ASSEMBLYAI_API_KEY={assembly_key}")
    print(f"GEMINI_API_KEY={gemini_key}")

