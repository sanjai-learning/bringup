# Zerodha Trading Platform — CLI Client

## Prerequisites

- Python 3.11+
- `mcp` package: `pip install "mcp[cli]>=1.10.1"`

## Setup (on inblr1pr001)

1. **Open SSH tunnel** to the platform server:

```bash
ssh -L 8000:localhost:8000 -i ~/.ssh/github_learning root@203.57.85.108
```

2. **Run commands** (in another terminal):

```bash
# Health check
python client/zerodha_client.py health

# Account data
python client/zerodha_client.py profile
python client/zerodha_client.py margins
python client/zerodha_client.py holdings
python client/zerodha_client.py positions

# Market quotes
python client/zerodha_client.py quote NSE INFY
python client/zerodha_client.py quote NSE RELIANCE
```

## Custom MCP URL

Override the default SSE URL with:

```bash
export MCP_SSE_URL=http://localhost:8000/sse
```

## How it works

The client uses SSH key authentication (no separate OAuth token needed):
- SSH tunnel provides encrypted + authenticated access
- MCP SSE endpoint is only exposed on the internal Docker network
- Your SSH key identity serves as the authentication mechanism
