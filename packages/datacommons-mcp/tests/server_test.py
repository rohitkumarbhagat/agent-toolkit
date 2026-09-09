# Copyright 2026 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for Data Commons MCP server resource registration."""

import asyncio
from functools import partial

import pytest
from datacommons_mcp.middleware import (
    DOCUMENTATION_INDEX_URI,
    DOCUMENTATION_RESOURCE_NAME,
    DOCUMENTATION_ROUTING_HINT,
    DocumentationMiddleware,
)
from datacommons_mcp.server import _register_documentation_resource
from fastmcp import Client, FastMCP
from fastmcp.client.transports import StreamableHttpTransport
from fastmcp.exceptions import ResourceError
from fastmcp.utilities.tests import run_server_async
from mcp import McpError


def documentation_server(enabled):
    base = "Custom server instructions.\n"
    server = FastMCP("test", instructions=base)
    server.add_middleware(
        DocumentationMiddleware(
            enabled=enabled,
            base_instructions=base,
        )
    )
    _register_documentation_resource(server)

    @server.resource("test://unrelated")
    def unrelated():
        return "unchanged"

    return server


@pytest.mark.asyncio
async def test_documentation_resource_registered_when_enabled(requests_mock):
    """The documentation resource is available when enabled."""
    documentation = "# Data Commons Documentation\n"
    requests_mock.get(DOCUMENTATION_INDEX_URI, text=documentation)
    mcp = documentation_server(enabled=True)

    async with Client(mcp) as client:
        resources = await client.list_resources()
        contents = await client.read_resource(DOCUMENTATION_INDEX_URI)

    resource = next(r for r in resources if str(r.uri) == DOCUMENTATION_INDEX_URI)
    assert str(resource.uri) == DOCUMENTATION_INDEX_URI
    assert resource.name == DOCUMENTATION_RESOURCE_NAME
    assert resource.title == "Data Commons Documentation Index"
    assert resource.description == (
        "Current Data Commons documentation index for API, client library, "
        "schema, dataset coverage, concept, and integration questions. Use this "
        "index to open only the documentation pages relevant to the question."
    )
    assert len(contents) == 1
    assert contents[0].text == documentation
    assert requests_mock.call_count == 1


@pytest.mark.asyncio
async def test_documentation_resource_not_registered_when_disabled():
    """The documentation resource can be disabled for DCP deployments."""
    mcp = documentation_server(enabled=False)

    async with Client(mcp) as client:
        resources = await client.list_resources()

    assert [str(r.uri) for r in resources] == ["test://unrelated"]


@pytest.mark.asyncio
@pytest.mark.parametrize("default", [False, True])
async def test_documentation_http_overrides(default, monkeypatch, requests_mock):
    server = documentation_server(default)
    original = server.instructions
    monkeypatch.setattr(
        server, "run_http_async", partial(server.run_http_async, stateless_http=True)
    )
    fetch = requests_mock.get(DOCUMENTATION_INDEX_URI, text="# Documentation")

    async with run_server_async(server) as url:
        # Initialization and listing must never download the index.
        async def check(header):
            enabled = default if header is None else header.lower() == "true"
            headers = {} if header is None else {"X-DC-Enable-Documentation": header}
            async with Client(StreamableHttpTransport(url, headers=headers)) as client:
                result = await client.initialize()
                expected = "Custom server instructions.\n"
                if enabled:
                    expected = f"{expected.rstrip()}\n\n{DOCUMENTATION_ROUTING_HINT}"
                assert result.instructions == expected
                for _ in range(2):
                    resources = await client.list_resources()
                    assert (
                        any(str(r.uri) == DOCUMENTATION_INDEX_URI for r in resources)
                        == enabled
                    )
                    assert (await client.read_resource("test://unrelated"))[
                        0
                    ].text == "unchanged"

        await asyncio.gather(
            *(check(value) for value in [None, "true", "false", "TRUE"])
        )
        assert fetch.call_count == 0
        for header in [None, "true", "false"]:
            enabled = default if header is None else header == "true"
            headers = {} if header is None else {"X-DC-Enable-Documentation": header}
            async with Client(StreamableHttpTransport(url, headers=headers)) as client:
                if enabled:
                    assert (await client.read_resource(DOCUMENTATION_INDEX_URI))[
                        0
                    ].text == "# Documentation"
                else:
                    with pytest.raises(
                        (ResourceError, McpError), match="Unknown resource"
                    ):
                        await client.read_resource(DOCUMENTATION_INDEX_URI)
        assert fetch.call_count == 1 + int(default)
        async with Client(
            StreamableHttpTransport(
                url, headers={"X-DC-Enable-Documentation": "invalid"}
            ),
            auto_initialize=False,
        ) as client:
            with pytest.raises(McpError, match="must be true or false") as error:
                await client.initialize()
            assert error.value.error.code == -32602
    assert server.instructions == original


@pytest.mark.parametrize(("value", "expected"), [(" TRUE ", True), (" false ", False)])
def test_documentation_header_whitespace(value, expected, monkeypatch):
    monkeypatch.setattr(
        "datacommons_mcp.middleware.get_http_headers",
        lambda: {"x-dc-enable-documentation": value},
    )
    middleware = DocumentationMiddleware(
        enabled=False,
        base_instructions="base",
    )
    assert middleware._enabled() is expected
