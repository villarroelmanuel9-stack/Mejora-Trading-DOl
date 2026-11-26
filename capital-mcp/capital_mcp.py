#!/usr/bin/env python3
"""
Capital.com READ-ONLY MCP server.

Lets Claude (Claude Desktop) see a Capital.com account: balance, open
positions, pending orders, activity / transactions history and prices.

READ-ONLY BY DESIGN: Capital.com API keys always allow trading (there are no
read-only keys), so this server enforces it itself. The only non-GET calls it
can ever make are opening the session (POST /session) and selecting the
account (PUT /session). Any other method or path is refused before it is sent.

Configuration (environment variables, or a .env file next to this script):
    CAPITAL_API_KEY      API key (Capital.com > Settings > API integrations)
    CAPITAL_IDENTIFIER   your Capital.com login (e-mail)
    CAPITAL_PASSWORD     the custom password you set for the API key
    CAPITAL_ENV          "demo" (default) or "live"
    CAPITAL_ACCOUNT_ID   optional: account to select after login
"""
from __future__ import annotations

import logging
import os
import sys
import threading
import time
from typing import Any, Optional

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

# stdio transport: stdout belongs to the MCP protocol, log to stderr only
logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(levelname)s capital-mcp: %(message)s")
log = logging.getLogger("capital-mcp")

BASE_URLS = {
    "live": "https://api-capital.backend-capital.com",
    "demo": "https://demo-api-capital.backend-capital.com",
}
SESSION_PATH = "/api/v1/session"
SESSION_TTL = 9 * 60  # tokens expire 10 min after last use; refresh a bit earlier


class ReadOnlyViolation(RuntimeError):
    """Raised when code tries to send anything that could change the account."""


