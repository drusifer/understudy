# Remote MCP example

The box office from [`examples/mcp`](../mcp), served over streamable HTTP with a
token, and played by URL. `servers.json` is in the `mcpServers` shape Claude Code
reads; its `Authorization` header takes the token from `MCP_TOKEN`.

```sh
# 1. start the server (leave it running)
node examples/mcp/server.mjs --http --port 8765 --token choose-a-token

# 2. in another terminal, play it (needs TYPESAFE_API_KEY too)
MCP_TOKEN=choose-a-token bobp make run ARGS="run examples/mcp-remote"
```

`BOX_PORT` picks another port (the URL is `http://127.0.0.1:${BOX_PORT:-8765}/mcp`).
understudy never starts or stops this server; `bobp make test-live` does both for its
own run.
