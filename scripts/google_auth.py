#!/usr/bin/env python3
"""One-time OAuth2 flow for Google Workspace APIs.

Run this once per account to generate a token file.

Usage:
    python scripts/google_auth.py --account work
    python scripts/google_auth.py --account personal
    python scripts/google_auth.py --account work --no-browser
"""

import argparse
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# Allow running from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google_auth_oauthlib.flow import InstalledAppFlow

from src.config import settings
from src.integrations.google_auth import GoogleAuthManager


def main() -> None:
    parser = argparse.ArgumentParser(description="Google OAuth2 authentication for Nella")
    parser.add_argument(
        "--account",
        required=True,
        help="Account name (e.g. 'work', 'personal'). "
        "Token saved to auth_tokens/google_<account>_auth_token.json",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Use console flow instead of opening a browser. "
        "Prints a URL to visit manually and prompts for the auth code.",
    )
    args = parser.parse_args()

    account = args.account
    creds_path = Path(settings.google_credentials_path)
    token_path = Path(f"auth_tokens/google_{account}_auth_token.json")

    if not creds_path.exists():
        print(f"ERROR: credentials file not found at {creds_path}")
        print("Download it from Google Cloud Console → APIs & Services → Credentials")
        sys.exit(1)

    if token_path.exists():
        print(f"Token already exists at {token_path}")
        response = input("Overwrite? [y/N] ").strip().lower()
        if response != "y":
            print("Aborted.")
            sys.exit(0)

    print(f"Authenticating account: {account}")
    print(f"Requesting scopes: {GoogleAuthManager.SCOPES}")
    flow = InstalledAppFlow.from_client_secrets_file(
        str(creds_path),
        scopes=GoogleAuthManager.SCOPES,
    )

    if args.no_browser:
        # Use a localhost redirect URI — after consent, the browser redirects
        # to localhost which won't be listening. Copy the full URL from the
        # browser's address bar and paste it here.
        redirect_uri = "http://localhost:8085/"
        flow.redirect_uri = redirect_uri
        auth_url, _ = flow.authorization_url(prompt="consent")
        print(f"\nVisit this URL in any browser to authorize:\n\n{auth_url}\n")
        print("After granting access, the browser will redirect to a page that")
        print("won't load. Copy the FULL URL from the address bar and paste it here.\n")
        redirect_response = input("Paste the redirect URL: ").strip()
        code = parse_qs(urlparse(redirect_response).query)["code"][0]
        flow.fetch_token(code=code)
        creds = flow.credentials
    else:
        print("Opening browser for Google OAuth consent...")
        creds = flow.run_local_server(port=0)

    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(creds.to_json(), encoding="utf-8")
    print(f"\nToken saved to {token_path}")


if __name__ == "__main__":
    main()
