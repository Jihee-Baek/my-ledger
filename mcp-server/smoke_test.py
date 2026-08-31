"""Manual end-to-end check: spawns server.py over stdio (as Claude
would) and calls a few tools through the real MCP client, so we're
verifying the actual wire protocol, not just importing the module."""

import asyncio
import sys
from pathlib import Path

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

SERVER_PY = Path(__file__).resolve().parent / "server.py"
PYTHON = sys.executable


def _text(result) -> str:
    return result.content[0].text if result.content else "(no content)"


async def call(session: ClientSession, name: str, args: dict) -> None:
    print(f"\n=== {name}({args}) ===")
    result = await session.call_tool(name, args)
    print("ERROR:" if result.is_error else "OK:", _text(result)[:500])


async def main() -> None:
    params = StdioServerParameters(command=PYTHON, args=[str(SERVER_PY)])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("=== registered tools ===")
            for t in tools.tools:
                print(f"- {t.name}: {t.description.splitlines()[0]}")

            await call(session, "get_monthly_summary", {"year": 2026, "month": 7})
            await call(session, "get_category_summary", {"year": 2026, "month": 7})
            await call(session, "get_merchant_summary", {"year": 2026, "month": 7, "limit": 3})
            await call(session, "get_merchant_summary", {"year": 2026, "month": 7, "months": 6, "limit": 3})
            await call(session, "get_spending_anomalies", {"year": 2026, "month": 7})
            await call(
                session,
                "compare_month",
                {"base_year": 2026, "base_month": 6, "target_year": 2026, "target_month": 7},
            )
            await call(session, "search_transactions", {"merchant": "스타벅스"})
            await call(session, "search_transactions", {"category": "존재안함"})
            await call(session, "get_recurring_expenses", {})
            await call(session, "get_budget_status", {"year": 2026, "month": 7})


if __name__ == "__main__":
    asyncio.run(main())
