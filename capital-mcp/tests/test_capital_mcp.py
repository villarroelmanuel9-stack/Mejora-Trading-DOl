"""Tests against a local fake Capital.com API (no real account is touched)."""
import asyncio
import importlib
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class FakeCapital(BaseHTTPRequestHandler):
    calls = []            # (method, path, headers, body)
    expire_next = False   # answer the next authorised GET with 401
    logins = 0

    def log_message(self, *a):
        pass

    def _reply(self, code, body, headers=None):
        raw = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _record(self):
        n = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(n) or b"{}") if n else {}
        FakeCapital.calls.append((self.command, self.path, dict(self.headers), body))
        return body

    def do_POST(self):
        body = self._record()
        if self.path == "/api/v1/session":
            if self.headers.get("X-CAP-API-KEY") != "KEY" or body.get("password") != "PW":
                return self._reply(401, {"errorCode": "error.invalid.details"})
            FakeCapital.logins += 1
            tok = f"T{FakeCapital.logins}"
            return self._reply(200, {"currentAccountId": "ACC1", "accounts": []},
                               {"CST": "cst-" + tok, "X-SECURITY-TOKEN": "sec-" + tok})
        self._reply(500, {"errorCode": "unexpected write"})

    def do_PUT(self):
        self._record()
        self._reply(200, {"dealingEnabled": True})

    def do_DELETE(self):
        self._record()
        self._reply(500, {"errorCode": "unexpected write"})

    def do_GET(self):
        self._record()
        tok = f"T{FakeCapital.logins}"
        if self.headers.get("CST") != "cst-" + tok or FakeCapital.expire_next:
            FakeCapital.expire_next = False
            return self._reply(401, {"errorCode": "error.invalid.session.token"})
        path = self.path.split("?")[0]
        if path == "/api/v1/accounts":
            return self._reply(200, {"accounts": [{"accountId": "ACC1", "accountName": "CFD", "accountType": "CFD",
                                                   "currency": "USD", "preferred": True,
                                                   "balance": {"balance": 1000.0, "deposit": 1000.0,
                                                               "profitLoss": -12.5, "available": 900.0}}]})
        if path == "/api/v1/positions":
            return self._reply(200, {"positions": [
                {"position": {"dealId": "D1", "direction": "BUY", "size": 0.5, "level": 3575.69, "upl": -8.25,
                              "currency": "USD", "leverage": 20, "createdDateUTC": "2026-11-26T01:20:00"},
                 "market": {"instrumentName": "Gold", "epic": "GOLD", "bid": 3574.0, "offer": 3574.3}},
                {"position": {"dealId": "D2", "direction": "SELL", "size": 1, "level": 20500, "upl": -4.25,
                              "currency": "USD"},
                 "market": {"instrumentName": "US Tech 100", "epic": "US100", "bid": 20504, "offer": 20505}}]})
        if path == "/api/v1/workingorders":
            return self._reply(200, {"workingOrders": []})
        if path == "/api/v1/history/activity":
            return self._reply(200, {"activities": [{"dealId": "D1", "type": "POSITION", "status": "ACCEPTED"}]})
        self._reply(404, {"errorCode": "not found"})


@pytest.fixture()
def mod(monkeypatch):
    srv = HTTPServer(("127.0.0.1", 0), FakeCapital)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    FakeCapital.calls, FakeCapital.logins, FakeCapital.expire_next = [], 0, False
    monkeypatch.setenv("CAPITAL_API_KEY", "KEY")
    monkeypatch.setenv("CAPITAL_IDENTIFIER", "me@example.com")
    monkeypatch.setenv("CAPITAL_PASSWORD", "PW")
    monkeypatch.setenv("CAPITAL_BASE_URL", f"http://127.0.0.1:{srv.server_address[1]}")
    monkeypatch.delenv("CAPITAL_ACCOUNT_ID", raising=False)
    import capital_mcp
    m = importlib.reload(capital_mcp)
    yield m
    srv.shutdown()


def test_summary_and_token_reuse(mod):
    s = mod.get_account_summary()
    assert s["environment"] == "demo"
    assert s["accounts"][0]["balance"] == 1000.0 and s["accounts"][0]["available"] == 900.0
    assert s["openPositions"] == 2 and s["totalUPL"] == -12.5
    p = s["positions"][0]
    assert (p["instrument"], p["direction"], p["openLevel"], p["upl"]) == ("Gold", "BUY", 3575.69, -8.25)
    mod.get_positions()
    assert FakeCapital.logins == 1  # one session reused for every call
    login = FakeCapital.calls[0]
    assert login[0] == "POST" and login[2]["X-CAP-API-KEY"] == "KEY"
    assert login[3] == {"identifier": "me@example.com", "password": "PW", "encryptedPassword": False}


def test_relogin_on_expired_session(mod):
    mod.get_accounts()
    FakeCapital.expire_next = True
    assert mod.get_positions()[1]["epic"] == "US100"
    assert FakeCapital.logins == 2


def test_history_params(mod):
    assert mod.get_activity_history(48)[0]["dealId"] == "D1"
    q = [c[1] for c in FakeCapital.calls if c[1].startswith("/api/v1/history/activity")][0]
    assert "lastPeriod=86400" in q  # capped at the API maximum (24 h)


def test_never_writes(mod):
    c = mod.client()
    for method, path in [("POST", "/api/v1/positions"), ("DELETE", "/api/v1/positions/D1"),
                         ("PUT", "/api/v1/positions/D1"), ("POST", "/api/v1/workingorders"),
                         ("DELETE", "/api/v1/session"), ("PUT", "/api/v1/accounts/preferences")]:
        with pytest.raises(mod.ReadOnlyViolation):
            c._send(method, path)
    mod.get_account_summary()
    mod.get_working_orders()
    writes = [(m, p) for m, p, *_ in FakeCapital.calls if m != "GET"]
    assert writes == [("POST", "/api/v1/session")]


def test_account_selection(mod, monkeypatch):
    monkeypatch.setenv("CAPITAL_ACCOUNT_ID", "ACC2")
    mod._client = None
    mod.get_accounts()
    assert ("PUT", "/api/v1/session") in [(m, p) for m, p, *_ in FakeCapital.calls]
    assert [b for m, p, h, b in FakeCapital.calls if m == "PUT"][0] == {"accountId": "ACC2"}


def test_bad_password(mod, monkeypatch):
    monkeypatch.setenv("CAPITAL_PASSWORD", "wrong")
    mod._client = None
    with pytest.raises(RuntimeError, match="login failed"):
        mod.get_accounts()


def test_missing_config(mod, monkeypatch):
    monkeypatch.delenv("CAPITAL_API_KEY")
    mod._client = None
    with pytest.raises(RuntimeError, match="CAPITAL_API_KEY"):
        mod.get_accounts()


def test_only_read_tools_exposed(mod):
    names = sorted(t.name for t in asyncio.run(mod.mcp.list_tools()))
    assert names == ["get_account_summary", "get_accounts", "get_activity_history", "get_market",
                     "get_positions", "get_transactions", "get_working_orders", "search_markets"]
