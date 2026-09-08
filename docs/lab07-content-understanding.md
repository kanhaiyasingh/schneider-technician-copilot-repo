# Lab 07 · Content Understanding — provisioning, deny-assignment fix & facilitator notes

Companion doc for **Lab 07 · Document Extraction with Azure AI Content
Understanding**: provisioning, the "deny assignment" fix, what the lab teaches,
and facilitator run-of-show / slide additions.

> ⚠️ Synthetic training data — not affiliated with or endorsed by Schneider Electric.

## 1. What the lab does

Lab 07 fixes the **front of the RAG pipeline**. It takes a **complex PDF**
(`data/complex-docs/galaxy-vs-field-service-report.pdf` — a Galaxy VS
field-service report for asset `GVS-0002` at the Grenoble Data Center, with
tables, a fault-code matrix, a torque table and a wiring diagram) and uses
**Azure AI Content Understanding** to produce clean Markdown + preserved tables
(`prebuilt-documentSearch`) and typed fields via a custom analyzer, then chunks +
embeds + ingests into `schneider-extracted-index` and queries it. Punch-line:
naive PDF text-dumps collapse tables and lose diagrams; Content Understanding
does not.

Files: `src/cu.py`, `src/gen_complex_doc.py`, `src/build_lab07.py`,
`labs/07-document-extraction.ipynb`, `data/complex-docs/galaxy-vs-field-service-report.pdf`.

## 2. Provisioning

**No new resource needed.** Content Understanding is a capability of your existing
Foundry / Azure AI Services resource at `https://<foundry>.services.ai.azure.com/`.
Requirements: a supported region (`swedencentral` works), `gpt-4.1-mini` +
`text-embedding-3-large` deployments, and the **Cognitive Services User** role.

```bash
az cognitiveservices account deployment create -g $RG -n $FOUNDRY \
  --deployment-name gpt-4.1-mini --model-name gpt-4.1-mini \
  --model-format OpenAI --model-version "2025-04-14" \
  --sku-capacity 50 --sku-name GlobalStandard
az role assignment create --assignee "$USER_OID" \
  --role "Cognitive Services User" --scope "$RG_SCOPE"
```

`.env` (or leave blank to auto-derive from `AI_FOUNDRY_PROJECT_ENDPOINT`):

```
AZURE_CONTENT_UNDERSTANDING_ENDPOINT=https://<foundry>.services.ai.azure.com/
CU_GPT_MINI_DEPLOYMENT=gpt-4.1-mini
CU_EMBEDDING_DEPLOYMENT=text-embedding-3-large
```

## 3. Fixing the "deny assignment" error

**Symptom:** creating a Cognitive Services account fails with *"blocked by deny
assignment"* at a scope whose resource group ends in **`..._managed`**.

**Cause:** you targeted a Foundry-**managed** resource group. Azure locks managed
RGs with a deny assignment — nobody (even Owner) can hand-create resources there.

**Fix:**
1. **Reuse the existing Foundry resource (recommended).** Content Understanding
   already lives on `your-foundry-resource` (`*.services.ai.azure.com`). Deploy
   `gpt-4.1-mini` there and point `.env` at its base URL — no new resource, no
   deny assignment.
2. **Or** create a standalone `--kind AIServices` account in a **normal**
   resource group (never one ending in `_managed`), deploy the two models, grant
   **Cognitive Services User**, and set `AZURE_CONTENT_UNDERSTANDING_ENDPOINT`.

> Rule of thumb: never target a `_managed` resource group for manual creation.

## 4. Facilitator additions

Optional advanced block after Lab 06 (~25 min): (1) why ingestion quality matters
+ show the naive text-dump, (2) content extraction demo, (3) field extraction demo,
(4) ingest → query hands-on, (5) your-turn wrap. Stumbles: `403` → missing
**Cognitive Services User** role or wrong endpoint (use the `services.ai.azure.com`
base, not `/api/projects/`); analyzer 404 → api-version mismatch; deny assignment
→ §3.

Slide bullets: RAG starts before the index; complex docs break naive extraction;
Content Understanding → clean Markdown + tables + figures + typed fields; same
pipeline better input; production = batch + one analyzer per doc type + Lab 06
eval gates.
