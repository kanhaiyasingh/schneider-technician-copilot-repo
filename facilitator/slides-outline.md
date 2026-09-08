# Slides Outline — Schneider Field Service Copilot Bootcamp

A build-along deck for the half-day workshop. **~28 slides**, mapped to the
[`run-of-show.md`](./run-of-show.md). Keep slides sparse — the labs carry the
detail. Suggested speaker notes are in *italics*.

> Design: Schneider green (`#3DCD58`) accents on a dark deck; one idea per slide;
> lots of diagrams, little text. Mark every data slide "Synthetic data — not
> affiliated with Schneider Electric."

---

## Section A — Framing (Block 1)

**1. Title**
- *Schneider Field Service Copilot — build an AI assistant for on-site technicians.*
- Microsoft Foundry × Schneider Electric bootcamp · half day.

**1b. Why this use case (rationale)**
- Why **C5 — Elevate Technician Support** over Schneider's other candidates (C1–C7):
  capability-complete, safety-critical, a "superset" learning path.
- *See [`why-this-use-case.md`](./why-this-use-case.md); use as an opening slide
  or pre-read for the customer.*

**2. The field problem**
- Technician on-site, UPS faulted, downtime is expensive, docs are scattered.
- *"A wrong fault-code guess isn't just unhelpful — it's a safety risk."*

**3. What you'll build today**
- One screenshot of the finished copilot answering an E07 question with a citation
  and warranty status.
- *"By the end, this is yours — grounded, observable, evaluated."*

**4. The learning arc (the throughline)**
- Persona → Tools → Grounding → Enterprise RAG → Orchestration → Trust.
- *Each step fixes a weakness of the last. Return to this slide between labs.*

## Section B — The demo (Block 2)

**5. Meet the copilot (demo slide)**
- Just a title + "Watch." Switch to the live **demo app**.
- *Run the demo script; don't show code yet — sell the outcome.*

**6. Under the hood (teaser)**
- Simple box diagram: Model + Persona + Tools + Search index + Tracing/Eval.
- *"Six building blocks. We'll build each one."*

## Section C — Foundry orientation (Block 3)

**7. Microsoft Foundry in one slide**
- Project · model deployment · agent · tool · connection.

**8. Grounding / RAG in one slide**
- Question → retrieve relevant text → answer *from that text* → cite.
- *Contrast with "the model just knows" (it doesn't, for your manuals).*

**9. Keyless auth**
- `az login` → `DefaultAzureCredential`. No keys in code. RBAC roles table.

**10. Environment check**
- "Open Lab 00 → Run All → green?" Troubleshooting one-liners.

## Section D — Lab 01: Agent (Block 4)

**11. Anatomy of an agent**
- Model + instructions (persona). The safety-first technician persona.

**12. Lab 01 — build it** 🧑‍💻
- File: `labs/01-first-agent.ipynb`. What to notice.

**13. The hallucination**
- Screenshot: persona agent's *wrong* TU‑14 answer.
- *"Fluent ≠ correct. Hold this thought — we fix it in two labs."*

## Section E — Lab 02: Tools (Block 5)

**14. Tools = the agent can act**
- Function tool = typed Python fn; model decides when to call.

**15. Our installed-base tools**
- `lookup_asset_by_serial`, `list_assets_for_site`, `check_warranty_and_contract`
  → the **escalate** flag.

**16. Lab 02 — build it** 🧑‍💻
- File: `labs/02-tools.ipynb`. Watch the tool-activity.

## Section F — Lab 03: File Search (Block 6)

**17. Grounding with File Search**
- Vector store → chunk + embed → `FileSearchTool` → citations.

**18. Lab 03 — build it** 🧑‍💻
- File: `labs/03-file-search.ipynb`.

**19. Before / after**
- Side-by-side: Lab 01 wrong TU‑14 vs. Lab 03 correct + cited.
- *The visible payoff of grounding.*

## Section G — Lab 04: Azure AI Search (Block 7)

**20. Why enterprise search?**
- Shared, governed, vector + **semantic** re-ranking; scales past a file bundle.

**21. Index anatomy**
- Fields, HNSW vector profile, semantic config. 3072-dim embeddings.

**22. Lab 04 — build it** 🧑‍💻
- File: `labs/04-azure-ai-search.ipynb`. (This index is reused in Labs 05 & 06.)

## Section H — Lab 05: Complete copilot (Block 8)

**23. Single-agent tool orchestration**
- One agent, all tools; it chooses what's needed and merges results.
- *The most common, most robust production pattern.*

**24. Lab 05 — build it** 🧑‍💻
- File: `labs/05-complete-copilot.ipynb`. The GVS‑0001 / E07 "needs both" moment.

## Section I — Lab 06: Trust (Block 9)

**25. Observability**
- OpenTelemetry span → Application Insights. Prompt, tool calls, latency = audit
  trail for a safety-critical action.

**26. Evaluation**
- Server-side evaluators: relevance · coherence · fluency. A quality gate.
- *A mixed result is the point — it catches weak answers before the field does.*

**27. Lab 06 — build it** 🧑‍💻
- File: `labs/06-observability-and-evaluation.ipynb`.

## Section J — Wrap (Block 10)

**28. Recap + what's next**
- The arc, one line each. Productionization: CI eval gates, cost/latency, human
  escalation, content safety, private networking.
- Pointers: immersion repo `hosted-agents/`, `AgentOps/`. Q&A + thank you.

---

## Section K — Optional advanced track: Data & Trust (Labs 07–09)

*Use only if you're running the extended/follow-on session. Slot after Section I or
as a second half-day. Keep the same sparse style.*

**29. Garbage in, garbage out (Content Understanding)**
- Split slide: a naive PDF text-dump (tables collapsed, figures lost) vs. Content
  Understanding output (Markdown tables, described figures, typed JSON fields).
- *"RAG is only as good as what you ingest. Fix the front of the pipeline."*

**30. Lab 07 — build it** 🧑‍💻
- File: `labs/07-document-extraction.ipynb`. Extract → then it feeds the Lab 04 index.

**31. The copilot is also a target**
- Three threats, one row each: jailbreak · PII paste · competitor/codename leak.
- *"A defensive prompt can be talked around. We want policy the model can't argue
  with."*

**32. Three layers of guardrails**
- Diagram: Prompt Shields (jailbreak/indirect) → PII blocklist → custom Schneider
  blocklist, all attached to one **RAI policy** on a **deployment**.

**33. Lab 08 — build it** 🧑‍💻
- File: `labs/08-guardrails.ipynb`. Benign passes; each attack blocked by its layer.
- *Note the synthetic blocklist terms (competitors + internal codenames).*

**34. Red teaming = measure the wall**
- ASR (Attack Success Rate), lower is better. Baseline vs. encoded (Base64/ROT13/
  confusable) vs. multilingual attacks.

**35. Lab 09 — build it** 🧑‍💻
- File: `labs/09-red-teaming.ipynb`. Bare model baseline → then attack the grounded
  copilot and compare ASR.

**36. The safety pipeline (payoff slide)**
- One triangle: **Guardrails (08) build the wall · Red teaming (09) climbs it ·
  Evaluation (06) measures it.** Run all three every release.
- *This is the slide to leave up during Q&A.*

---

### Optional backup slides
- Architecture deep-dive (how `config.py`/`tools.py` are shared by labs + app).
- The `openai` 2.44 + AAD embedding workaround (for the curious).
- Cost model for a production deployment.
- RBAC role reference (from [`docs/azure-setup.md`](../docs/azure-setup.md)).
