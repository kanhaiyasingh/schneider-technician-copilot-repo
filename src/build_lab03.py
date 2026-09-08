"""Builder for Lab 03 — Grounding on Product Manuals with File Search."""
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
# Lab 03 · Grounding on Product Manuals (File Search)

In Lab 01 the persona-only agent was asked about fault code **TU-14** and
**made up the wrong answer** (it guessed "memory/configuration fault" — the manual
actually says *ground-fault protection tripped*). That's the danger of an
ungrounded agent in the field.

Here we fix it with **File Search**: we upload the product manuals into a
**vector store**, attach it to the agent with `FileSearchTool`, and the model
retrieves the real text and **cites** it.

You'll learn to:
1. Create a vector store and upload documents.
2. Attach `FileSearchTool` to an agent.
3. Get grounded, cited answers — and see the hallucination disappear.

> ⚠️ Synthetic training data — not affiliated with or endorsed by Schneider Electric.
"""),
    md("""
## 1. Connect
"""),
    code(BOOTSTRAP + '''
project_client = config.get_project_client()
openai_client = project_client.get_openai_client()
print("Connected. Model:", config.MODEL)
'''),
    md("""
## 2. Create a vector store and upload the manuals

`upload_and_poll` uploads each file and waits for it to be chunked and embedded.
There are 4 synthetic manuals in `data/manuals/`.

> 💡 **If you hit a `403 Forbidden` here:** your account needs the
> **Storage Blob Data Contributor** role on the Foundry project's storage
> account (wait ~5-10 min after granting). This is the most common file-search
> setup issue.
"""),
    code('''
manual_paths = sorted(config.MANUALS_DIR.glob("*.md"))
print("Manuals to upload:", [p.name for p in manual_paths])

vector_store = openai_client.vector_stores.create(name="schneider-manuals")
print("📦 Vector store:", vector_store.id)

for p in manual_paths:
    f = openai_client.vector_stores.files.upload_and_poll(
        vector_store_id=vector_store.id, file=open(p, "rb")
    )
    print(f"  ✅ {p.name} -> {f.status}")
'''),
    md("""
## 3. Create a grounded agent

We attach `FileSearchTool(vector_store_ids=[...])` and instruct the agent to
**always search the manuals and cite them**.
"""),
    code('''
from azure.ai.projects.models import FileSearchTool

GROUNDED_INSTRUCTIONS = config.TECH_PERSONA + """

You have a File Search tool over the official product manuals. For any question
about fault codes, specifications, safety, or procedures, ALWAYS search the
manuals first and base your answer on what you find, citing the source. If the
manuals do not contain the answer, say so clearly.
"""

grounded_agent = config.create_prompt_agent(
    project_client,
    name="technician-copilot-grounded",
    instructions=GROUNDED_INSTRUCTIONS,
    tools=[FileSearchTool(vector_store_ids=[vector_store.id])],
)
print(f"✅ Grounded agent: {grounded_agent.name} (v{grounded_agent.version})")
'''),
    md("""
## 4. Re-ask the question that fooled Lab 01

Compare this answer to the hallucinated one from Lab 01. It should now correctly
say **TU-14 = ground-fault protection tripped**, with a manual citation.
"""),
    code('''
print("🤖", config.ask(project_client, grounded_agent,
    "On a MasterPact MTZ, what does fault code TU-14 mean and what is the first thing I should do?"))
'''),
    md("""
## 5. More grounded lookups
"""),
    code('''
for q in [
    "A Galaxy VS UPS is showing fault code E07 — what should I do first?",
    "The PM8000 is reporting A140. Is that a meter failure?",
    "How long must I wait before touching the DC bus terminals on an ATV630?",
]:
    print("👤", q)
    print("🤖", config.ask(project_client, grounded_agent, q), "\\n" + "-"*70)
'''),
    md("""
## 🙌 Your turn

1. Ask about a spec that is **not** in any manual (e.g. an exact busbar torque
   value). Confirm the grounded agent says it isn't in the manuals rather than
   inventing a number.
2. Ask a question that spans **two** products (e.g. "Which products in the manuals
   mention IGBT stages?") and see how File Search pulls from multiple documents.
"""),
    code('''
# 👉 Your experiment here.
'''),
    md("""
## Clean up

Delete the agent and the vector store so we don't leave resources behind.
"""),
    code('''
config.delete_agent(project_client, grounded_agent)
openai_client.vector_stores.delete(vector_store.id)
print("🗑️  Deleted grounded agent and vector store.")
print("Next: Lab 04 grounds on enterprise search with Azure AI Search.")
'''),
]

if __name__ == "__main__":
    path = save(cells, "03-file-search.ipynb")
    print("Wrote", path)
