"""Builder for Lab 05 — The Complete Copilot (orchestrating multiple tools)."""
from nb_util import md, code, save

BOOTSTRAP = '''
import sys, warnings
from pathlib import Path

warnings.filterwarnings("ignore")  # hide experimental-feature notices for a clean lab
here = Path.cwd()
src = next((p / "src" for p in [here, *here.parents] if (p / "src" / "config.py").exists()), None)
if src and str(src) not in sys.path:
    sys.path.insert(0, str(src))

import config
'''

cells = [
    md("""
# Lab 05 · The Complete Copilot

So far each capability lived in its own agent:

- **Lab 02** — installed-base tools (warranty, site, escalation)
- **Lab 03/04** — manual knowledge (fault codes, specs, safety)

A real field question needs **both** at once:

> *"The Galaxy VS with serial GVS-0001 is throwing E07 — is it under warranty, and
> what should I do?"*

In this lab we give **one agent all the tools** and let it **orchestrate**: it
decides which tool(s) to call, in what order, and combines the results into a
single grounded answer. This is *single-agent tool orchestration* — the most
common and robust production pattern.

> 🧭 **Prerequisite:** run **Lab 04** first so the Azure AI Search index exists —
> the manual-search tool queries it.

> ⚠️ Synthetic training data — not affiliated with or endorsed by Schneider Electric.
"""),
    md("""
## 1. Assemble every capability

We combine the three installed-base function tools with a `search_product_manuals`
tool (which queries the Lab 04 index under the hood).
"""),
    code(BOOTSTRAP + '''
from tools import INSTALLED_BASE_TOOLS, search_product_manuals

ALL_TOOLS = INSTALLED_BASE_TOOLS + [search_product_manuals]
print("Copilot tools:", [t.__name__ for t in ALL_TOOLS])
'''),
    md("""
## 2. Build the orchestrating agent

Same Agent Framework pattern as Lab 02 — we just hand it the full toolset and
instructions on **when** to use each.
"""),
    code('''
from agent_framework_foundry import FoundryChatClient
from azure.identity.aio import AzureCliCredential

COPILOT_INSTRUCTIONS = config.TECH_PERSONA + """

You are the complete field copilot. You have two kinds of tools:
- Installed-base tools (lookup_asset_by_serial, list_assets_for_site,
  check_warranty_and_contract) for questions about specific equipment, sites,
  warranty, and service contracts.
- search_product_manuals for fault codes, specifications, safety, and procedures.

For a technician's request, use WHICHEVER tools are needed — often both — and
combine the results into one clear, safety-first answer. Cite the manual sections
you rely on. If an asset is out of warranty with no contract, flag that it needs
escalation.
"""

async def ask_copilot(question):
    async with AzureCliCredential(process_timeout=30) as credential:
        client = FoundryChatClient(credential=credential)
        agent = client.as_agent(
            name="schneider-complete-copilot",
            instructions=COPILOT_INSTRUCTIONS,
            tools=ALL_TOOLS,
        )
        return await agent.run(question)

print("Copilot ready.")
'''),
    md("""
## 3. A question that needs both capabilities

Watch the agent call **`lookup_asset_by_serial` / `check_warranty_and_contract`**
*and* **`search_product_manuals`**, then merge warranty status with the E07
procedure and safety guidance.
"""),
    code('''
q = ("The Galaxy VS UPS with serial GVS-0001 is throwing fault code E07. "
     "Is it still under warranty, and what should the technician do about E07?")
print("👤", q, "\\n")
print("🤖", await ask_copilot(q))
'''),
    md("""
## 4. Site triage + escalation

A broader request: review a site and flag anything needing escalation.
"""),
    code('''
q2 = ("I'm heading to site SITE-CHN-01. List the equipment there, and tell me which "
      "assets are out of warranty with no service contract so I can pre-authorize a "
      "chargeable visit.")
print("👤", q2, "\\n")
print("🤖", await ask_copilot(q2))
'''),
    md("""
## 5. Pure-knowledge question still works

The same agent answers a manual-only question without touching the installed-base
tools — orchestration means *using only what's needed*.
"""),
    code('''
q3 = "On an ATV630, what does SCF3 indicate and how should I respond?"
print("👤", q3, "\\n")
print("🤖", await ask_copilot(q3))
'''),
    md("""
## 🙌 Your turn

1. Ask a question that mixes **two products** at **two sites** (e.g. compare an
   asset's warranty at one site with a fault-code procedure for another). See how
   the agent chains multiple tool calls.
2. **Advanced:** true *multi-agent* systems route between separate specialist
   agents (e.g. a dedicated "safety officer" agent). Sketch how you'd split this
   copilot into a router + specialists, and what state each would need.
"""),
    code('''
# 👉 Your experiment here.
'''),
    md("""
## Recap

One agent, many tools, orchestrated automatically — this is your deployable
Schneider Field Service Copilot. In **Lab 06** we prove it's trustworthy with
**evaluations** and **observability**.
"""),
]

if __name__ == "__main__":
    path = save(cells, "05-complete-copilot.ipynb")
    print("Wrote", path)
