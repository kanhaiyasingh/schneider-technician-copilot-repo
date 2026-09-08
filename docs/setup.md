# Participant setup

Follow these steps **before** the workshop (or in the first 15 minutes). By the
end you'll have a working Python environment and a green **Lab 00** check.

> If **you** are provisioning the Azure resources yourself, do
> [`azure-setup.md`](./azure-setup.md) **first**. If a facilitator already gave
> you a project endpoint and access, start here.

---

## 1. Prerequisites

| Tool | Version | Check |
|------|---------|-------|
| **Python** | 3.11 or 3.12 | `python --version` |
| **Azure CLI** | latest | `az version` |
| **Git** | any recent | `git --version` |
| **VS Code** *(recommended)* | latest | with the **Python** + **Jupyter** extensions |

You also need:
- An **Azure account** with access to the workshop's Foundry project.
- The **project endpoint** (and, if you're provisioning, the other values in
  [`../.env.sample`](../.env.sample)).

---

## 2. Get the code

```bash
git clone <this-repo-url>
cd foundry-agentic-ai-immersion/schneider-technician-copilot
```

---

## 3. Create a virtual environment & install dependencies

The workshop is pinned to exact library versions in
[`requirements.txt`](../requirements.txt).

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**macOS / Linux:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> **Tip:** register the environment as a Jupyter kernel so notebooks can select
> it:
> ```bash
> python -m ipykernel install --user --name schneider-copilot \
>   --display-name "Python (Schneider Copilot)"
> ```

---

## 4. Configure `.env`

Copy the sample and fill in your values (hints are in the file):

**Windows:**
```powershell
copy .env.sample .env
```
**macOS / Linux:**
```bash
cp .env.sample .env
```

At minimum you must set:

| Variable | Where to get it |
|----------|-----------------|
| `AI_FOUNDRY_PROJECT_ENDPOINT` | Foundry portal → project → Overview → Endpoints |
| `AZURE_OPENAI_ENDPOINT` | Same Foundry resource, `...openai.azure.com/openai/v1` |
| `AZURE_AI_MODEL_DEPLOYMENT_NAME` | Your chat deployment name (default `gpt-5.4`) |
| `EMBEDDING_MODEL_DEPLOYMENT_NAME` | Your embedding deployment (default `text-embedding-3-large`) |

Keep `.env` in **this** folder (`schneider-technician-copilot/`). The labs find
it automatically.

---

## 5. Sign in to Azure

Authentication is **keyless** (Entra ID) — no API keys anywhere.

```bash
az login
# If you belong to more than one tenant:
az login --tenant <your-tenant-id>
az account set --subscription "<your-subscription-id>"
```

Confirm you're signed in as the right identity:
```bash
az account show --query user.name -o tsv
```

---

## 6. Verify — run Lab 00

Open the notebook and run all cells:

- **VS Code:** open `labs/00-setup-check.ipynb`, pick the
  **Python (Schneider Copilot)** kernel, **Run All**.
- **Browser:** `jupyter notebook` → open `labs/00-setup-check.ipynb`.

You should see a green checklist confirming the project connection and the chat
model. If it passes, you're ready. 🎉

---

## 7. Lab order

Run the labs in order — later labs reuse artifacts from earlier ones (Lab 04
builds the Search index that Labs 05 and 06 depend on):

| # | Lab | You'll build |
|---|-----|--------------|
| 00 | `00-setup-check` | Environment validation |
| 01 | `01-first-agent` | Your first Foundry agent (persona only) |
| 02 | `02-tools` | Function tools (installed-base lookups) with the Agent Framework |
| 03 | `03-file-search` | Grounding on manuals with hosted File Search |
| 04 | `04-azure-ai-search` | Vector + semantic RAG over the manuals |
| 05 | `05-complete-copilot` | The full copilot — all tools orchestrated |
| 06 | `06-observability-and-evaluation` | Tracing + server-side evals |

> Work in the `labs/` copies (clean, no outputs). Fully-executed reference
> versions live in `solutions/` if you get stuck.

---

## Troubleshooting

- **`AI_FOUNDRY_PROJECT_ENDPOINT is not set`** — your `.env` isn't being found or
  the variable is blank. Confirm `.env` is in `schneider-technician-copilot/` and
  the value is filled in.
- **`403` / `AuthorizationFailure`** — usually RBAC not yet propagated or a
  resource firewall. Wait a few minutes, confirm `az login` identity, and see the
  troubleshooting notes in [`azure-setup.md`](./azure-setup.md).
- **Wrong kernel** — if imports fail, make sure the notebook's kernel is the
  `.venv` you installed into (bottom-right in VS Code / **Kernel** menu in
  Jupyter).
- **Model errors** — confirm the deployment names in `.env` exactly match the
  Foundry portal.
