"""Builder for Lab 01 — Your First Technician Copilot Agent."""
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
# Lab 01 · Your First Technician Copilot Agent

**Goal:** stand up a persona-driven agent that talks like a Schneider field
service expert — safety-first, concise, and honest about what it doesn't know.

You'll learn:

1. How an **agent = model + instructions (persona)**.
2. How to invoke it with the **Responses API**.
3. How to keep **multi-turn context** with a conversation.
4. Why a persona alone isn't enough — motivating the grounding labs that follow.

> ⚠️ Synthetic training data — not affiliated with or endorsed by Schneider Electric.
"""),
    md("""
## 1. Connect
"""),
    code(BOOTSTRAP + '''
project_client = config.get_project_client()
print("Connected. Model:", config.MODEL)
'''),
    md("""
## 2. Define the persona

The **instructions** are the agent's system prompt. Our shared
`config.TECH_PERSONA` encodes the behaviours we want every technician agent to
have: **safety first (LOTO, arc-flash, stored energy), correct field
terminology, cite sources, stay in scope, and never invent fault codes.**
"""),
    code('''
print(config.TECH_PERSONA)
'''),
    md("""
## 3. Create the agent
"""),
    code('''
agent = config.create_prompt_agent(
    project_client,
    name="technician-copilot-v1",
    instructions=config.TECH_PERSONA,
)
print(f"✅ Created agent: {agent.name} (v{agent.version})")
'''),
    md("""
## 4. Ask a safety-critical question

Notice how the persona steers the model toward LOTO / stored-energy warnings.
"""),
    code('''
q1 = "I need to replace the IGBT power module on an Altivar ATV630 drive. What safety steps must I take first?"
print("👤", q1, "\\n")
print("🤖", config.ask(project_client, agent, q1))
'''),
    md("""
## 5. Multi-turn context

Fault-finding is a conversation. We create a **conversation** object and pass its
id to keep context across turns — the follow-up says "it" and the agent still
knows we mean the ATV630.
"""),
    code('''
openai_client = project_client.get_openai_client()
conversation = openai_client.conversations.create()
print("Conversation id:", conversation.id, "\\n")

turn1 = "What does fault code OCF mean on the ATV630?"
print("👤", turn1)
print("🤖", config.ask(project_client, agent, turn1, conversation_id=conversation.id), "\\n")

turn2 = "Could a shorted motor cable cause it?"
print("👤", turn2)
print("🤖", config.ask(project_client, agent, turn2, conversation_id=conversation.id))
'''),
    md("""
## 6. The gap 🔍

Ask the agent something that only lives in a **product manual** — a precise
torque spec or a rare fault code. Without grounding, it will either refuse
(good — the persona told it not to guess) or risk hallucinating.

**This gap is exactly what Labs 03–04 fix** by grounding the agent in manuals
(File Search) and enterprise data (Azure AI Search).
"""),
    code('''
q_gap = "On a MasterPact MTZ trip unit, what does fault code TU-14 mean and what is the first thing I should do?"
print("👤", q_gap, "\\n")
print("🤖", config.ask(project_client, agent, q_gap))
'''),
    md("""
## 🙌 Your turn

1. Change `config.TECH_PERSONA` (copy it into a variable here) to also ask the
   agent to **always end with a one-line "Next step:" recommendation**. Recreate
   the agent and test.
2. Ask an **out-of-scope** question (e.g. "What's the weather?") and confirm the
   agent politely declines.
"""),
    code('''
# 👉 Your experiment here.
'''),
    md("""
## Clean up
"""),
    code('''
config.delete_agent(project_client, agent)
print("🗑️  Agent deleted. On to Lab 02 — giving the agent tools.")
'''),
]

if __name__ == "__main__":
    path = save(cells, "01-first-agent.ipynb")
    print("Wrote", path)
