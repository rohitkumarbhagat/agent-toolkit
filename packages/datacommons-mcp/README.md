# Data Commons MCP Server

This is a Model Context Protocol (MCP) server for fetching public statistical data from [Data Commons](https://datacommons.org) instances.

Data Commons is an open knowledge repository that provides a unified view across multiple public data sets and statistics.  This server allows any MCP-enabled agent or client to query the Data Commons knowledge graph.

## Features
* **MCP-Compliant:** Implements the Model Context Protocol for seamless agent integration.
* **Data Commons Access:** Fetches public statistics and data from the base datacommons.org knowledge graph.
* **Custom Instance Support:** Can be configured to work with Custom Data Commons instances.
* **Flexible Serving:** Runs over both streamable HTTP and stdio.

## Quickstart

### Prerequisites

1.  You must have a Data Commons API key; create one at [apikeys.datacommons.org](https://apikeys.datacommons.org/).
2.  Install `uv` by following the [official installation instructions](https://docs.astral.sh/uv/getting-started/installation).

### Configuration

Set the following required environment variable in your shell:

```
export DC_API_KEY=<your API key>
```

### Enable Local Reranking

Local reranking is optional and is disabled by default.

If you are running from a source checkout, install the optional reranker
dependency:

```bash
uv sync --package datacommons-mcp --extra rerank
```

Enable reranking with exactly one source:

Option 1: use a model id

```bash
export DC_ENABLE_RERANKING=true
export DC_RERANK_MODEL=mixedbread-ai/mxbai-rerank-base-v1
export DC_RERANK_CANDIDATE_LIMIT=50
export DC_RERANK_BATCH_SIZE=16
```

Option 2: use a local model directory

```bash
export DC_ENABLE_RERANKING=true
export DC_RERANK_MODEL_PATH=/models/mxbai-rerank-base-v1
export DC_RERANK_CANDIDATE_LIMIT=50
export DC_RERANK_BATCH_SIZE=16
```

To download the model locally ahead of time from the workspace root:

```bash
uv run --package datacommons-mcp python \
  packages/datacommons-mcp/scripts/download_reranker.py \
  --output-dir /models/mxbai-rerank-base-v1
```

Or from the package directory:

```bash
cd packages/datacommons-mcp
uv run python scripts/download_reranker.py \
  --output-dir models/mxbai-rerank-base-v1
```

Then point the MCP server at that local directory:

```bash
export DC_RERANK_MODEL_PATH=/models/mxbai-rerank-base-v1
```

Notes:

- set only one of `DC_RERANK_MODEL` or `DC_RERANK_MODEL_PATH`
- if neither is set, the default model id is `mixedbread-ai/mxbai-rerank-base-v1`
- startup logs clearly whether the reranker was loaded from a `model id` or `local path`
- `DC_RERANK_CANDIDATE_LIMIT` controls how many initial candidates are reranked
- `DC_RERANK_BATCH_SIZE` controls local inference batch size
- if reranking is enabled but the reranker dependencies are not installed, server
  startup will fail fast

If you are using `uvx`, install/run the package with the rerank extra:

```bash
uvx --from 'datacommons-mcp[rerank]' datacommons-mcp serve stdio
```

### Start the server 

Run the server from your command line in one of two modes:

**Streamable HTTP**

This runs the server with Streamable HTTP.

```bash
# Runs on default port 8080
uvx datacommons-mcp serve http [--port <PORT>]
```

The server will be available at `http://localhost:<port>/mcp`.

**stdio**

This transport mode is intended for local integrations and is programmatically configured within a client (like Gemini CLI settings) to communicate over `stdio`.

```bash
uvx datacommons-mcp serve stdio
```

### Test Locally Without An LLM

You do not need to wire the server to an LLM client to smoke test it.

Option 1: run the HTTP server and check health

```bash
uv run datacommons-mcp serve http --host 0.0.0.0 --port 8080
curl http://localhost:8080/mcp/health
```

Option 2: use MCP Inspector against stdio

```bash
export DC_API_KEY=<your API key>
npx @modelcontextprotocol/inspector uv run datacommons-mcp serve stdio
```

The inspector lets you connect to the MCP server and invoke tools manually
without configuring an LLM.

## Clients

You can use any MCP-enabled agent or client to connect to your running server. For example, see the [Data Commons MCP documentation](https://github.com/datacommonsorg/agent-toolkit/blob/main/docs/user_guide.md) for guides on connecting:
* [Google Gemini CLI](https://github.com/datacommonsorg/agent-toolkit/blob/main/docs/quickstart.md)
* [Google ADK natively](https://github.com/datacommonsorg/agent-toolkit/blob/main/docs/user_guide.md#use-the-sample-agent)
* [Google ADK in Colab](https://colab.research.google.com/github/datacommonsorg/agent-toolkit/blob/main/notebooks/datacommons_mcp_tools_with_custom_agent.ipynb)

Or see your preferred client's documentation for how to configure it, using the commands listed above.

## Advanced Configuration
### Using MCP Tools with a Custom Data Commons

Follow the [Guide for using MCP Tools with Custom Data Commons](https://github.com/datacommonsorg/agent-toolkit/blob/main/docs/user_guide.md#custom-data-commons) to set additional environment variables required for custom configuration.

## Testing

If you are developing from this repo checkout, install test dependencies:

```bash
uv sync --package datacommons-mcp --extra test
```

To run the MCP package tests from this directory:

```bash
PYTHONPATH=../../../api-python uv run pytest tests/test_dc_client.py tests/test_services.py
```

To run tests with reranker support installed:

```bash
uv sync --package datacommons-mcp --extra test --extra rerank
PYTHONPATH=../../../api-python uv run pytest tests/test_dc_client.py tests/test_services.py
```

If your environment auto-loads incompatible pytest plugins, run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=../../../api-python uv run pytest tests/test_dc_client.py tests/test_services.py
```
