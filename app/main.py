import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from mcp import ClientSession
from mcp.client.sse import sse_client


BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))

MCP_SSE_URL = os.getenv("MCP_SSE_URL", "http://platform-mcp:8000/sse")
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://127.0.0.1:3000").rstrip("/")


app = FastAPI(title="Zerodha Trading Platform")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "app" / "static")), name="static")


def _get_user(request: Request) -> dict[str, str]:
    """Extract user info from OAuth2 Proxy forwarded headers."""
    email = request.headers.get("X-Forwarded-Email", "")
    user = request.headers.get("X-Forwarded-User", "")
    preferred = request.headers.get("X-Forwarded-Preferred-Username", user)
    return {"login": preferred or user, "email": email, "name": preferred or user}


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
    async with sse_client(MCP_SSE_URL) as (read_stream, write_stream):
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


@app.get("/")
async def index(request: Request):
    user = _get_user(request)
    health = await _call_mcp_tool("zerodha_healthcheck")
    page_state: dict[str, Any] = {"health": health, "show_account_details": False}

    if not health.get("configured", {}).get("access_token"):
        page_state["login"] = await _call_mcp_tool("zerodha_login_url")

    return TEMPLATES.TemplateResponse(
        request,
        "index.html",
        {
            "user": user,
            "page_state": page_state,
            "app_base_url": APP_BASE_URL,
        },
    )


@app.get("/account-details")
async def account_details(request: Request):
    user = _get_user(request)
    dashboard = await _dashboard_data()
    page_state: dict[str, Any] = {
        "health": dashboard.get("health", {}),
        "show_account_details": True,
        "dashboard": dashboard,
    }

    if not dashboard.get("health", {}).get("configured", {}).get("access_token"):
        page_state["login"] = dashboard.get("login")

    return TEMPLATES.TemplateResponse(
        request,
        "index.html",
        {
            "user": user,
            "page_state": page_state,
            "app_base_url": APP_BASE_URL,
        },
    )


@app.post("/zerodha/request-token")
async def zerodha_request_token(request: Request, request_token: str = Form(...)):
    result = await _call_mcp_tool("zerodha_exchange_request_token", {"request_token": request_token})
    # Redirect back with status shown on page
    return RedirectResponse("/account-details", status_code=303)


@app.get("/auth/zerodha/callback")
async def zerodha_callback(request: Request, request_token: str | None = None):
    if not request_token:
        return RedirectResponse("/", status_code=303)
    await _call_mcp_tool("zerodha_exchange_request_token", {"request_token": request_token})
    return RedirectResponse("/account-details", status_code=303)