class CapitalClient:
    """Minimal Capital.com REST client that can only read."""

    def __init__(self, api_key: str, identifier: str, password: str, env: str = "demo",
                 account_id: Optional[str] = None, base_url: Optional[str] = None,
                 timeout: float = 20.0) -> None:
        env = (env or "demo").strip().lower()
        if env not in BASE_URLS:
            raise ValueError("CAPITAL_ENV must be 'demo' or 'live'")
        self.env = env
        self.base_url = (base_url or BASE_URLS[env]).rstrip("/")
        self._api_key = api_key
        self._identifier = identifier
        self._password = password
        self._account_id = account_id or None
        self._cst: Optional[str] = None
        self._sec: Optional[str] = None
        self._last_use = 0.0
        self._lock = threading.Lock()
        self._http = httpx.Client(base_url=self.base_url, timeout=timeout)

    # ── safety ────────────────────────────────────────────────────────────
    @staticmethod
    def _check_allowed(method: str, path: str) -> None:
        method = method.upper()
        if method == "GET":
            return
        if path == SESSION_PATH and method in ("POST", "PUT"):
            return
        raise ReadOnlyViolation(f"blocked {method} {path}: this connector is read-only")

    def _send(self, method: str, path: str, **kw: Any) -> httpx.Response:
        self._check_allowed(method, path)
        return self._http.request(method, path, **kw)

    # ── session ───────────────────────────────────────────────────────────
    def _login(self) -> None:
        r = self._send(
            "POST", SESSION_PATH,
            headers={"X-CAP-API-KEY": self._api_key, "Content-Type": "application/json"},
            json={"identifier": self._identifier, "password": self._password, "encryptedPassword": False},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Capital.com login failed (HTTP {r.status_code}): {_error_text(r)}")
        cst, sec = r.headers.get("CST"), r.headers.get("X-SECURITY-TOKEN")
        if not cst or not sec:
            raise RuntimeError("Capital.com login did not return session tokens")
        self._cst, self._sec, self._last_use = cst, sec, time.monotonic()
        current = (r.json() or {}).get("currentAccountId")
        if self._account_id and current and str(current) != str(self._account_id):
            s = self._send("PUT", SESSION_PATH, headers=self._auth(), json={"accountId": self._account_id})
            if s.status_code != 200:
                raise RuntimeError(f"could not select account {self._account_id}: {_error_text(s)}")
        log.info("session opened (%s)", self.env)

    def _auth(self) -> dict:
        return {"CST": self._cst or "", "X-SECURITY-TOKEN": self._sec or ""}

    def get(self, path: str, params: Optional[dict] = None) -> Any:
        """GET with automatic login, token refresh and one retry on 401."""
        with self._lock:
            if not self._cst or time.monotonic() - self._last_use > SESSION_TTL:
                self._login()
            params = {k: v for k, v in (params or {}).items() if v is not None}
            r = self._send("GET", path, headers=self._auth(), params=params)
            if r.status_code == 401:
                self._login()
                r = self._send("GET", path, headers=self._auth(), params=params)
            if r.status_code != 200:
                raise RuntimeError(f"GET {path} failed (HTTP {r.status_code}): {_error_text(r)}")
            self._last_use = time.monotonic()
            return r.json()


def _error_text(r: httpx.Response) -> str:
    try:
        body = r.json()
        return str(body.get("errorCode") or body)
    except Exception:
        return r.text[:200]


# ── formatting helpers ─────────────────────────────────────────────────────
def _account(a: dict) -> dict:
    b = a.get("balance") or {}
    return {
        "accountId": a.get("accountId"),
        "name": a.get("accountName"),
        "type": a.get("accountType"),
        "currency": a.get("currency"),
        "preferred": a.get("preferred"),
        "balance": b.get("balance"),
        "deposit": b.get("deposit"),
        "profitLoss": b.get("profitLoss"),
        "available": b.get("available"),
    }


def _position(p: dict) -> dict:
    pos, mkt = p.get("position") or {}, p.get("market") or {}
    return {
        "dealId": pos.get("dealId"),
        "instrument": mkt.get("instrumentName"),
        "epic": mkt.get("epic"),
        "direction": pos.get("direction"),
        "size": pos.get("size"),
        "openLevel": pos.get("level"),
        "bid": mkt.get("bid"),
        "offer": mkt.get("offer"),
        "upl": pos.get("upl"),
        "currency": pos.get("currency"),
        "leverage": pos.get("leverage"),
        "stopLevel": pos.get("stopLevel"),
        "profitLevel": pos.get("profitLevel"),
        "openedUTC": pos.get("createdDateUTC") or pos.get("createdDate"),
    }


def _hours_to_seconds(hours: float) -> int:
    return int(max(60, min(86400, float(hours) * 3600)))


# ── MCP server ─────────────────────────────────────────────────────────────
mcp = FastMCP("capital")
_client: Optional[CapitalClient] = None


def client() -> CapitalClient:
    global _client
    if _client is None:
        missing = [k for k in ("CAPITAL_API_KEY", "CAPITAL_IDENTIFIER", "CAPITAL_PASSWORD") if not os.getenv(k)]
        if missing:
            raise RuntimeError("missing configuration: " + ", ".join(missing))
        _client = CapitalClient(
            api_key=os.environ["CAPITAL_API_KEY"],
            identifier=os.environ["CAPITAL_IDENTIFIER"],
            password=os.environ["CAPITAL_PASSWORD"],
            env=os.getenv("CAPITAL_ENV", "demo"),
            account_id=os.getenv("CAPITAL_ACCOUNT_ID"),
            base_url=os.getenv("CAPITAL_BASE_URL"),  # tests only
        )
    return _client


@mcp.tool()
def get_account_summary() -> dict:
    """Overview of the Capital.com account: balance, available funds, open P/L and open positions."""
    c = client()
    accounts = [_account(a) for a in c.get("/api/v1/accounts").get("accounts", [])]
    positions = [_position(p) for p in c.get("/api/v1/positions").get("positions", [])]
    return {
        "environment": c.env,
        "accounts": accounts,
        "openPositions": len(positions),
        "totalUPL": round(sum(float(p["upl"] or 0) for p in positions), 2),
        "positions": positions,
    }


@mcp.tool()
def get_accounts() -> list:
    """All Capital.com accounts with balance, deposit, profit/loss and available funds."""
    return [_account(a) for a in client().get("/api/v1/accounts").get("accounts", [])]


@mcp.tool()
def get_positions() -> list:
    """Open positions: instrument, direction, size, open level, current bid/offer and unrealised P/L."""
    return [_position(p) for p in client().get("/api/v1/positions").get("positions", [])]


@mcp.tool()
def get_working_orders() -> list:
    """Pending (working) orders that have not been executed yet."""
    out = []
    for w in client().get("/api/v1/workingorders").get("workingOrders", []):
        d, m = w.get("workingOrderData") or {}, w.get("marketData") or {}
        out.append({
            "dealId": d.get("dealId"), "instrument": m.get("instrumentName"), "epic": d.get("epic"),
            "direction": d.get("direction"), "size": d.get("orderSize"), "level": d.get("orderLevel"),
            "type": d.get("orderType"), "stopDistance": d.get("stopDistance"),
            "profitDistance": d.get("profitDistance"), "createdUTC": d.get("createdDateUTC") or d.get("createdDate"),
        })
    return out


@mcp.tool()
def get_activity_history(last_hours: float = 24) -> list:
    """Trading activity (opened / closed / amended deals) in the last N hours (max 24)."""
    data = client().get("/api/v1/history/activity", {"lastPeriod": _hours_to_seconds(last_hours), "detailed": "true"})
    return data.get("activities", [])


@mcp.tool()
def get_transactions(last_hours: float = 24, type: Optional[str] = None) -> list:
    """Account transactions (TRADE, DEPOSIT, WITHDRAWAL, SWAP...) in the last N hours (max 24)."""
    data = client().get("/api/v1/history/transactions", {"lastPeriod": _hours_to_seconds(last_hours), "type": type})
    return data.get("transactions", [])


@mcp.tool()
def search_markets(term: str) -> list:
    """Find instruments by name (e.g. 'gold', 'US100') and get their epic codes."""
    data = client().get("/api/v1/markets", {"searchTerm": term})
    return [{"epic": m.get("epic"), "name": m.get("instrumentName"), "type": m.get("instrumentType"),
             "bid": m.get("bid"), "offer": m.get("offer"), "status": m.get("marketStatus")}
            for m in data.get("markets", [])[:20]]


@mcp.tool()
def get_market(epic: str) -> dict:
    """Current price snapshot of one instrument (e.g. epic 'GOLD' or 'US100')."""
    data = client().get(f"/api/v1/markets/{epic}")
    inst, snap = data.get("instrument") or {}, data.get("snapshot") or {}
    return {"epic": inst.get("epic", epic), "name": inst.get("name"), "currency": inst.get("currency"),
            "bid": snap.get("bid"), "offer": snap.get("offer"), "high": snap.get("high"), "low": snap.get("low"),
            "changePct": snap.get("percentageChange"), "status": snap.get("marketStatus"),
            "updateUTC": snap.get("updateTimeUTC") or snap.get("updateTime")}


if __name__ == "__main__":
    mcp.run(transport="stdio")
