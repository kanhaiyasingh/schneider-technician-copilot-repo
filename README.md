# Schneider Field Service Copilot — a Microsoft Foundry bootcamp

A **half-day, hands-on workshop** that builds an AI **field-service copilot** for
on-site technicians who service industrial electrical equipment (UPS, power
meters, variable speed drives, air circuit breakers). You'll go from a bare model
to a **grounded, tool-using, observable, evaluated** copilot on **Microsoft
Foundry** — one capability per lab.

> ⚠️ **All content is synthetic.** The product manuals, serial numbers, sites,
> fault codes, and warranty records are fabricated for training only. This
> workshop is **not affiliated with or endorsed by Schneider Electric.**

---

## What you'll build

A copilot that can:
- Speak with a **safety-first field-technician persona** (LOTO, arc-flash, DC bus).
- **Look up your installed base** — asset by serial, a site's equipment, warranty
  & service-contract status, and flag cases needing **escalation**.
- **Ground answers in the product manuals** with citations (fault codes, specs,
  procedures) — no hallucinated fault codes.
- **Orchestrate all of the above** in a single agent.
- Be **trustworthy**: every answer is **traced** to Application Insights and the
  copilot is **scored** by server-side evaluations.
- **Extract clean, structured data from complex PDFs** with Content Understanding
  before they ever reach the search index — fixing the front of the RAG pipeline.

Audience: **beginner → intermediate**. Duration: **4 hours** (~2 h teaching/demo +
**2 h hands-on labs**).

---

## The labs

Run them **in order** — each fixes a weakness of the previous one, and later labs
reuse earlier artifacts (Lab 04 builds the Search index used by Labs 05 & 06).

| # | Lab | Capability | You build |
|---|-----|-----------|-----------|
| 00 | [`labs/00-setup-check.ipynb`](labs/00-setup-check.ipynb) | Environment | Validate project, model, auth |
| 01 | [`labs/01-first-agent.ipynb`](labs/01-first-agent.ipynb) | **Agent** | A persona agent (and see it hallucinate) |
| 02 | [`labs/02-tools.ipynb`](labs/02-tools.ipynb) | **Function tools** | Installed-base lookups + escalation |
| 03 | [`labs/03-file-search.ipynb`](labs/03-file-search.ipynb) | **File Search** | Hosted RAG over the manuals, cited |
| 04 | [`labs/04-azure-ai-search.ipynb`](labs/04-azure-ai-search.ipynb) | **Azure AI Search** | Enterprise vector + semantic RAG |
| 05 | [`labs/05-complete-copilot.ipynb`](labs/05-complete-copilot.ipynb) | **Orchestration** | One agent, all tools |
| 06 | [`labs/06-observability-and-evaluation.ipynb`](labs/06-observability-and-evaluation.ipynb) | **Trust** | Tracing + server-side evals |
| 07 | [`labs/07-document-extraction.ipynb`](labs/07-document-extraction.ipynb) | **Content Understanding** *(advanced)* | Extract clean data from complex PDFs before ingestion |
| 08 | [`labs/08-guardrails.ipynb`](labs/08-guardrails.ipynb) | **Guardrails** *(trust)* | Prompt Shields + PII + a custom Schneider blocklist |
| 09 | [`labs/09-red-teaming.ipynb`](labs/09-red-teaming.ipynb) | **Red teaming** *(trust)* | Auto-attack the copilot and measure Attack Success Rate |

Fully-executed reference versions live in [`solutions/`](solutions/) if you get
stuck.

---

## Repository layout

