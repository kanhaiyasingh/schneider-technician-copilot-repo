# Schneider Field Service Copilot — Demo App

A polished, end-user-facing **Streamlit** app that shows the audience *the final
product* before they build it in the notebooks. It walks through the whole
workshop arc in seven tabs:

| Tab | Shows | Lab |
|-----|-------|-----|
| 🤖 **Copilot** | The complete agent orchestrating all tools | 05 |
| 💬 **Agent** | A persona-only agent (and how it can hallucinate) | 01 |
| 🛠️ **Tools** | Function tools = live installed-base lookups | 02 |
| 📄 **File Search** | Hosted RAG over the manuals, with citations | 03 |
| 🔎 **AI Search** | Enterprise vector + semantic RAG | 04 |
| 📡 **Observability** | Every answer traced to Application Insights | 06 |
| ✅ **Evaluation** | Server-side quality scoring (relevance/coherence/fluency) | 06 |

> ⚠️ All content (manuals, serials, fault codes) is **synthetic** and for
> training only. Not affiliated with or endorsed by Schneider Electric.

---

## 1. Prerequisites

1. Complete the workshop [`setup.md`](../docs/setup.md) once — you need the same
   `.venv`, a configured `../.env`, and `az login`.
2. The **Azure AI Search index** should exist (the app can build it for you from
   the **AI Search** tab, or run **Lab 04** first).
3. For the **Observability** and **Evaluation** tabs, Application Insights must be
   connected to the project (see [`azure-setup.md`](../docs/azure-setup.md)).

## 2. Install & run

> **Important:** launch Streamlit with the workshop's **own** virtual
> environment. A bare `streamlit run app.py` uses whatever `streamlit` is first
> on your `PATH`, which may be a different environment that's missing the
> workshop libraries (you'll see `ModuleNotFoundError: No module named
> 'agent_framework_foundry'`).

From this `demo-app/` folder:

```bash
# workshop libs (once) + the app's extra libs, into the workshop venv
pip install -r ../requirements.txt
pip install -r requirements.txt

# make sure you're signed in
az login

# launch via the workshop venv's interpreter (not a bare `streamlit`)
..\..\.venv\Scripts\python.exe -m streamlit run app.py      # Windows
../../.venv/bin/python -m streamlit run app.py              # macOS/Linux
```

The app opens at **http://localhost:8501**. Keep the terminal running. If the app
detects it's in the wrong environment it will show the exact command to use
instead of crashing.

> **Tip:** run it full-screen and zoom the browser to ~110% so the audience can
> read answers easily.

## 3. First-run notes (avoid live-demo surprises)

- **Warm it up before you present.** The first call in each tab is the slowest
  (it creates a server-side agent; File Search also uploads the manuals). Click
  through every tab once *before* the audience is watching.
- **Build the index first.** On the **AI Search** tab, click
  *"① Check / build the search index"* until it says *ready* — the Copilot,
  Observability and Evaluation tabs all rely on it.
- **Evaluation takes ~1–2 minutes.** Start it, then talk through what the
  evaluators measure while it runs.
- **Reset when done.** The sidebar *"Reset & clean up agents"* button deletes the
  server-side agents and vector store this app created.

---

## 4. Suggested demo script (~12–15 minutes)

A narrative that motivates *why* each capability exists. Speak to the pain, show
the fix.

**① Hook — the problem (💬 Agent tab, ~2 min)**
> "Meet our field technician's assistant. It has a great safety-first persona…"
- Ask: *"On a MasterPact MTZ, what does fault code TU-14 mean?"*
- It answers confidently — **but it's guessing**. "It sounds authoritative, yet
  it has never seen our manuals. In the field, a wrong fault-code meaning is
  dangerous. Let's fix that."

**② Give it knowledge (📄 File Search tab, ~2 min)**
- Ask the **same** TU-14 question.
- Now it answers correctly *and cites the manual*. "Same question — but now it's
  grounded in *our* documents. Notice the citation."

**③ Scale the knowledge (🔎 AI Search tab, ~2 min)**
- Click *build the index*, then ask about **A140 on the PM8000**.
- "File Search is great for a folder of PDFs. In production, this lives in an
  enterprise **vector + semantic** search index — same cited answers, governed
  and shared across apps."

**④ Let it act (🛠️ Tools tab, ~2 min)**
- Ask: *"Check warranty and service contract for serial MTZ-0002 — does it need
  escalation?"*
- Point at the **Tool activity** panel. "It didn't guess — it *called a function*
  against our installed base and flagged this asset for escalation."

**⑤ Put it together (🤖 Copilot tab, ~2 min)**
- Ask: *"The Galaxy VS with serial GVS-0001 is throwing E07 — is it under
  warranty, and what should the technician do?"*
- Watch it call **both** an installed-base tool **and** manual search, then merge
  warranty status + the E07 procedure + safety steps. "This is the end product."

**⑥ Make it trustworthy (📡 Observability + ✅ Evaluation, ~3 min)**
- **Observability:** ask a question, show the **Trace ID**. "Every field
  interaction is an auditable trace in Application Insights — prompt, tool calls,
  latency."
- **Evaluation:** run the eval. "Before we ship, we *score* answer quality. A
  mixed result is the point — it catches weak answers before a technician does."

**Close:**
> "Everything you just saw, you'll build yourself in the next two hours — one lab
> per capability. Let's open Lab 00."

---

## 5. Architecture

The app is intentionally thin — all logic reuses the workshop's own `src/`:

```
demo-app/
├─ app.py              # Streamlit UI only (tabs, styling, rendering)
├─ copilot_backend.py  # one function per capability; imports ../src/{config,tools}.py
├─ assets/logo.svg     # custom brand mark (not the official logo asset)
└─ requirements.txt    # streamlit + pandas (on top of ../requirements.txt)
```

`copilot_backend.py` contains **no Streamlit code**, so you can smoke-test any
capability from the CLI:

```bash
python copilot_backend.py agent
python copilot_backend.py tools "List all equipment at site SITE-CHN-01."
python copilot_backend.py ai_search "What does A140 mean on the PM8000?"
```

Because it reuses `config.py` and `tools.py`, the demo and the labs always behave
identically — what the audience sees is exactly what they'll build.

---

## 6. Troubleshooting

- **`ModuleNotFoundError: No module named 'agent_framework_foundry'`** (or
  `agent_framework`) — Streamlit is running in the wrong Python environment.
  Relaunch with the workshop venv's interpreter as shown in §2
  (`..\..\.venv\Scripts\python.exe -m streamlit run app.py`), not a bare
  `streamlit run app.py`. The app now shows this instruction on screen too.
- **Blank / error in a tab** — check the terminal running Streamlit for the Python
  error. Most failures are auth (`az login` expired) or the index not built yet.
- **`403` on AI Search / File Search** — RBAC or resource firewall; see the
  troubleshooting notes in [`../docs/azure-setup.md`](../docs/azure-setup.md).
- **Observability tab errors** — Application Insights isn't connected to the
  project. Connect it (portal) or set `APPLICATIONINSIGHTS_CONNECTION_STRING`.
- **Port already in use** — run on another port:
  `streamlit run app.py --server.port 8600`.
