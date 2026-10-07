#!/usr/bin/env python3
"""
Legacy terminal utility to check OpenRouter key usage and credit balance.
Designed for Windows users, headless environments, or anyone who prefers CLI over the macOS app.
Zero mandatory external dependencies (uses standard library with fallback to requests/dotenv if installed).
"""

import sys
import os
import json

def load_env_file(filepath=".env"):
    """Lightweight .env parser fallback when python-dotenv is not installed."""
    if not os.path.isfile(filepath):
        # Also check parent directory if run from scripts/
        parent_filepath = os.path.join("..", filepath)
        if os.path.isfile(parent_filepath):
            filepath = parent_filepath
        else:
            return
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k and k not in os.environ:
                    os.environ[k] = v
    except Exception:
        pass

# 1. Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    # also try root if run from scripts/
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
except ImportError:
    load_env_file(".env")
    load_env_file(os.path.join(os.path.dirname(__file__), "..", ".env"))

# 2. Resolve API key
api_key = None
if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
    api_key = sys.argv[1].strip()
if not api_key:
    api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    if sys.stdin.isatty():
        try:
            api_key = input("Enter OPENROUTER_API_KEY: ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            sys.exit(1)
    if not api_key:
        sys.exit("❌ Error: OPENROUTER_API_KEY not found in arguments, environment, or .env")

headers = {
    "Authorization": f"Bearer {api_key}",
    "User-Agent": "OpenRouter-Legacy-CLI/1.0"
}

def fetch_json(url):
    """Fetch JSON via requests if installed, else fallback to standard urllib."""
    try:
        import requests
        res = requests.get(url, headers=headers, timeout=15)
        if not res.ok:
            return None, f"❌ Error ({res.status_code}): {res.text}"
        return res.json(), None
    except ImportError:
        import urllib.request
        import urllib.error
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                content = response.read().decode("utf-8")
                return json.loads(content), None
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            return None, f"❌ Error ({e.code}): {err_body}"
        except Exception as e:
            return None, f"❌ Connection Error: {str(e)}"

# 1. Key info & limits
key_data_json, err = fetch_json("https://openrouter.ai/api/v1/auth/key")
if err:
    sys.exit(err)

data = key_data_json.get("data", {}) if key_data_json else {}
usage = data.get("usage", 0.0)
limit = data.get("limit")

print(f"🔑 Key Label:     {data.get('label')}")
print(f"💸 Key Usage:     ${usage:,.4f} USD")
print(f"🎯 Key Limit:     {f'${limit:,.4f} USD' if limit is not None else 'Unlimited'}")
if limit is not None:
    print(f"⏳ Key Remaining: ${max(0.0, limit - usage):,.4f} USD")
print(f"🆓 Free Tier:     {'Yes' if data.get('is_free_tier') else 'No'}")

# 2. Account credits & totals
credits_json, _ = fetch_json("https://openrouter.ai/api/v1/credits")
if credits_json:
    c = credits_json.get("data", {})
    total_credits = c.get("total_credits", 0.0)
    total_usage = c.get("total_usage", 0.0)
    print("-" * 35)
    print(f"💰 Total Credits: ${total_credits:,.4f} USD")
    print(f"📊 Total Usage:   ${total_usage:,.4f} USD")
    print(f"💳 Total Balance: ${max(0.0, total_credits - total_usage):,.4f} USD")
