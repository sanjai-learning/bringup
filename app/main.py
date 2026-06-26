import json
import os
import sys
from pathlib import Path
from typing import Any

from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from starlette.middleware.sessions import SessionMiddleware


BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))

APP_BASE_URL = os.getenv("APP_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
SESSION_SECRET = os.getenv("SESSION_SECRET", "change-me")
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
GITHUB_ALLOWED_ORG = os.getenv("GITHUB_ALLOWED_ORG", "sanjai-learning").strip()
ZERODHA_SECRET_FILE = Path(os.getenv("ZERODHA_SECRET_FILE", "/run/secrets/zerodha_secret.txt"))
ZERODHA_ACCESS_TOKEN_FILE = Path(os.getenv("ZERODHA_ACCESS_TOKEN_FILE", "/data/zerodha_access_token"))


app = FastAPI(title="Zerodha MCP Web UI")
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "app" / "static")), name="static")

oauth = OAuth()
oauth.register(
    name="github",
    client_id=GITHUB_CLIENT_ID or "missing-client-id",
    client_secret=GITHUB_CLIENT_SECRET or "missing-client-secret",
    access_token_url="https://github.com/login/oauth/access_token",
    authorize_url="https://github.com/login/oauth/authorize",
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "read:user user:email read:org"},
)


def _github_configured() -> bool:
    return bool(GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET and SESSION_SECRET and SESSION_SECRET != "change-me")


def _load_secret_values() -> dict[str, str]:
    values: dict[str, str] = {}

    if ZERODHA_SECRET_FILE.exists():
        lines = [line.strip() for line in ZERODHA_SECRET_FILE.read_text().splitlines() if line.strip()]
        if lines and all("=" in line for line in lines):
            for line in lines:
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip()
        elif len(lines) >= 4:
            values["ZERODHA_API_KEY"] = lines[1]
            values["ZERODHA_API_SECRET"] = lines[3]

    values.setdefault("ZERODHA_CLIENT_ID", os.getenv("ZERODHA_CLIENT_ID", "LI8768"))

    if ZERODHA_ACCESS_TOKEN_FILE.exists():
        token = ZERODHA_ACCESS_TOKEN_FILE.read_text().strip()
        if token:
            values["ZERODHA_ACCESS_TOKEN"] = token

    return values


def _zerodha_env() -> dict[str, str]:
    env = os.environ.copy()
    env.update(_load_secret_values())
    return env


def _set_flash(request: Request, message: str, level: str = "info") -> None:
    request.session["flash"] = {"message": message, "level": level}


def _pop_flash(request: Request) -> dict[str, str] | None:
    return request.session.pop("flash", None)


def _current_user(request: Request) -> dict[str, Any] | None:
    return request.session.get("user")


def _require_user(request: Request) -> RedirectResponse | None:
    if _current_user(request):
        return None
    _set_flash(request, "Sign in with GitHub first.", "error")
    return RedirectResponse("/", status_code=303)


def _tool_result_to_data(result: Any) -> Any:
    structured = getattr(result, "structuredContent", None)
    if structured is not None:
        return structured

    content = getattr(result, "content", None) or []
    if len(content) == 1 and getattr(content[0], "type", None) == "text":
        text = content[0].text
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"ok": False, "raw": text}

    if hasattr(result, "model_dump"):
        return result.model_dump()

    return result


