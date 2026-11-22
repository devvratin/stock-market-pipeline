"""Upstox OAuth 2.0 authentication and daily token caching."""

import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

import requests

from stress.common import config
from stress.common.logging_setup import get_logger
from stress.common.timeutil import IST

logger = get_logger(__name__)

AUTHORIZE_URL = "https://api.upstox.com/v2/login/authorization/dialog"
TOKEN_URL = "https://api.upstox.com/v2/login/authorization/token"
DEFAULT_TOKEN_PATH = Path(".token.json")


def _today_ist() -> str:
    """Return today's date in IST as YYYY-MM-DD."""
    return datetime.now(IST).date().isoformat()


def build_login_url(
    api_key: str = config.UPSTOX_API_KEY,
    redirect_uri: str = config.REDIRECT_URI,
) -> str:
    """Build the Upstox OAuth login URL."""
    params = urlencode(
        {
            "response_type": "code",
            "client_id": api_key,
            "redirect_uri": redirect_uri,
        }
    )
    return f"{AUTHORIZE_URL}?{params}"


def exchange_code_for_token(
    code: str,
    api_key: str = config.UPSTOX_API_KEY,
    api_secret: str = config.UPSTOX_API_SECRET,
    redirect_uri: str = config.REDIRECT_URI,
) -> str:
    """Exchange a single-use OAuth authorization code for an access token."""
    headers = {
        "accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    payload = {
        "code": code.strip(),
        "client_id": api_key,
        "client_secret": api_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    response = requests.post(TOKEN_URL, headers=headers, data=payload, timeout=15)
    response.raise_for_status()
    token = response.json()["access_token"]
    logger.info("Successfully exchanged auth code for Upstox access token.")
    return token


def save_token(access_token: str, token_path: Path = DEFAULT_TOKEN_PATH) -> None:
    """Save the access token alongside today's IST date."""
    data = {"access_token": access_token, "date": _today_ist()}
    token_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    logger.info("Saved Upstox token to %s.", token_path)


def load_todays_token(token_path: Path = DEFAULT_TOKEN_PATH) -> str | None:
    """Return the cached token if it was saved today (IST), else None."""
    if not token_path.exists():
        return None
    data = json.loads(token_path.read_text(encoding="utf-8"))
    if data.get("date") == _today_ist() and data.get("access_token"):
        return data["access_token"]
    return None


def get_token(token_path: Path = DEFAULT_TOKEN_PATH) -> str:
    """Return today's valid token, or prompt the user to log in once."""
    cached = load_todays_token(token_path)
    if cached:
        logger.info("Using cached Upstox token for %s.", _today_ist())
        return cached

    if not config.UPSTOX_API_KEY or not config.UPSTOX_API_SECRET:
        raise ValueError("Missing UPSTOX_API_KEY or UPSTOX_API_SECRET in .env")

    login_url = build_login_url()
    print("\n1. Open this URL in your browser and log in to Upstox:")
    print(f"   {login_url}\n")
    print("2. After redirect, copy the 'code=' value from the browser address bar.")
    auth_code = input("Paste auth code here: ").strip()

    token = exchange_code_for_token(auth_code)
    save_token(token, token_path)
    return token