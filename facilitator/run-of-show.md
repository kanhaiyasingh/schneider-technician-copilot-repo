# Run of Show — Schneider Field Service Copilot Bootcamp

**Format:** Half day · **4 hours** total (≈ 2 h instruction + demo, **2 h hands-on
labs**), interleaved.
**Audience:** beginner → intermediate developers / data & platform engineers.
**Outcome:** each participant builds a working, grounded, observable, evaluated
field-service copilot on Microsoft Foundry.

> **Golden rule:** teach a concept for a few minutes, then let them *build* it.
> Every capability has a matching lab. Keep talking to a minimum — the labs are
> the product.

---

## Room / tech checklist (T‑minus 30 min)

- [ ] Every participant has: an Azure login with the right **RBAC roles**, the
      **project endpoint**, and can reach `https://ai.azure.com`.
- [ ] Environment set up per [`docs/setup.md`](../docs/setup.md); **Lab 00 passes**
      for each attendee (do this as pre-work if possible).
- [ ] The **Azure AI Search index** is either pre-built (run Lab 04 once) or you'll
      build it live from the demo app.
- [ ] **Application Insights** connected to the project (Observability/Eval tabs).
- [ ] **Demo app** warmed up: `streamlit run app.py`, clicked through **every tab**
      once so first-call latency doesn't bite on stage. See
      [`demo-app/README.md`](../demo-app/README.md).
- [ ] Slides open (see [`slides-outline.md`](./slides-outline.md)); projector at
      110% zoom.

---

## Timeline

| Time | Block | Mode | Facilitator focus |
|------|-------|------|-------------------|
| 0:00–0:15 | **1. Welcome & the field problem** | Talk | Why a technician copilot; the cost of a wrong fault code |
| 0:15–0:30 | **2. "Wow" demo — the end product** | Demo | Run the Streamlit app end-to-end |
| 0:30–0:45 | **3. Foundry & environment orientation** | Talk + check | Concepts; confirm everyone's Lab 00 is green |
| 0:45–1:05 | **4. Lab 01 — your first agent** | 🧑‍💻 Lab | Persona agents; watch it hallucinate |
| 1:05–1:30 | **5. Lab 02 — function tools** | Teach + 🧑‍💻 Lab | Tool calling against the installed base |
| 1:30–1:40 | ☕ **Break** | — | — |
| 1:40–2:05 | **6. Lab 03 — File Search grounding** | Teach + 🧑‍💻 Lab | Vector store, citations, the hallucination fixed |
| 2:05–2:35 | **7. Lab 04 — Azure AI Search (RAG)** | Teach + 🧑‍💻 Lab | Enterprise vector + semantic retrieval |
| 2:35–3:00 | **8. Lab 05 — the complete copilot** | Teach + 🧑‍💻 Lab | Single-agent tool orchestration |
| 3:00–3:10 | ☕ **Break** | — | — |
| 3:10–3:45 | **9. Lab 06 — Trust: observability + evals** | Teach + 🧑‍💻 Lab | Tracing + server-side evaluation |
| 3:45–4:00 | **10. Wrap-up, productionization, Q&A** | Talk | Where to go next; resources |

**Hands-on total:** Labs 01–06 ≈ **2 hours** of participant build time.

---

## Block-by-block notes

### 1 · Welcome & the field problem (0:00–0:15)
- Set the scene: a technician on-site with a faulted UPS, no signal to call
  support, expensive downtime. What if an AI assistant knew the manuals *and* the
  asset's warranty?
- State the arc: "By lunch you'll have built exactly that — and made it
  trustworthy."
- Ground rules: synthetic data, keyless auth, ask questions anytime.

### 2 · "Wow" demo (0:15–0:30)
- Drive the **demo app** using the script in
  [`demo-app/README.md`](../demo-app/README.md) §4.
- Narrative beats: Agent *guesses* TU‑14 → File Search *cites* it → AI Search
  *scales* it → Tools *act* (warranty/escalation) → Copilot *combines* → Trace +
  Eval make it *trustworthy*.
- Don't explain code yet — sell the outcome. "You'll build every piece of this."

### 3 · Foundry & environment orientation (0:30–0:45)
- Concepts (keep it light): **project**, **model deployment**, **agent**,
  **tool**, **connection**, **grounding/RAG**.
- Auth model: `DefaultAzureCredential` / `az login`, **no keys**.
- Live-check: everyone opens **Lab 00** and runs it → green checklist. Fix
  stragglers now (usually RBAC propagation or wrong kernel).

### 4 · Lab 01 — first agent (0:45–1:05)
- Teach (3 min): system prompt / persona; the Responses API via `config.ask`.
- Build: run `labs/01-first-agent.ipynb`.
- **Key moment:** ask about **TU‑14**. The persona-only agent answers *confidently
  and wrongly*. Land the point: *fluent ≠ correct*. This motivates grounding.

### 5 · Lab 02 — function tools (1:05–1:30)
- Teach (5 min): tools = plain Python functions with typed args; the Agent
  Framework exposes them; the model decides when to call.
- Build: `labs/02-tools.ipynb` — lookup by serial, list site, warranty/escalation.
- Point at the **escalate** flag (out of warranty + no contract). "The model isn't
  guessing coverage — it's calling your system of record."

### ☕ Break (1:30–1:40)

### 6 · Lab 03 — File Search (1:40–2:05)
- Teach (5 min): vector store, chunking/embeddings, `FileSearchTool`, citations.
- Build: `labs/03-file-search.ipynb`.
- **Callback:** re-ask TU‑14 — now correct **and cited**. The hallucination is
  gone. Visible before/after is the teaching win.

