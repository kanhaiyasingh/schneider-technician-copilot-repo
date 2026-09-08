"""Builder for Lab 04 — Enterprise Grounding with Azure AI Search."""
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
# Lab 04 · Enterprise Grounding with Azure AI Search

File Search (Lab 03) is great for a handful of documents. In production, technical
content lives in an **enterprise search index** shared across many apps, with
**vector + semantic hybrid** retrieval and governance.

Here we:
1. Build an **Azure AI Search** index (vector + semantic).
2. Chunk the manuals, generate **embeddings**, and upload them.
3. Attach the index to an agent with **`AzureAISearchTool`** and get cited answers.

> ⚠️ Synthetic training data — not affiliated with or endorsed by Schneider Electric.
"""),
    md("""
## 1. Connect + resolve the Search connection

The Foundry project already has a **connection** to Azure AI Search. We fetch it
(with credentials) so we can create an index and upload documents. The connection
may authenticate by **API key** or **Entra ID (RBAC)** — `config.get_search_credential`
handles both.
"""),
    code(BOOTSTRAP + '''
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents import SearchClient

project_client = config.get_project_client()
search_conn = config.get_search_connection(project_client)
search_cred = config.get_search_credential(search_conn)

INDEX_NAME = config.WORKSHOP_INDEX_NAME
index_client = SearchIndexClient(endpoint=search_conn.target, credential=search_cred)
print("Search endpoint :", search_conn.target)
print("Connection name :", search_conn.name)
print("Target index    :", INDEX_NAME)
'''),
    md("""
## 2. Create the index (vector + semantic)

`text-embedding-3-large` produces **3072-dim** vectors. We add an HNSW vector
profile for similarity search and a semantic configuration for re-ranking.
"""),
    code('''
from azure.search.documents.indexes.models import (
    SearchIndex, SimpleField, SearchableField, SearchField, SearchFieldDataType,
    VectorSearch, HnswAlgorithmConfiguration, VectorSearchProfile,
    SemanticConfiguration, SemanticPrioritizedFields, SemanticField, SemanticSearch,
)

EMBED_DIMS = 3072  # text-embedding-3-large

fields = [
    SimpleField(name="id", type=SearchFieldDataType.String, key=True),
    SearchableField(name="product", type=SearchFieldDataType.String, filterable=True, facetable=True),
    SearchableField(name="title", type=SearchFieldDataType.String),
    SearchableField(name="content", type=SearchFieldDataType.String),
    SearchField(
        name="contentVector",
        type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
        searchable=True, vector_search_dimensions=EMBED_DIMS,
        vector_search_profile_name="vp",
    ),
]
vector_search = VectorSearch(
    algorithms=[HnswAlgorithmConfiguration(name="hnsw")],
    profiles=[VectorSearchProfile(name="vp", algorithm_configuration_name="hnsw")],
)
semantic_search = SemanticSearch(configurations=[
    SemanticConfiguration(
        name="default",
        prioritized_fields=SemanticPrioritizedFields(
            title_field=SemanticField(field_name="title"),
            content_fields=[SemanticField(field_name="content")],
            keywords_fields=[SemanticField(field_name="product")],
        ),
    )
])
index_client.create_or_update_index(
    SearchIndex(name=INDEX_NAME, fields=fields, vector_search=vector_search, semantic_search=semantic_search)
)
print(f"✅ Index '{INDEX_NAME}' created/updated.")
'''),
    md("""
## 3. Chunk the manuals, embed, and upload

We split each manual into its `##` sections (a simple, effective chunking
strategy) and embed each chunk with `config.embed_texts`.
"""),
    code('''
import re

docs = []
for path in sorted(config.MANUALS_DIR.glob("*.md")):
    text = path.read_text(encoding="utf-8")
    product = text.splitlines()[0].lstrip("# ").split(" — ")[0]
    for i, part in enumerate(re.split(r"\\n(?=## )", text)):
        chunk = part.strip()
        if len(chunk) < 20:
            continue
        docs.append({
            "id": f"{path.stem}-{i}",
            "product": product,
            "title": chunk.splitlines()[0].lstrip("# ").strip(),
            "content": chunk,
        })

print(f"Prepared {len(docs)} chunks. Generating embeddings...")
vectors = config.embed_texts([d["content"] for d in docs])
for d, v in zip(docs, vectors):
    d["contentVector"] = v

SearchClient(endpoint=search_conn.target, index_name=INDEX_NAME, credential=search_cred).upload_documents(documents=docs)
print(f"✅ Uploaded {len(docs)} chunks to '{INDEX_NAME}'.")
'''),
    md("""
## 4. Create an agent that searches the index

`AzureAISearchTool` points the agent at our index via the project **connection**.
`query_type=SEMANTIC` enables semantic re-ranking; the agent returns answers with
inline citations like `【4:0†source】`.
"""),
    code('''
from azure.ai.projects.models import (
    PromptAgentDefinition, AzureAISearchTool, AzureAISearchToolResource,
    AISearchIndexResource, AzureAISearchQueryType,
)

search_tool = AzureAISearchTool(
    azure_ai_search=AzureAISearchToolResource(
        indexes=[AISearchIndexResource(
            project_connection_id=search_conn.name,
            index_name=INDEX_NAME,
            query_type=AzureAISearchQueryType.SEMANTIC,
        )]
    )
)

search_agent = config.create_prompt_agent(
    project_client,
    name="technician-copilot-aisearch",
    instructions=config.TECH_PERSONA + """

You have an Azure AI Search tool over the product-manual knowledge base. Always
search it for fault codes, specs, safety, and procedures, and cite the sources it
returns. If nothing relevant is found, say so.""",
    tools=[search_tool],
)
print(f"✅ Search agent: {search_agent.name} (v{search_agent.version})")
'''),
    md("""
## 5. Ask grounded questions
"""),
    code('''
import time
time.sleep(3)  # give the index a moment to finish indexing

for q in [
    "What does fault code A140 mean on the PowerLogic PM8000 and what should I check?",
    "A Galaxy VS UPS shows E07. What is the first action?",
    "Which products mention IGBT stages, and why does that matter for safety?",
]:
    print("👤", q)
    print("🤖", config.ask(project_client, search_agent, q), "\\n" + "-"*70)
'''),
    md("""
## 🙌 Your turn

1. Switch the tool's `query_type` to `AzureAISearchQueryType.VECTOR_SEMANTIC_HYBRID`
   and re-create the agent. Compare the answers — hybrid blends keyword + vector.
2. Add a **filter** experiment: ask a question scoped to a single product and see
   whether the retrieved citations stay on-topic.
"""),
    code('''
# 👉 Your experiment here.
'''),
    md("""
## Clean up

We delete the agent. We keep the **index** if you want to reuse it in Lab 06;
uncomment the last line to delete it.
"""),
    code('''
config.delete_agent(project_client, search_agent)
print("🗑️  Deleted search agent.")
# index_client.delete_index(INDEX_NAME); print("🗑️  Deleted index.")
print("Next: Lab 05 orchestrates multiple specialist agents.")
'''),
]

if __name__ == "__main__":
    path = save(cells, "04-azure-ai-search.ipynb")
    print("Wrote", path)
