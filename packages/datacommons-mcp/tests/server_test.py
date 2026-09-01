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

from types import SimpleNamespace

import pytest
from datacommons_mcp.app import DOCUMENTATION_RESOURCE_NAME
from datacommons_mcp.server import (
    DOCUMENTATION_INDEX_URI,
    _register_documentation_resource,
)
from fastmcp import Client, FastMCP


@pytest.mark.asyncio
async def test_documentation_resource_registered_when_enabled(requests_mock):
    """The documentation resource is available when enabled."""
    documentation = "# Data Commons Documentation\n"
    requests_mock.get(DOCUMENTATION_INDEX_URI, text=documentation)
    mcp = FastMCP("test")
    app = SimpleNamespace(settings=SimpleNamespace(enable_documentation_resource=True))

    _register_documentation_resource(mcp, app)

    async with Client(mcp) as client:
        resources = await client.list_resources()
        contents = await client.read_resource(DOCUMENTATION_INDEX_URI)

    assert len(resources) == 1
    resource = resources[0]
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
    mcp = FastMCP("test")
    app = SimpleNamespace(settings=SimpleNamespace(enable_documentation_resource=False))

    _register_documentation_resource(mcp, app)

    async with Client(mcp) as client:
        resources = await client.list_resources()

    assert resources == []
