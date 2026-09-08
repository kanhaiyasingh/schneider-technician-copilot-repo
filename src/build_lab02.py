"""Builder for Lab 02 — Giving the Agent Tools (installed-base lookups)."""
from nb_util import md, code, save

BOOTSTRAP = '''
import sys
from pathlib import Path

here = Path.cwd()
src = next((p / "src" for p in [here, *here.parents] if (p / "src" / "config.py").exists()), None)
if src and str(src) not in sys.path:
    sys.path.insert(0, str(src))

import config
'''

cells = [
    md("""
# Lab 02 · Giving the Agent Tools

A persona makes the agent *sound* right, but it can't answer questions about
**your** equipment: *"Is the UPS at the Chennai plant still under warranty?"*
That data lives in the installed-base system.

In this lab we give the copilot **function tools** — plain Python functions the
model can call — using the **Microsoft Agent Framework** (`FoundryChatClient`).
The framework runs the tool-calling loop for us: the model decides *when* to call
a tool, we execute it, and it folds the result into the answer.

You'll use three tools (already written in `src/tools.py`):

| Tool | What it does |
|---|---|
| `lookup_asset_by_serial` | Find one asset's details from its serial |
| `list_assets_for_site` | List every asset at a customer site |
| `check_warranty_and_contract` | Warranty + service-contract status, with an `escalate` flag |

> ⚠️ Synthetic training data — not affiliated with or endorsed by Schneider Electric.
"""),
    md("""
## 1. Inspect the tools

These are ordinary functions with `Annotated` type hints + Pydantic `Field`
descriptions. Those descriptions are what the model reads to decide how to call
them, so they matter as much as the code.
"""),
    code(BOOTSTRAP + '''
import json
from tools import INSTALLED_BASE_TOOLS, lookup_asset_by_serial

# Call a tool directly (no AI yet) to see its raw output.
print(json.dumps(json.loads(lookup_asset_by_serial("GVS-0001")), indent=2))
print("\\nTools available to the agent:", [t.__name__ for t in INSTALLED_BASE_TOOLS])
'''),
    md("""
## 2. Build a tool-using agent with the Agent Framework

`FoundryChatClient` reads `AI_FOUNDRY_PROJECT_ENDPOINT` + `FOUNDRY_MODEL` from the
environment and authenticates with `AzureCliCredential`. `client.as_agent(...)`
attaches our persona and tools. `await agent.run(question)` runs the full
tool-calling loop.
"""),
    code('''
from agent_framework_foundry import FoundryChatClient
from azure.identity.aio import AzureCliCredential

TECH_TOOL_INSTRUCTIONS = config.TECH_PERSONA + """

You can look up installed equipment with the provided tools. When a technician
mentions a serial number or site, USE the tools to get real warranty, contract,
and location data rather than guessing. Summarize what you find clearly.
"""

async def ask_tool_agent(question, tools=INSTALLED_BASE_TOOLS):
    async with AzureCliCredential(process_timeout=30) as credential:
        client = FoundryChatClient(credential=credential)
        agent = client.as_agent(
            name="technician-copilot-tools",
            instructions=TECH_TOOL_INSTRUCTIONS,
            tools=tools,
        )
        return await agent.run(question)

print("Agent factory ready.")
'''),
    md("""
## 3. Ask questions that require a tool call
"""),
    code('''
q1 = "Is the Galaxy VS UPS with serial GVS-0001 still under warranty, and what service plan does it have?"
print("👤", q1, "\\n")
print("🤖", await ask_tool_agent(q1))
'''),
    code('''
q2 = "What equipment is installed at site SITE-CHN-01?"
print("👤", q2, "\\n")
print("🤖", await ask_tool_agent(q2))
'''),
    md("""
## 4. The escalation signal

`check_warranty_and_contract` returns an `escalate` flag when an asset is **out of
warranty AND has no service contract**. Watch the agent surface that for
`MTZ-0002`.
"""),
    code('''
q3 = "A technician wants to book a chargeable repair for breaker MTZ-0002. Check its warranty and contract status and tell me if this needs escalation."
print("👤", q3, "\\n")
print("🤖", await ask_tool_agent(q3))
'''),
    md("""
## 🙌 Your turn

1. Ask about a **serial that doesn't exist** (e.g. `ZZZ-9999`). Confirm the agent
   reports it wasn't found instead of inventing an answer.
2. Write a **new tool** in a cell — e.g. `firmware_baseline(serial)` that returns
   just the firmware field — add it to the `tools=[...]` list, and ask a question
   that uses it.
"""),
    code('''
# 👉 Your experiment here.
'''),
    md("""
## Recap

The agent now blends **language skill** (persona) with **live data** (tools).
Next, Lab 03 grounds it in the **product manuals** so it can answer detailed
procedure and fault-code questions with citations.
"""),
]

if __name__ == "__main__":
    path = save(cells, "02-tools.ipynb")
    print("Wrote", path)
