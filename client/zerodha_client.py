"""
Zerodha Trading Platform CLI Client.

Connects to the MCP platform server via SSE transport.
Requires SSH tunnel: ssh -L 8000:localhost:8000 root@203.57.85.108

Usage:
    python client/zerodha_client.py health
    python client/zerodha_client.py profile
    python client/zerodha_client.py margins
    python client/zerodha_client.py holdings
    python client/zerodha_client.py positions
    python client/zerodha_client.py quote NSE INFY
"""

import asyncio
import json
import os
import sys

from mcp import ClientSession
from mcp.client.sse import sse_client


MCP_SSE_URL = os.getenv("MCP_SSE_URL", "http://localhost:8000/sse")


async def call_tool(name: str, arguments: dict | None = None) -> dict:
    async with sse_client(MCP_SSE_URL) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(name, arguments or {})

            content = getattr(result, "content", None) or []
            if len(content) == 1 and getattr(content[0], "type", None) == "text":
                try:
                    return json.loads(content[0].text)
                except json.JSONDecodeError:
                    return {"raw": content[0].text}
            return {"result": str(result)}


COMMANDS = {
    "health": ("zerodha_healthcheck", None),
    "profile": ("zerodha_profile", None),
    "margins": ("zerodha_margins", None),
    "holdings": ("zerodha_holdings", None),
    "positions": ("zerodha_positions", None),
}


async def main():
    if len(sys.argv) < 2:
        print(__doc__.strip())
        sys.exit(1)

    cmd = sys.argv[1].lower()

    if cmd == "quote":
        if len(sys.argv) < 4:
            print("Usage: quote <exchange> <symbol>")
            print("Example: quote NSE INFY")
            sys.exit(1)
        exchange, symbol = sys.argv[2], sys.argv[3]
        result = await call_tool("zerodha_quote", {"exchange": exchange, "symbol": symbol})
    elif cmd in COMMANDS:
        tool_name, args = COMMANDS[cmd]
        result = await call_tool(tool_name, args)
    else:
        print(f"Unknown command: {cmd}")
        print(f"Available: {', '.join(list(COMMANDS.keys()) + ['quote'])}")
        sys.exit(1)

    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