### 7 · Lab 04 — Azure AI Search (2:05–2:35)
- Teach (7 min): why enterprise search vs. a file bundle — shared, governed,
  vector + **semantic** re-ranking. The embedding REST workaround (why it exists).
- Build: `labs/04-azure-ai-search.ipynb` — create index, chunk/embed/upload,
  `AzureAISearchTool`.
- Note: this index persists and is reused by Labs 05 & 06.

### 8 · Lab 05 — the complete copilot (2:35–3:00)
- Teach (5 min): **single-agent tool orchestration** — one agent, many tools,
  it picks what's needed. The most robust production pattern.
- Build: `labs/05-complete-copilot.ipynb`.
- Highlight the GVS‑0001 / E07 question that needs **both** warranty lookup *and*
  manual search, merged into one answer.

### ☕ Break (3:00–3:10)

### 9 · Lab 06 — Trust (3:10–3:45)
- Teach (7 min): **observability** (OpenTelemetry → App Insights; audit trail for
  a safety-critical action) and **evaluation** (server-side evaluators;
  relevance / coherence / fluency; a quality gate before shipping).
- Build: `labs/06-observability-and-evaluation.ipynb`.
- Frame the **mixed eval result** honestly: one question scores low *by design* —
  that's evaluation doing its job, catching weak answers before the field does.

### 10 · Wrap-up (3:45–4:00)
- Recap the arc in one slide: persona → tools → grounding → RAG → orchestration →
  trust.
- Productionization pointers: CI eval gates, cost/latency, human escalation,
  content safety, private networking.
- Point to the immersion repo's `hosted-agents/` and `AgentOps/` for "what's next."
- Q&A.

---

---

## Optional advanced track — Data & Trust (Labs 07–09)

The core 4-hour agenda above ends at Lab 06. Labs **07–09** are self-contained
add-ons for a **follow-on session, a second half-day, or fast finishers**. Each is
~25–35 min and assumes the Lab 04 Search index already exists. Swap them into the
timeline (e.g. in place of the wrap-up) only if the room is ahead of schedule.

| Lab | Capability | Teach focus | New prereq |
|---|---|---|---|
| **07 · Content Understanding** | Extract clean, structured data from complex PDFs *before* they hit the RAG index | Naive text-dump vs. CU: tables preserved, figures described, typed fields. "Garbage in, garbage out" for RAG. | `Cognitive Services User` on the resource |
| **08 · Guardrails** | Stack Prompt Shields + PII detection + a **custom Schneider blocklist** on the model | Defence the model can't be argued out of; policy attached to a deployment, not a prompt | `Cognitive Services Contributor`; a spare model deployment + quota |
| **09 · Red teaming** | Auto-attack the copilot and measure **Attack Success Rate** | Offence vs. defence (08) vs. measurement (06) = a repeatable safety pipeline; encoded/multilingual attacks | Red-team-supported region; Python 3.10–3.13 kernel |

**Trust story to tell (08 + 09 together):** *Guardrails build the wall; red teaming
tries to climb it; evaluation (Lab 06) measures the height.* Run all three on every
release and safety becomes a pipeline, not a hope.

**Facilitator cautions:**
- **Lab 08** creates real Azure resources (blocklist, RAI policy, a guardrailed
  deployment) and cleans them up at the end — leave the cleanup cell time to run.
- **Lab 09** scans consume model calls and a few minutes each; keep
  `num_objectives=5` and the 2-category advanced scan to stay in budget. On Windows,
  benign `UnicodeEncodeError` logging noise from PyRIT is expected.
- Both **08 and 09** need Azure prereqs the core labs don't — confirm the IT team
  provisioned them (see [`docs/azure-setup.md`](../docs/azure-setup.md)) *before* the
  session, or these labs will 403.

---

## Common stumbles & fast fixes

| Symptom | Likely cause | Fix |
|---|---|---|
| `403` on Search / file upload | RBAC not propagated, or resource firewall | Wait 5 min; confirm roles; check `defaultAction` on Search/Storage |
| `AI_FOUNDRY_PROJECT_ENDPOINT is not set` | `.env` missing / wrong folder | Copy `.env.sample`→`.env` in the workshop folder |
| Import errors in a notebook | Wrong kernel | Select the workshop `.venv` kernel |
| `Missing credentials` (embeddings) | Known `openai` 2.44 + AAD bug | Already handled by `config.embed_texts` (REST) |
| Eval shows a fail | Out-of-scope question by design | Explain it's the intended signal, not a bug |
| Traces don't appear | 1–3 min latency, or App Insights not connected | Wait; verify the project's App Insights connection |
| Lab 08 `403` on RAI/blocklist PUT | Missing `Cognitive Services Contributor`, or resource firewall | Confirm the role; blocklist-item PUTs can 500 intermittently — the lab retries |
| Lab 09 import/`AttackStrategy` error | Wrong `azure-ai-evaluation` version or Python | `pip install "azure-ai-evaluation[redteam]"`; use a Python 3.10–3.13 kernel |

## Facilitation tips
- **Timebox labs.** Show the `solutions/` copy if a table falls behind; don't let
  one blocker stall the room.
- **Pair novices.** Beginner + intermediate per machine keeps momentum.
- **Reinforce the throughline.** Every lab answers a weakness of the previous one.
- **Keep the demo app open** on a side screen as the "north star" of what they're
  assembling.
