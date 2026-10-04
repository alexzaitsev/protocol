# Copyright 2026 Alex Zaitsev
# SPDX-License-Identifier: AGPL-3.0-only

from starlette.testclient import TestClient


def test_oidc_discovery_is_available(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/protocol")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("MCP_SERVER_URL", "https://family-health.fly.dev")

    from main import create_app

    response = TestClient(create_app()).get("/.well-known/openid-configuration")

    assert response.status_code == 200
    assert response.json()["issuer"].rstrip("/") == "https://family-health.fly.dev"
