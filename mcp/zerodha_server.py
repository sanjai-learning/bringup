import os
from pathlib import Path
from typing import Any

from kiteconnect import KiteConnect
from mcp.server.fastmcp import FastMCP


# Load secrets from mounted file if present
_SECRET_FILE = Path(os.getenv("ZERODHA_SECRET_FILE", "/run/secrets/zerodha_secret.txt"))
_ACCESS_TOKEN_FILE = Path(os.getenv("ZERODHA_ACCESS_TOKEN_FILE", "/data/zerodha_access_token"))


def _load_secrets() -> None:
    """Load Zerodha secrets from file into environment variables."""
    if _SECRET_FILE.exists():
        lines = [l.strip() for l in _SECRET_FILE.read_text().splitlines() if l.strip()]
        if lines and all("=" in l for l in lines):
            for line in lines:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())
        elif len(lines) >= 4:
            os.environ.setdefault("ZERODHA_API_KEY", lines[1])
            os.environ.setdefault("ZERODHA_API_SECRET", lines[3])

    if _ACCESS_TOKEN_FILE.exists():
        token = _ACCESS_TOKEN_FILE.read_text().strip()
        if token:
            os.environ.setdefault("ZERODHA_ACCESS_TOKEN", token)


_load_secrets()

_MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
_MCP_PORT = int(os.getenv("MCP_PORT", "8000"))

mcp = FastMCP("zerodha", host=_MCP_HOST, port=_MCP_PORT)


def _env(name: str, required: bool = True) -> str:
    value = os.getenv(name, "").strip()
    if required and not value:
        raise RuntimeError(f"Missing environment variable: {name}")
    return value


def _client(require_access_token: bool = True) -> KiteConnect:
    api_key = _env("ZERODHA_API_KEY")
    client = KiteConnect(api_key=api_key)
    if require_access_token:
        access_token = _env("ZERODHA_ACCESS_TOKEN")
        client.set_access_token(access_token)
    return client


def _safe_error(exc: Exception) -> dict[str, Any]:
    return {"ok": False, "error": str(exc)}


@mcp.tool()
def zerodha_healthcheck() -> dict[str, Any]:
    """Check whether required Zerodha environment variables are configured."""
    try:
        api_key = bool(_env("ZERODHA_API_KEY", required=False))
        api_secret = bool(_env("ZERODHA_API_SECRET", required=False))
        client_id = _env("ZERODHA_CLIENT_ID", required=False) or "LI8768"
        access_token = bool(_env("ZERODHA_ACCESS_TOKEN", required=False))
        return {
            "ok": True,
            "client_id": client_id,
            "configured": {
                "api_key": api_key,
                "api_secret": api_secret,
                "access_token": access_token,
            },
        }
    except Exception as exc:  # pragma: no cover
        return _safe_error(exc)


@mcp.tool()
def zerodha_login_url() -> dict[str, Any]:
    """Generate Zerodha login URL to obtain a request_token."""
    try:
        client = _client(require_access_token=False)
        client_id = _env("ZERODHA_CLIENT_ID", required=False) or "LI8768"
        return {
            "ok": True,
            "client_id": client_id,
            "login_url": client.login_url(),
            "next": "Complete login and use request_token with zerodha_exchange_request_token.",
        }
    except Exception as exc:
        return _safe_error(exc)


@mcp.tool()
def zerodha_exchange_request_token(request_token: str) -> dict[str, Any]:
    """Exchange request_token for access_token and return session details."""
    try:
        api_secret = _env("ZERODHA_API_SECRET")
        client = _client(require_access_token=False)
        data = client.generate_session(request_token=request_token, api_secret=api_secret)
        access_token = data.get("access_token")
        if access_token:
            # Persist token so subsequent calls can use it
            os.environ["ZERODHA_ACCESS_TOKEN"] = access_token
            _ACCESS_TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
            _ACCESS_TOKEN_FILE.write_text(access_token.strip() + "\n")
        return {
            "ok": True,
            "access_token": access_token,
            "user_id": data.get("user_id"),
            "user_name": data.get("user_name"),
            "email": data.get("email"),
        }
    except Exception as exc:
        return _safe_error(exc)


@mcp.tool()
def zerodha_profile() -> dict[str, Any]:
    """Fetch Zerodha profile for the authenticated user."""
    try:
        client = _client(require_access_token=True)
        profile = client.profile()
        return {"ok": True, "profile": profile}
    except Exception as exc:
        return _safe_error(exc)


@mcp.tool()
def zerodha_margins() -> dict[str, Any]:
    """Fetch account margins."""
    try:
        client = _client(require_access_token=True)
        return {"ok": True, "margins": client.margins()}
    except Exception as exc:
        return _safe_error(exc)


@mcp.tool()
def zerodha_holdings() -> dict[str, Any]:
    """Fetch holdings."""
    try:
        client = _client(require_access_token=True)
        return {"ok": True, "holdings": client.holdings()}
    except Exception as exc:
        return _safe_error(exc)


@mcp.tool()
def zerodha_positions() -> dict[str, Any]:
    """Fetch positions."""
    try:
        client = _client(require_access_token=True)
        return {"ok": True, "positions": client.positions()}
    except Exception as exc:
        return _safe_error(exc)


@mcp.tool()
def zerodha_quote(exchange: str, symbol: str) -> dict[str, Any]:
    """Fetch quote for a trading symbol, for example exchange='NSE', symbol='INFY'."""
    try:
        client = _client(require_access_token=True)
        instrument = f"{exchange}:{symbol}"
        quote = client.quote(instrument)
        return {"ok": True, "instrument": instrument, "quote": quote.get(instrument)}
    except Exception as exc:
        return _safe_error(exc)


if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio").strip().lower()
    mcp.run(transport=transport)
