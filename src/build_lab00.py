"""Builder for Lab 00 — Environment & Foundry Connectivity Check."""
from nb_util import md, code, save

BOOTSTRAP = '''
# Put the workshop's src/ on the path so we can import our shared helpers.
import sys
from pathlib import Path

here = Path.cwd()
src = next((p / "src" for p in [here, *here.parents] if (p / "src" / "config.py").exists()), None)
if src and str(src) not in sys.path:
    sys.path.insert(0, str(src))

import config
print("workshop src:", src)
'''

cells = [
    md("""
# Lab 00 · Setup & Connectivity Check

**Field Service Technician Copilot — Schneider Electric Foundry Bootcamp**

Before we build anything, let's confirm your environment can reach Azure AI
Foundry. By the end of this 10-minute check you will have:

- ✅ Loaded the workshop configuration from the repo-root `.env`
- ✅ Authenticated to Foundry with `az login` (Entra ID — no API keys)
- ✅ Made a live round-trip to your deployed model

> ⚠️ **Disclaimer** — All equipment names, fault codes, manuals, and asset data
> in this workshop are **synthetic** and created for training purposes only. They
> are **not** official Schneider Electric documentation and are not affiliated
> with or endorsed by Schneider Electric.
"""),
    md("""
## 1. Load configuration

`config.py` walks up the folder tree to find the repository-root `.env`, then
exposes the endpoint, model, and data paths every lab shares.
"""),
    code(BOOTSTRAP + '''
print("Project endpoint :", config.PROJECT_ENDPOINT[:40] + "..." if config.PROJECT_ENDPOINT else "(missing!)")
print("Chat model       :", config.MODEL)
print("Embedding model  :", config.EMBEDDING_MODEL)
print("Search endpoint  :", config.SEARCH_ENDPOINT or "(not set)")
print("Manuals dir      :", config.MANUALS_DIR)

assert config.PROJECT_ENDPOINT, "AI_FOUNDRY_PROJECT_ENDPOINT is empty — check the repo-root .env"
print("\\n✅ Configuration loaded.")
'''),
    md("""
## 2. Authenticate & connect

We authenticate with **`AzureCliCredential`**, which reuses your `az login`
session. If the next cell fails with an auth error, open a terminal and run:

```bash
az login
```
"""),
    code('''
project_client = config.get_project_client()
print("✅ AIProjectClient created for:", config.PROJECT_ENDPOINT.split("/api/")[0])
'''),
    md("""
## 3. Live round-trip

We create a throwaway agent, ask it one question, then delete it — proving the
full create → invoke → clean-up loop works end to end.
"""),
    code('''
agent = config.create_prompt_agent(
    project_client,
    name="setup-check-agent",
    instructions="You are a connectivity probe. Reply with the single word: READY.",
)
print(f"Created probe agent: {agent.name} (v{agent.version})")

reply = config.ask(project_client, agent, "Are you online?")
print("Model replied:", reply.strip())

config.delete_agent(project_client, agent)
print("🗑️  Probe agent deleted.")
print("\\n🎉 Environment is ready. Continue to Lab 01.")
'''),
    md("""
## 4. (Optional) Content Understanding — only for Lab 07

**Lab 07 (advanced)** uses **Azure AI Content Understanding** to extract clean data
from complex PDFs. It runs on the *same* Foundry resource — no separate resource
needed. This check is **optional and non-blocking**: if you're not doing Lab 07,
you can skip it. It confirms the CU endpoint is reachable with your `az login`
token and that your resource speaks the GA API version.

Lab 07 also needs two model deployments on this resource:
**`gpt-4.1-mini`** and **`text-embedding-3-large`**.
"""),
    code('''
import os, requests
import cu  # workshop CU client (src/cu.py)

cu_endpoint = (
    os.environ.get("AZURE_CONTENT_UNDERSTANDING_ENDPOINT")
    or config.PROJECT_ENDPOINT.split("/api/projects/")[0]
)
try:
    cu_client = cu.ContentUnderstandingClient(cu_endpoint)
    probe_url = f"{cu_endpoint.rstrip('/')}/contentunderstanding/analyzers?api-version={cu_client._api_version}"
    resp = requests.get(probe_url, headers=cu_client._headers, timeout=60)
    if resp.status_code == 200:
        prebuilt = [a.get("analyzerId") for a in resp.json().get("value", [])]
        print("✅ Content Understanding reachable at:", cu_endpoint)
        print("   API version:", cu_client._api_version)
        print(f"   {len(prebuilt)} prebuilt analyzers available "
              f"(incl. prebuilt-documentSearch: {'prebuilt-documentSearch' in prebuilt}).")
        print("   ➡️  Ready for Lab 07. Ensure gpt-4.1-mini + text-embedding-3-large are deployed.")
    else:
        print(f"⚠️  CU returned HTTP {resp.status_code} — {resp.text[:200]}")
        print("   This only affects Lab 07. See docs/lab07-content-understanding.md.")
except Exception as exc:
    print("ℹ️  Content Understanding check skipped (only needed for Lab 07):")
    print("   ", str(exc)[:300])
    print("   See docs/lab07-content-understanding.md for provisioning help.")
'''),
    md("""
## ✅ Success criteria

You should have seen the model reply (something like `READY`) and the probe
agent get deleted.

### Troubleshooting

| Symptom | Fix |
|---|---|
| `AI_FOUNDRY_PROJECT_ENDPOINT is empty` | Copy `.env.example` → `.env` at the repo root and fill it in. |
| `Failed to invoke the Azure CLI` / auth error | Run `az login` in a terminal, then re-run the cell. |
| `403` / `PermissionDenied` | Your account needs the **Azure AI User** role on the Foundry project. |
| CU check shows `403` / `404` (Lab 07 only) | Need the **Cognitive Services User** role, or your region/resource lacks the GA API — see `docs/lab07-content-understanding.md`. |
"""),
]

if __name__ == "__main__":
    path = save(cells, "00-setup-check.ipynb")
    print("Wrote", path)
