import asyncio
import sys

from conftest import INITIAL, SCRIPTS, UPDATED
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def test_mcp_stdio_round_trip(tmp_path):
    async def check():
        parameters = StdioServerParameters(
            command=sys.executable,
            args=[str(SCRIPTS / "mcp_server.py")],
            cwd=tmp_path,
        )
        async with stdio_client(parameters) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                initialized = await session.initialize()
                assert initialized.serverInfo.name == "Assumption Hunter"
                tools = {tool.name: tool for tool in (await session.list_tools()).tools}
                assert set(tools) == {
                    "get_audit_guide", "validate_audit_snapshot", "rank_audit_assumptions", "compare_audit_snapshots",
                }
                assert all(tool.annotations.readOnlyHint for tool in tools.values())
                assert {prompt.name for prompt in (await session.list_prompts()).prompts} == {"audit_assumptions"}
                prompt = await session.get_prompt("audit_assumptions")
                assert "Falsification" in prompt.messages[0].content.text or "falsification" in prompt.messages[0].content.text
                resources = {str(resource.uri): resource.uri for resource in (await session.list_resources()).resources}
                uri = resources["assumption-hunter://assets/example"]
                example = (await session.read_resource(uri)).contents[0].text
                assert example == INITIAL.read_text(encoding="utf-8")
                data = {"snapshot_json": example}
                valid = await session.call_tool("validate_audit_snapshot", data)
                assert not valid.isError and valid.structuredContent["assumption_count"] == 2
                ranked = await session.call_tool("rank_audit_assumptions", data)
                assert ranked.structuredContent["ranking"][0]["id"] == "ASM-001"
                diff = await session.call_tool("compare_audit_snapshots", {
                    "old_snapshot_json": example,
                    "new_snapshot_json": UPDATED.read_text(encoding="utf-8"),
                })
                assert diff.structuredContent["status_changed"] == ["ASM-001"]
                denied = await session.call_tool("validate_audit_snapshot", {"snapshot_json": str(INITIAL)})
                assert denied.isError
                no_traversal = await session.call_tool("get_audit_guide", {"section": "../LICENSE"})
                assert no_traversal.isError
                guide = await session.call_tool("get_audit_guide", {"section": "state"})
                assert not guide.isError and "Authorized persistence" in guide.content[0].text
                assert list(tmp_path.iterdir()) == []

    asyncio.run(asyncio.wait_for(check(), timeout=25))
