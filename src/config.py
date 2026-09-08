"""Shared configuration and client helpers for the Schneider Technician Copilot workshop.

Every lab imports from this module so the notebooks stay short and consistent.
It reuses the repository-root ``.env`` and Entra auth (``az login``) — no keys.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


def _find_repo_root(start: Optional[Path] = None) -> Path:
    """Walk upward from ``start`` until a directory containing ``.env`` is found.

    Labs live in ``schneider-technician-copilot/labs/``; the ``.env`` sits at the
    repository root, so a simple ``parent`` is not enough. We search upward.
    """
    here = (start or Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        if (candidate / ".env").exists():
            return candidate
    # Fall back to two levels up (labs -> workshop -> repo root).
    return here.parents[1] if len(here.parents) >= 2 else here


REPO_ROOT = _find_repo_root()
WORKSHOP_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = WORKSHOP_ROOT / "data"
MANUALS_DIR = DATA_DIR / "manuals"
EVAL_DIR = DATA_DIR / "eval"
INSTALLED_BASE_PATH = DATA_DIR / "installed_base.json"
EVAL_QA_PATH = EVAL_DIR / "technician_qa.jsonl"

# Load the repo-root .env exactly once on import.
load_dotenv(REPO_ROOT / ".env")

# --- Config constants (read from the shared .env) ---------------------------
PROJECT_ENDPOINT = os.environ.get("AI_FOUNDRY_PROJECT_ENDPOINT", "")
MODEL = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-5.4")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL_DEPLOYMENT_NAME", "text-embedding-3-large")
SEARCH_ENDPOINT = os.environ.get("AZURE_AI_SEARCH_ENDPOINT", "")
SEARCH_INDEX_NAME = os.environ.get("AZURE_SEARCH_INDEX_NAME", "build2026-aisearch-index")
TENANT_ID = os.environ.get("TENANT_ID", "")

# A dedicated index for this workshop so we never collide with other labs.
WORKSHOP_INDEX_NAME = "schneider-manuals-index"

# Shared technician-copilot persona, reused across labs for consistency.
TECH_PERSONA = """
You are the Schneider Field Service Technician Copilot, assisting on-site
technicians who service industrial electrical equipment (UPS, power meters,
variable speed drives, air circuit breakers).

Always:
1. Prioritize SAFETY — call out lockout-tagout (LOTO), arc-flash PPE, and stored
   energy (DC bus / capacitor) hazards whenever relevant.
2. Be concise and use correct field terminology (e.g., bypass, THD, IGBT, DC bus,
   fault codes).
3. When you rely on a manual, cite the source. If you are unsure or the manuals do
   not cover it, say so — never invent fault codes, specifications, or procedures.
4. Stay in scope: answer equipment service questions only. Politely decline
   unrelated questions.
""".strip()



def get_credential():
    """Return an ``AzureCliCredential`` (requires ``az login``).

    Matches the convention used by the workshop's reference notebooks.
    """
    from azure.identity import AzureCliCredential

    return AzureCliCredential(process_timeout=30)


def get_project_client():
    """Create an :class:`AIProjectClient` for the shared Foundry project."""
    from azure.ai.projects import AIProjectClient

    if not PROJECT_ENDPOINT:
        raise RuntimeError(
            "AI_FOUNDRY_PROJECT_ENDPOINT is not set. Fill in the repo-root .env."
        )
    return AIProjectClient(endpoint=PROJECT_ENDPOINT, credential=get_credential())


def create_prompt_agent(project_client, name: str, instructions: str, tools=None):
    """Create (version) a prompt agent via the raw Foundry API.

    Used by the hosted-tool labs (basic agent, file search, AI Search). ``tools``
    is an optional list of hosted tool objects (e.g. ``FileSearchTool``).
    """
    from azure.ai.projects.models import PromptAgentDefinition

    definition_kwargs = {"model": MODEL, "instructions": instructions}
    if tools:
        definition_kwargs["tools"] = tools
    return project_client.agents.create_version(
        agent_name=name,
        definition=PromptAgentDefinition(**definition_kwargs),
    )


def delete_agent(project_client, agent) -> None:
    """Delete an agent version created with :func:`create_prompt_agent`."""
    try:
        project_client.agents.delete_version(
            agent_name=agent.name, agent_version=agent.version
        )
    except Exception as exc:  # pragma: no cover - cleanup best effort
        print(f"Cleanup warning: could not delete {getattr(agent, 'name', agent)}: {exc}")


def get_search_connection(project_client):
    """Return the project's default Azure AI Search connection (with credentials)."""
    from azure.ai.projects.models import ConnectionType

    return project_client.connections.get_default(
        connection_type=ConnectionType.AZURE_AI_SEARCH, include_credentials=True
    )


def get_search_credential(search_connection):
    """Return an ``AzureKeyCredential`` (ApiKey conn) or an ``AzureCliCredential``."""
    from azure.core.credentials import AzureKeyCredential

    key = None
    creds = getattr(search_connection, "credentials", None) or {}
    if isinstance(creds, dict):
        key = creds.get("key")
    return AzureKeyCredential(key) if key else get_credential()


def embed_texts(texts, api_version: str = "2024-02-01"):
    """Embed a list of strings with the deployed embedding model via REST.

    The bundled ``openai`` client has a known AAD-credential bug in this
    environment, so we call the Azure OpenAI embeddings endpoint directly with a
    bearer token. Returns a list of embedding vectors (one per input string).
    """
    import requests

    base = os.environ.get("AZURE_OPENAI_ENDPOINT", "").split("/openai/")[0]
    if not base:
        raise RuntimeError("AZURE_OPENAI_ENDPOINT is not set in the .env")
    token = get_credential().get_token("https://cognitiveservices.azure.com/.default").token
    url = f"{base}/openai/deployments/{EMBEDDING_MODEL}/embeddings?api-version={api_version}"
    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"input": list(texts)},
        timeout=60,
    )
    resp.raise_for_status()
    return [item["embedding"] for item in resp.json()["data"]]


def search_manuals(query: str, k: int = 3) -> str:
    """Retrieve the top-k manual chunks for a query from the workshop AI Search index.

    Returns a formatted string of ``[product · section] content`` blocks, or a
    not-found message. Requires the index built in Lab 04 to exist.
    """
    import json as _json

    from azure.search.documents import SearchClient

    project_client = get_project_client()
    conn = get_search_connection(project_client)
    cred = get_search_credential(conn)
    client = SearchClient(endpoint=conn.target, index_name=WORKSHOP_INDEX_NAME, credential=cred)
    results = list(
        client.search(search_text=query, top=k, select=["product", "title", "content"])
    )
    if not results:
        return _json.dumps({"error": f"No manual content found for '{query}'."})
    blocks = [
        f"[{r['product']} · {r['title']}]\n{r['content']}" for r in results
    ]
    return "\n\n---\n\n".join(blocks)


def ask(project_client, agent, question: str, conversation_id: Optional[str] = None) -> str:
    """Invoke an agent via the Responses API and return its text output.

    ``agent`` may be an agent object (with ``.name``) or a plain agent-name string.
    Pass ``conversation_id`` to keep multi-turn context.
    """
    agent_name = getattr(agent, "name", agent)
    openai_client = project_client.get_openai_client()
    kwargs = {
        "extra_body": {
            "agent_reference": {"type": "agent_reference", "name": agent_name}
        },
        "input": question,
    }
    if conversation_id:
        kwargs["conversation"] = conversation_id
    response = openai_client.responses.create(**kwargs)
    return response.output_text or ""