async def _call_mcp_tool(name: str, arguments: dict[str, Any] | None = None) -> Any:
    server = StdioServerParameters(
        command=sys.executable,
        args=[str(BASE_DIR / "mcp" / "zerodha_server.py")],
        env=_zerodha_env(),
        cwd=str(BASE_DIR),
    )

    async with stdio_client(server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(name, arguments or {})
            return _tool_result_to_data(result)


async def _dashboard_data() -> dict[str, Any]:
    health = await _call_mcp_tool("zerodha_healthcheck")
    data: dict[str, Any] = {"health": health}

    if not health.get("configured", {}).get("access_token"):
        data["login"] = await _call_mcp_tool("zerodha_login_url")
        return data

    data["profile"] = await _call_mcp_tool("zerodha_profile")
    data["margins"] = await _call_mcp_tool("zerodha_margins")
    data["holdings"] = await _call_mcp_tool("zerodha_holdings")
    data["positions"] = await _call_mcp_tool("zerodha_positions")
    return data


async def _page_state(show_account_details: bool) -> dict[str, Any]:
    health = await _call_mcp_tool("zerodha_healthcheck")
    state: dict[str, Any] = {
        "health": health,
        "show_account_details": show_account_details,
    }

    if not health.get("configured", {}).get("access_token"):
        state["login"] = await _call_mcp_tool("zerodha_login_url")
        return state

    if show_account_details:
        state["dashboard"] = await _dashboard_data()

    return state


def _persist_access_token(access_token: str) -> None:
    ZERODHA_ACCESS_TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    ZERODHA_ACCESS_TOKEN_FILE.write_text(access_token.strip() + "\n")


@app.get("/")
async def index(request: Request):
    user = _current_user(request)
    page_state = None
    if user:
        page_state = await _page_state(show_account_details=False)

    return TEMPLATES.TemplateResponse(
        request,
        "index.html",
        {
            "user": user,
            "flash": _pop_flash(request),
            "page_state": page_state,
            "github_configured": _github_configured(),
            "app_base_url": APP_BASE_URL,
            "allowed_org": GITHUB_ALLOWED_ORG,
        },
    )


@app.get("/account-details")
async def account_details(request: Request):
    redirect = _require_user(request)
    if redirect is not None:
        return redirect

    page_state = await _page_state(show_account_details=True)

    return TEMPLATES.TemplateResponse(
        request,
        "index.html",
        {
            "user": _current_user(request),
            "flash": _pop_flash(request),
            "page_state": page_state,
            "github_configured": _github_configured(),
            "app_base_url": APP_BASE_URL,
            "allowed_org": GITHUB_ALLOWED_ORG,
        },
    )


@app.get("/login")
async def login(request: Request):
    if not _github_configured():
        _set_flash(request, "GitHub OAuth is not configured yet. Set GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, and SESSION_SECRET.", "error")
        return RedirectResponse("/", status_code=303)

    redirect_uri = f"{APP_BASE_URL}/auth/github/callback"
    return await oauth.github.authorize_redirect(request, redirect_uri)


@app.get("/auth/github/callback")
async def auth_github_callback(request: Request):
    try:
        token = await oauth.github.authorize_access_token(request)
    except OAuthError as exc:
        _set_flash(request, f"GitHub login failed: {exc.error}", "error")
        return RedirectResponse("/", status_code=303)

    user_response = await oauth.github.get("user", token=token)
    orgs_response = await oauth.github.get("user/orgs", token=token)
    user = user_response.json()
    orgs = orgs_response.json()
    org_names = {org.get("login", "") for org in orgs}

    if GITHUB_ALLOWED_ORG and GITHUB_ALLOWED_ORG not in org_names:
        _set_flash(request, f"GitHub user is not a member of {GITHUB_ALLOWED_ORG}.", "error")
        return RedirectResponse("/", status_code=303)

    request.session["user"] = {
        "login": user.get("login"),
        "name": user.get("name") or user.get("login"),
        "avatar_url": user.get("avatar_url"),
        "html_url": user.get("html_url"),
        "orgs": sorted(org_names),
    }
    _set_flash(request, "Signed in with GitHub.", "success")
    return RedirectResponse("/", status_code=303)


@app.post("/logout")
async def logout(request: Request):
    request.session.clear()
    _set_flash(request, "Signed out.", "success")
    return RedirectResponse("/", status_code=303)


@app.get("/auth/zerodha/callback")
async def zerodha_callback(request: Request, request_token: str | None = None):
    redirect = _require_user(request)
    if redirect is not None:
        return redirect

    if not request_token:
        _set_flash(request, "Missing Zerodha request_token.", "error")
        return RedirectResponse("/", status_code=303)

    result = await _call_mcp_tool("zerodha_exchange_request_token", {"request_token": request_token})
    if result.get("ok") and result.get("access_token"):
        _persist_access_token(result["access_token"])
        _set_flash(request, "Zerodha access token updated.", "success")
    else:
        _set_flash(request, result.get("error", "Failed to exchange Zerodha request token."), "error")
    return RedirectResponse("/", status_code=303)


@app.post("/zerodha/request-token")
async def zerodha_request_token(request: Request, request_token: str = Form(...)):
    redirect = _require_user(request)
    if redirect is not None:
        return redirect

    result = await _call_mcp_tool("zerodha_exchange_request_token", {"request_token": request_token})
    if result.get("ok") and result.get("access_token"):
        _persist_access_token(result["access_token"])
        _set_flash(request, "Zerodha access token updated.", "success")
    else:
        _set_flash(request, result.get("error", "Failed to exchange Zerodha request token."), "error")

    return RedirectResponse("/", status_code=303)