```
schneider-technician-copilot/
├─ README.md                 # you are here
├─ requirements.txt          # pinned Python deps for the labs
├─ .env.sample               # copy to .env and fill in (hints inside)
├─ labs/                     # the 10 teaching notebooks (clean, run these)
├─ solutions/                # executed reference notebooks (with outputs)
├─ src/                      # shared code the labs + app import
│  ├─ config.py              #   clients, auth, persona, embeddings, search
│  ├─ tools.py               #   installed-base function tools + manual search
│  ├─ data_gen.py            #   deterministic synthetic-data generator
│  ├─ nb_util.py             #   notebook builder helpers
│  └─ build_lab0*.py         #   notebook generators (authoring)
├─ data/                     # synthetic corpus
│  ├─ manuals/               #   4 product manuals (Galaxy VS, MTZ, PM8000, ATV630)
│  ├─ installed_base.json    #   15 assets across 3 sites
│  └─ eval/technician_qa.jsonl #  ground-truth Q&A for evaluation
├─ demo-app/                 # Streamlit showcase app (the "wow" before labs)
│  ├─ app.py, copilot_backend.py, requirements.txt, README.md
│  └─ assets/logo.svg
├─ docs/
│  ├─ setup.md               # participant local setup
│  └─ azure-setup.md         # provisioning Azure resources
└─ facilitator/
   ├─ run-of-show.md         # minute-by-minute agenda
   └─ slides-outline.md      # deck outline
```

---

## Getting started

### 1. Provision Azure (facilitator / self-service)
Follow [`docs/azure-setup.md`](docs/azure-setup.md): a **Foundry** resource +
project, a **chat** model (`gpt-5.4`) and **embedding** model
(`text-embedding-3-large`), an **Azure AI Search** service, an **Application
Insights** resource, and the **RBAC** roles that make keyless auth work.

### 2. Set up your machine (participants)
Follow [`docs/setup.md`](docs/setup.md):
```bash
python -m venv .venv && .venv\Scripts\activate      # Windows
pip install -r requirements.txt
copy .env.sample .env                                # then fill in the values
az login
```
Open `labs/00-setup-check.ipynb` → **Run All** → you should see a green checklist.

### 3. (Facilitators) Show the demo app first
The [`demo-app/`](demo-app/) is a branded Streamlit app that demonstrates the
**finished** copilot across seven tabs — a "wow" moment before participants build
it. See [`demo-app/README.md`](demo-app/README.md) for the run + demo script.

---

## Prerequisites at a glance

- **Python 3.11 or 3.12**, Azure CLI, Git (VS Code + Python/Jupyter recommended).
- An Azure account with access to the workshop's Foundry project and these roles:
  **Azure AI User**, **Cognitive Services OpenAI User**, **Search Index Data
  Contributor**, **Search Service Contributor** (+ **Storage Blob Data
  Contributor** for File Search).
- **Keyless auth only** — `az login`, no API keys in code or `.env`.

---

## Facilitator materials

- [`facilitator/why-this-use-case.md`](facilitator/why-this-use-case.md) — the
  customer-facing rationale: why **C5 — Elevate Technician Support** was chosen
  over Schneider's other candidates (C1–C7). Good pre-read / opening slide.
- [`facilitator/run-of-show.md`](facilitator/run-of-show.md) — the 4-hour agenda,
  block-by-block notes, and a stumbles-and-fixes table.
- [`facilitator/slides-outline.md`](facilitator/slides-outline.md) — a ~28-slide
  deck outline mapped to the run of show.

---

## Notes & conventions

- **Notebooks in `labs/` are the product** — teaching copies with clean cells.
  They're generated from `src/build_lab*.py` (authoring), so edit the builders and
  regenerate rather than hand-editing notebook JSON.
- **Shared code, one source of truth.** Labs *and* the demo app import
  `src/config.py` and `src/tools.py`, so what the audience sees in the demo is
  exactly what they build.
- **Fast-moving SDKs are pinned.** Keep `requirements.txt` versions exact — Foundry
  SDKs are pre-release and bumping them is likely to break the labs.
- **Troubleshooting:** most `403` errors here are **RBAC propagation or resource
  networking**, not code. See the troubleshooting sections in
  [`docs/azure-setup.md`](docs/azure-setup.md) and
  [`docs/setup.md`](docs/setup.md).

---

## Where to go next

After the copilot works, explore productionization in the parent
`foundry-agentic-ai-immersion` repo: `hosted-agents/` (azd-deployed container
agents) and `AgentOps/` (GitOps CI/CD with evaluation gates).
