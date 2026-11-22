"""Offline unit tests for Phase 2 Upstox authentication."""

import json

import requests

from stress.auth.upstox_auth import (
    build_login_url,
    exchange_code_for_token,
    load_todays_token,
    save_token,
)


def test_build_login_url():
    url = build_login_url(
        api_key="my-key",
        redirect_uri="http://127.0.0.1:8000/callback",
    )
    assert url.startswith("https://api.upstox.com/v2/login/authorization/dialog?")
    assert "response_type=code" in url
    assert "client_id=my-key" in url
    assert "redirect_uri=http%3A%2F%2F127.0.0.1%3A8000%2Fcallback" in url


def test_save_and_load_todays_token(tmp_path):
    token_file = tmp_path / ".token.json"
    save_token("secret-token-123", token_path=token_file)

    assert load_todays_token(token_path=token_file) == "secret-token-123"


def test_expired_token_returns_none(tmp_path):
    token_file = tmp_path / ".token.json"
    token_file.write_text(
        json.dumps({"access_token": "old-token", "date": "2020-01-01"}),
        encoding="utf-8",
    )

    assert load_todays_token(token_path=token_file) is None


def test_exchange_code_for_token_mocked(monkeypatch):
    class FakeResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict:
            return {"access_token": "mocked-access-token"}

    def fake_post(url, headers, data, timeout):
        assert url == "https://api.upstox.com/v2/login/authorization/token"
        assert data["grant_type"] == "authorization_code"
        assert data["code"] == "abc123"
        return FakeResponse()

    monkeypatch.setattr(requests, "post", fake_post)

    token = exchange_code_for_token(
        code="abc123",
        api_key="k",
        api_secret="s",
        redirect_uri="http://127.0.0.1:8000/callback",
    )
    assert token == "mocked-access-token"