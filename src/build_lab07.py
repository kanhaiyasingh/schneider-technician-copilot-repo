"""Builder for Lab 07 — Document Extraction with Azure AI Content Understanding.

Lab 07 is the "how good data gets INTO Search" capstone. Labs 03/04 grounded the
copilot on *already-clean* Markdown manuals. Real Schneider documents are complex
PDFs — spec sheets, fault-code matrices, torque tables, wiring diagrams. This lab
uses **Azure AI Content Understanding** to turn one such PDF into clean Markdown +
structured fields, then feeds it into the same Azure AI Search RAG pipeline.
"""
from nb_util import md, code, save

BOOTSTRAP = '''
import os, sys, json, textwrap
from pathlib import Path

here = Path.cwd()
src = next((p / "src" for p in [here, *here.parents] if (p / "src" / "config.py").exists()), None)
if src and str(src) not in sys.path:
    sys.path.insert(0, str(src))

import config
import cu
'''

cells = [
    md("""
# Lab 07 · Document Extraction with Azure AI Content Understanding

Labs 03–04 grounded the copilot on our product manuals — but those were already
**clean Markdown**. In the real world, technical knowledge arrives as **complex
PDFs**: scanned spec sheets, fault-code matrices, torque tables, wiring diagrams,
inspection checklists. Dump those straight into a search index and you get
**garbage in, garbage out** — collapsed tables, lost figures, jumbled columns.

**Azure AI Content Understanding** fixes the *front* of the RAG pipeline. It turns
messy multimodal documents into:
1. **Clean, structured Markdown** (tables preserved, figures described),
2. **Typed fields** you define (fault codes, asset details, torque specs) via a
   custom analyzer.

In this lab we:
1. See why a **naive** PDF text-dump is bad.
2. Extract clean Markdown + tables with the **`prebuilt-documentSearch`** analyzer.
3. Extract **structured fields** with a **custom analyzer**.
4. Chunk, embed and **ingest the clean output into Azure AI Search** — the same
   pipeline you built in Lab 04 — and query it.

> 🧭 **Prerequisite:** an Azure AI Content Understanding–enabled resource
> (`*.services.ai.azure.com`) with **GPT-4.1-mini** + **text-embedding-3-large**
> deployments and the **Cognitive Services User** role. See
> [`docs/azure-setup.md`](../docs/azure-setup.md) §Content Understanding.

> ⚠️ Synthetic training data — not affiliated with or endorsed by Schneider Electric.
"""),
    md("""
## 1. The problem — naive ingestion loses structure

Our source is a synthetic **field-service report** for Galaxy VS asset `GVS-0002`
at the Grenoble Data Center (`SITE-GRE-02`). It has seven sections with tables,
a wiring diagram, and a checklist — exactly the kind of document a technician
actually receives.

Let's extract its text the *naive* way (a plain PDF text reader) and see what
happens to the tables and the diagram.
"""),
    code(BOOTSTRAP + '''
from pypdf import PdfReader

PDF_PATH = config.DATA_DIR / "complex-docs" / "galaxy-vs-field-service-report.pdf"
print("Document :", PDF_PATH.name, f"({PDF_PATH.stat().st_size:,} bytes)")

reader = PdfReader(str(PDF_PATH))
naive_text = "\\n".join((page.extract_text() or "") for page in reader.pages)
print(f"Pages    : {len(reader.pages)}  |  Naive chars: {len(naive_text)}\\n")
print("----- NAIVE TEXT (first 1600 chars) -----")
print(naive_text[:1600])
print("\\n⚠️  Notice: table columns run together, the fault-code matrix loses its")
print("   rows, and the wiring DIAGRAM is gone entirely — poor material for RAG.")
'''),
    md("""
## 2. Connect to Content Understanding (keyless)

Content Understanding is exposed on your **Foundry / Azure AI Services** resource
at its `https://<resource>.services.ai.azure.com/` base URL. We authenticate with
**Entra ID** (`az login`) — no keys, consistent with every other lab.

`src/cu.py` is a tiny REST client that mirrors the official
[`azure-ai-content-understanding-python`](https://github.com/Azure-Samples/azure-ai-content-understanding-python)
sample's method names, so what you learn here transfers to the GA SDK.
"""),
    code('''
# Endpoint: explicit env var, else derive from the Foundry project endpoint.
cu_endpoint = (
    os.environ.get("AZURE_CONTENT_UNDERSTANDING_ENDPOINT")
    or config.PROJECT_ENDPOINT.split("/api/projects/")[0]
)
if not cu_endpoint:
    raise RuntimeError("Set AZURE_CONTENT_UNDERSTANDING_ENDPOINT (or AI_FOUNDRY_PROJECT_ENDPOINT) in .env")

client = cu.ContentUnderstandingClient(cu_endpoint)
print("✅ Content Understanding endpoint:", cu_endpoint)
print("   API version:", client._api_version)
'''),
    md("""
## 3. (Once per resource) map the model deployments

Prebuilt analyzers reference logical model names. `update_defaults` tells the
service which of *your* deployments to use. This is a **one-time** step per
resource — if your administrator already ran it, the call is a harmless no-op, so
we wrap it in `try/except`.

`prebuilt-documentSearch` needs **GPT-4.1-mini** + **text-embedding-3-large**.
"""),
    code('''
gpt_mini = os.environ.get("CU_GPT_MINI_DEPLOYMENT", "gpt-4.1-mini")
embed_dep = os.environ.get("CU_EMBEDDING_DEPLOYMENT", config.EMBEDDING_MODEL)

try:
    result = client.update_defaults({
        "gpt-4.1-mini": gpt_mini,
        "text-embedding-3-large": embed_dep,
    })
    print("✅ Model deployments mapped:")
    for model, dep in result.get("modelDeployments", {}).items():
        print(f"   {model} -> {dep}")
except Exception as exc:
    print("ℹ️  Could not update defaults (may already be configured by an admin):")
    print("   ", str(exc)[:300])
'''),
    md("""
## 4. Content extraction — clean Markdown + tables

The **`prebuilt-documentSearch`** analyzer is purpose-built for RAG: it outputs
GitHub-flavoured Markdown with tables preserved, describes figures, and maps the
document structure. Analysis is a **long-running operation** — we submit the file,
then poll until it succeeds.
"""),
    code('''
print("🔍 Analyzing with prebuilt-documentSearch (this can take ~20-60s)...")
result = client.analyze_document(str(PDF_PATH), analyzer_id=cu.PREBUILT_DOCUMENT_SEARCH, timeout_seconds=240)

clean_markdown = cu.get_markdown(result)
tables = cu.get_tables(result)

print(f"✅ Extracted {len(clean_markdown)} chars of clean Markdown.")
print(f"📊 Detected {len(tables)} tables:")
for i, t in enumerate(tables, 1):
    print(f"   Table {i}: {t.get('rowCount')} rows x {t.get('columnCount')} cols")

print("\\n----- CLEAN MARKDOWN (first 1800 chars) -----")
print(clean_markdown[:1800])
'''),
    md("""
### Naive vs. Content Understanding

The contrast is the whole point: same PDF, but CU preserves the **table rows**,
labels the **fault codes**, and even represents the **wiring diagram** as a
described figure — content an LLM can actually reason over.
"""),
    code('''
def has_pipe_tables(text):
    return sum(1 for line in text.splitlines() if line.count("|") >= 2)

print(f"{'Metric':<32}{'Naive':>10}{'Content Understanding':>24}")
print("-" * 66)
print(f"{'Characters extracted':<32}{len(naive_text):>10}{len(clean_markdown):>24}")
print(f"{'Markdown table rows (| … |)':<32}{has_pipe_tables(naive_text):>10}{has_pipe_tables(clean_markdown):>24}")
print(f"{'Structured tables detected':<32}{0:>10}{len(tables):>24}")
print("\\n➡️  CU gives you clean, chunk-ready material; the naive dump does not.")
'''),
    md("""
## 5. Structured field extraction — a custom analyzer

Clean Markdown is great for retrieval, but sometimes you want **typed fields** —
the serial number, the warranty status, the fault-code table as JSON — to drive
automation (dispatch, escalation, dashboards).

We define a **custom analyzer** on top of `prebuilt-documentAnalyzer` with a field
schema, create it, run it, and read back structured JSON.
"""),
    code('''
# A **stable** analyzer id (not a random one) so re-running this notebook
# overwrites the same analyzer instead of piling up new ones. PUT is idempotent,
# so at most one custom analyzer ever exists for this lab — even if a cell fails
# before the cleanup step at the bottom.
analyzer_id = "schneider_fsr_lab07"
analyzer_template = {
    "description": "Schneider field-service report — key fields + fault-code table",
    "baseAnalyzerId": cu.PREBUILT_DOCUMENT_ANALYZER,
    "config": {"returnDetails": True},
    "models": {"completion": gpt_mini, "embedding": embed_dep},
    "fieldSchema": {
        "fields": {
            "SerialNumber": {"type": "string", "method": "extract",
                             "description": "Equipment serial number, e.g. GVS-0002"},
            "EquipmentModel": {"type": "string", "method": "extract",
                               "description": "Product / model name"},
            "SiteName": {"type": "string", "method": "extract",
                         "description": "Site name and/or site id"},
            "WarrantyStatus": {"type": "string", "method": "extract",
                               "description": "Warranty status of the asset"},
            "FaultCodes": {
                "type": "array", "method": "extract",
                "description": "Every fault code row in the report",
                "items": {
                    "type": "object",
                    "properties": {
                        "Code": {"type": "string"},
                        "Meaning": {"type": "string"},
                        "FirstAction": {"type": "string"},
                    },
                },
            },
        }
    },
}

print(f"🛠️  Creating custom analyzer '{analyzer_id}'...")
# Clear any leftover from a previous run so create always starts clean.
try:
    client.delete_analyzer(analyzer_id)
except Exception:
    pass
create_resp = client.begin_create_analyzer(analyzer_id, analyzer_template)
client.poll_result(create_resp, timeout_seconds=180)
print("✅ Analyzer ready.")
'''),
    code('''
print("🔍 Extracting structured fields...")
field_result = client.analyze_document(str(PDF_PATH), analyzer_id=analyzer_id, timeout_seconds=240)
fields = cu.get_fields(field_result)

print("📋 Extracted fields:")
for key in ("SerialNumber", "EquipmentModel", "SiteName", "WarrantyStatus"):
    print(f"   {key:<16}: {cu.field_value(fields.get(key, {}))}")

print("\\n⚡ Fault codes (as structured JSON):")
for row in cu.field_value(fields.get("FaultCodes", {})) or []:
    code_ = (row or {}).get("Code")
    meaning = (row or {}).get("Meaning")
    print(f"   {code_}: {meaning}")
'''),
    md("""
## 6. Ingest the clean output into Azure AI Search

Now we close the loop: chunk the **CU Markdown**, embed each chunk, and upsert into
a dedicated index `schneider-extracted-index` — the *same* vector + semantic schema
you built in Lab 04, but fed by clean, extraction-quality content.
"""),
    code('''
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents import SearchClient
from azure.search.documents.indexes.models import (
    SearchIndex, SimpleField, SearchableField, SearchField, SearchFieldDataType,
    VectorSearch, HnswAlgorithmConfiguration, VectorSearchProfile,
    SemanticConfiguration, SemanticPrioritizedFields, SemanticField, SemanticSearch,
)

EXTRACTED_INDEX = "schneider-extracted-index"
EMBED_DIMS = 3072  # text-embedding-3-large

project_client = config.get_project_client()
search_conn = config.get_search_connection(project_client)
search_cred = config.get_search_credential(search_conn)
index_client = SearchIndexClient(endpoint=search_conn.target, credential=search_cred)

fields = [
    SimpleField(name="id", type=SearchFieldDataType.String, key=True),
    SearchableField(name="product", type=SearchFieldDataType.String, filterable=True, facetable=True),
    SearchableField(name="source", type=SearchFieldDataType.String, filterable=True),
    SearchableField(name="title", type=SearchFieldDataType.String),
    SearchableField(name="content", type=SearchFieldDataType.String),
    SearchField(name="contentVector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True, vector_search_dimensions=EMBED_DIMS,
                vector_search_profile_name="vp"),
]
index_client.create_or_update_index(SearchIndex(
    name=EXTRACTED_INDEX, fields=fields,
    vector_search=VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="hnsw")],
        profiles=[VectorSearchProfile(name="vp", algorithm_configuration_name="hnsw")]),
    semantic_search=SemanticSearch(configurations=[SemanticConfiguration(
        name="default",
        prioritized_fields=SemanticPrioritizedFields(
            title_field=SemanticField(field_name="title"),
            content_fields=[SemanticField(field_name="content")],
            keywords_fields=[SemanticField(field_name="product")]))]),
))
print(f"✅ Index '{EXTRACTED_INDEX}' created/updated.")
'''),
    code('''
import re

# Chunk the CU Markdown on headings (falls back to paragraph blocks).
parts = [p.strip() for p in re.split(r"\\n(?=#{1,3} )", clean_markdown) if p.strip()]
if len(parts) < 2:
    parts = [p.strip() for p in clean_markdown.split("\\n\\n") if len(p.strip()) > 40]

docs = []
for i, chunk in enumerate(parts):
    if len(chunk) < 20:
        continue
    docs.append({
        "id": f"gvs-fsr-{i}",
        "product": "Galaxy VS",
        "source": PDF_PATH.name,
        "title": chunk.splitlines()[0].lstrip("# ").strip()[:120] or f"section-{i}",
        "content": chunk,
    })

print(f"Prepared {len(docs)} chunks from CU output. Embedding...")
vectors = config.embed_texts([d["content"] for d in docs])
for d, v in zip(docs, vectors):
    d["contentVector"] = v

SearchClient(endpoint=search_conn.target, index_name=EXTRACTED_INDEX,
             credential=search_cred).upload_documents(documents=docs)
print(f"✅ Uploaded {len(docs)} extraction-quality chunks to '{EXTRACTED_INDEX}'.")
'''),
    md("""
## 7. Query the extracted knowledge

The clean chunks are now retrievable. Because tables survived extraction, queries
about the **fault-code matrix** or **torque specs** return precise, grounded text.
"""),
    code('''
import time
time.sleep(3)  # let indexing settle

search_client = SearchClient(endpoint=search_conn.target, index_name=EXTRACTED_INDEX, credential=search_cred)
for q in [
    "What is the first action for fault code E07 on the Galaxy VS?",
    "What is the torque spec for the input bus bar?",
    "What was the measured DC bus voltage and was it in tolerance?",
]:
    print("👤", q)
    hits = list(search_client.search(search_text=q, top=1, select=["title", "content"]))
    snippet = (hits[0]["content"][:280] + " …") if hits else "(no hit)"
    print("🔎", snippet, "\\n" + "-" * 70)
'''),
    md("""
## 🙌 Your turn

1. **Add a field.** Extend the custom analyzer's `fieldSchema` with a
   `TorqueSpecs` array (termination + N·m) and re-run — structured torque data you
   could push to a maintenance system.
2. **Bring your own document.** Drop another PDF/image into `data/complex-docs/`
   and analyze it. Try an image file to see **figure descriptions** in the Markdown.
3. **Ground the copilot on it.** Point the Lab 04/05 `AzureAISearchTool` at
   `schneider-extracted-index` and ask the copilot a question answered only by this
   report — end-to-end, complex-PDF → grounded answer.
"""),
    code('''
# 👉 Your experiment here.
'''),
    md("""
## Clean up

We delete the custom analyzer. The **extracted index** is kept so you can point the
copilot at it in the "Your turn" challenge — uncomment the last line to delete it.
"""),
    code('''
try:
    client.delete_analyzer(analyzer_id)
    print(f"🗑️  Deleted custom analyzer '{analyzer_id}'.")
except Exception as exc:
    print("Cleanup warning:", str(exc)[:200])
# index_client.delete_index(EXTRACTED_INDEX); print("🗑️  Deleted extracted index.")
'''),
    md("""
## 🎓 What you learned

You fixed the **front of the RAG pipeline**:

| Step | Naive | Content Understanding |
|---|---|---|
| Tables | collapse into run-on text | preserved as Markdown tables |
| Figures | lost | described (chart/diagram) |
| Fields | none | typed JSON (fault codes, asset, warranty) |
| RAG quality | low | high — grounded, precise |

**In production:** batch-analyze a document library into an index, add custom
analyzers per document type (invoices, spec sheets, service reports), and gate the
extraction quality with the evaluation techniques from **Lab 06**.

**Next:** make the copilot **safe** — **[Lab 08 · Guardrails](08-guardrails.ipynb)**
stacks Prompt Shields, PII detection, and a custom Schneider blocklist on the model.
"""),
]

if __name__ == "__main__":
    path = save(cells, "07-document-extraction.ipynb")
    print("Wrote", path)
