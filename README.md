# How to Give Ollama Agents Live Web Access With Zenrows MCP

A local Ollama agent that reads live web pages, including bot-protected ones, through the Zenrows MCP server. The model runs on your machine and never contacts the target site directly.

This repository accompanies the Zenrows article [How to Give Ollama Agents Live Web Access With Zenrows MCP](https://www.zenrows.com/blog/ollama-agents-live-web-access-zenrows-mcp).

## Features
- Connects the Zenrows MCP server to a local Ollama model over STDIO
- Runs a single-pass agent that fetches and reads protected pages
- Uses the `extract` tool for structured JSON output, with Zenrows choosing how to fetch each page
- Passes the model only the parsed fields, so the result fits a local model's context window
- Tests against a Cloudflare-fronted Indeed search and a purpose-built antibot challenge page
- Includes a control script showing what a plain HTTP request returns on the same target
- Filters invented tool arguments before they reach the MCP server
- Ships an `ollmcp` config for chatting with the same tools in the terminal, with no code

## Prerequisites
- Python 3.11 or later (ollmcp requires it)
- Node.js (the MCP server runs through `npx`)
- Ollama installed and running, with a tool-capable model such as `qwen3`
- A Zenrows API key, optional for the local MCP server: [create a free account](https://app.zenrows.com/register)

Tested with the pinned versions in `requirements.txt` on Python 3.14 and 3.15, against `qwen3:latest`.

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/ZenRows/ollama-agent-web-access-zenrows-mcp.git
cd ollama-agent-web-access-zenrows-mcp
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
```

### 3. Activate the environment

```bash
source .venv/bin/activate
```

On Windows, use `.venv\Scripts\activate`.

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Install and start Ollama

```bash
brew install ollama
brew services start ollama
ollama pull qwen3
```

## Configuration

Copy the example environment file and add your key:

```bash
cp .env.example .env
```

```
ZENROWS_API_KEY=your_zenrows_api_key
```

Copy the key from your [Zenrows dashboard](https://app.zenrows.com/settings/api-keys). Without a key, the local MCP server creates a Free account for you on its first tool call.

`zenrows-mcp.json` holds the MCP server configuration for the ollmcp bridge:

```json
{
  "mcpServers": {
    "zenrows": {
      "command": "sh",
      "args": ["-c", "set -a && . ./.env && set +a && exec npx -y @zenrows/mcp"]
    }
  }
}
```

The `sh -c` command sources `.env` into the environment before starting `npx`, so the MCP server reads `ZENROWS_API_KEY` from there. The JSON holds no secret and is committed; `.env` is not, and is excluded in `.gitignore`.

The `.env` path is relative, so run ollmcp from the project root. On Windows, replace the `command` and `args` with the [documented config](https://docs.zenrows.com/mcp/overview#local-mcp-server) (`npx -y @zenrows/mcp` with an `env` object), and keep that copy out of version control if it holds your key.

## Project structure

```
.
├── agent.py
├── cloudflare_site.py
├── without_zenrows.py
├── check_cloudflare.sh
├── zenrows-mcp.json
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

- `agent.py` runs the agent against the antibot challenge page
- `cloudflare_site.py` runs the same loop against a Cloudflare-fronted Indeed search
- `without_zenrows.py` is the control: a plain HTTP request to the antibot challenge page
- `check_cloudflare.sh` prints the target's `server` and `date` headers
- `zenrows-mcp.json` is the server config for the no-code ollmcp route

## How it works

The agent has four layers, and the model never touches the target site.

```
You ask a question
  ↓
Ollama picks the extract tool and a URL
  ↓
Zenrows MCP fetches the page, applying proxies and rendering as needed
  ↓
The model reads the parsed fields from its context and answers
```

Ollama returns tool calls but does not execute them. The script is its own MCP client: it starts the Zenrows MCP server with `npx`, calls the tool, feeds the `data` object back as a `tool` message, and asks the model again. This is a single retrieval pass, which is what the example questions need.

## Running the project

Check what is in front of the target:

```bash
sh check_cloudflare.sh
```

Chat with the Zenrows tools in the terminal, with no code:

```bash
ollmcp --servers-json zenrows-mcp.json --model qwen3:latest
```

Run the agent against the antibot challenge page:

```bash
python agent.py
```

The Cloudflare-fronted target:

```bash
python cloudflare_site.py
```

The control, for comparison:

```bash
python without_zenrows.py
```

## Output

`agent.py` and `cloudflare_site.py` print the tool call, the first 300 characters of the tool result, and the model's answer. The result is structured JSON with an `ok` flag, the extraction mode, and a `data` object holding the parsed fields: the challenge verdict and page title for `agent.py`, and the job listings for `cloudflare_site.py`.

`without_zenrows.py` prints a status code and response length. On the tested target it returned 403 and a challenge page rather than content.

## Technologies
- Python
- Ollama
- Zenrows
- Model Context Protocol
- ollmcp

## Related article

This repository accompanies the Zenrows article:

**How to Give Ollama Agents Live Web Access With Zenrows MCP**

https://www.zenrows.com/blog/ollama-agents-live-web-access-zenrows-mcp
