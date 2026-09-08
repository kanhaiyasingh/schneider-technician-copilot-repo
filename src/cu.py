"""Minimal, keyless Azure AI **Content Understanding** REST client for the workshop.

Content Understanding (CU) turns *complex, multimodal* documents (scanned PDFs,
spec sheets with tables, wiring diagrams) into clean, structured data — Markdown,
detected tables, figure descriptions, and (with a custom analyzer) typed fields.
Lab 07 uses it to extract high-quality content *before* it is chunked, embedded
and pushed into Azure AI Search.

Why a vendored client instead of an SDK?
    The official ``azure-ai-contentunderstanding`` GA SDK is the right choice for
    production, but it is not pinned into this workshop's environment and the lab
    machines' package proxy is restrictive. CU's surface we need is a thin REST
    API, so we mirror the shapes from the official sample
    (`Azure-Samples/azure-ai-content-understanding-python`) using ``requests`` +
    ``azure-identity`` — both already workshop dependencies. The method names
    (``begin_analyze_binary``, ``begin_analyze_url``, ``poll_result``,
    ``begin_create_analyzer``, ``update_defaults``) match that sample so
    participants can graduate to the SDK later with no surprises.

Auth is **keyless** (Entra ID via ``az login``), consistent with the rest of the
workshop — no subscription keys in code or ``.env``.

GA REST facts (api-version ``2025-11-01``):
    * binary file   -> POST ``/contentunderstanding/analyzers/{id}:analyzeBinary``
    * document URL   -> POST ``/contentunderstanding/analyzers/{id}:analyze``
                        body ``{"inputs": [{"url": "..."}]}``
    * create/get/del -> PUT/GET/DELETE ``/contentunderstanding/analyzers/{id}``
    * model defaults -> PATCH ``/contentunderstanding/defaults`` (merge-patch+json)
    Both analyze calls are long-running: the response carries an
    ``operation-location`` header you poll until ``status == "Succeeded"``.
"""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import requests

# GA api-version. Override via the ``CONTENT_UNDERSTANDING_API_VERSION`` env var
# (e.g. "2025-05-01-preview") if your resource/region only exposes preview.
DEFAULT_API_VERSION = "2025-11-01"
COGNITIVE_SCOPE = "https://cognitiveservices.azure.com/.default"

# The prebuilt analyzer that emits RAG-ready Markdown + layout + tables.
# Requires GPT-4.1-mini + text-embedding-3-large deployments on the resource.
PREBUILT_DOCUMENT_SEARCH = "prebuilt-documentSearch"
# The base analyzer used when defining a *custom field* analyzer.
PREBUILT_DOCUMENT_ANALYZER = "prebuilt-document"


def cli_token_provider() -> Callable[[], str]:
    """Return a callable that yields a fresh Entra bearer token for CU.

    Uses ``AzureCliCredential`` (``az login``) — the same keyless convention the
    rest of the workshop follows. The token is scoped to Cognitive Services.
    """
    from azure.identity import AzureCliCredential, get_bearer_token_provider

    return get_bearer_token_provider(AzureCliCredential(process_timeout=30), COGNITIVE_SCOPE)


class ContentUnderstandingClient:
    """Thin, keyless wrapper over the Content Understanding REST API."""

    def __init__(
        self,
        endpoint: str,
        api_version: Optional[str] = None,
        *,
        token_provider: Optional[Callable[[], str]] = None,
    ) -> None:
        if not endpoint:
            raise ValueError(
                "Content Understanding endpoint is required "
                "(e.g. https://<resource>.services.ai.azure.com/)."
            )
        self._endpoint = endpoint.rstrip("/")
        self._api_version = api_version or os.environ.get(
            "CONTENT_UNDERSTANDING_API_VERSION", DEFAULT_API_VERSION
        )
        self._token_provider = token_provider or cli_token_provider()

    # --- internal helpers ----------------------------------------------------
    @property
    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self._token_provider()}"}

    def _analyzer_url(self, analyzer_id: str) -> str:
        return (
            f"{self._endpoint}/contentunderstanding/analyzers/{analyzer_id}"
            f"?api-version={self._api_version}"
        )

    def _analyze_url(self, analyzer_id: str) -> str:
        return (
            f"{self._endpoint}/contentunderstanding/analyzers/{analyzer_id}:analyze"
            f"?api-version={self._api_version}"
        )

    def _analyze_binary_url(self, analyzer_id: str) -> str:
        return (
            f"{self._endpoint}/contentunderstanding/analyzers/{analyzer_id}:analyzeBinary"
            f"?api-version={self._api_version}"
        )

    def _defaults_url(self) -> str:
        return f"{self._endpoint}/contentunderstanding/defaults?api-version={self._api_version}"

    @staticmethod
    def _raise(resp: requests.Response) -> None:
        """Raise for HTTP errors, surfacing the service's error body for debugging."""
        if resp.status_code >= 400:
            detail = resp.text
            try:
                detail = resp.json()
            except Exception:  # pragma: no cover - best effort
                pass
            raise requests.HTTPError(
                f"CU request failed [{resp.status_code}] {resp.request.method} "
                f"{resp.request.url}\n{detail}",
                response=resp,
            )

    # --- resource config -----------------------------------------------------
    def update_defaults(self, model_deployments: Dict[str, Optional[str]]) -> Dict[str, Any]:
        """Map CU model names to your deployment names (once per resource).

        Prebuilt analyzers reference logical model names (``gpt-4.1-mini``,
        ``text-embedding-3-large``); this tells CU which of *your* deployments to
        use. Example::

            client.update_defaults({
                "gpt-4.1-mini": "gpt-4.1-mini",
                "text-embedding-3-large": "text-embedding-3-large",
            })
        """
        headers = self._headers
        headers["Content-Type"] = "application/merge-patch+json"
        resp = requests.patch(
            self._defaults_url(),
            headers=headers,
            json={"modelDeployments": model_deployments},
            timeout=60,
        )
        self._raise(resp)
        return resp.json()

    # --- analyzers -----------------------------------------------------------
    def begin_create_analyzer(self, analyzer_id: str, analyzer_template: Dict[str, Any]) -> requests.Response:
        """Create/replace a custom analyzer (PUT). Poll the response before use."""
        if not analyzer_template:
            raise ValueError("analyzer_template must be provided.")
        headers = self._headers
        headers["Content-Type"] = "application/json"
        resp = requests.put(
            self._analyzer_url(analyzer_id), headers=headers, json=analyzer_template, timeout=60
        )
        self._raise(resp)
        return resp

    def delete_analyzer(self, analyzer_id: str) -> None:
        resp = requests.delete(self._analyzer_url(analyzer_id), headers=self._headers, timeout=60)
        self._raise(resp)

    # --- analysis (long-running) --------------------------------------------
    def begin_analyze_binary(self, analyzer_id: str, file_location: str) -> requests.Response:
        """Analyze a **local file** (GA ``:analyzeBinary`` endpoint)."""
        path = Path(file_location)
        if not path.is_file():
            raise ValueError(f"File not found: {file_location}")
        headers = self._headers
        headers["Content-Type"] = "application/octet-stream"
        resp = requests.post(
            self._analyze_binary_url(analyzer_id),
            headers=headers,
            data=path.read_bytes(),
            timeout=120,
        )
        self._raise(resp)
        return resp

    def begin_analyze_url(self, analyzer_id: str, url: str) -> requests.Response:
        """Analyze a document by **public URL** (``:analyze`` endpoint)."""
        if not (url.startswith("http://") or url.startswith("https://")):
            raise ValueError("url must start with http:// or https://")
        headers = self._headers
        headers["Content-Type"] = "application/json"
        resp = requests.post(
            self._analyze_url(analyzer_id),
            headers=headers,
            json={"inputs": [{"url": url}]},
            timeout=120,
        )
        self._raise(resp)
        return resp

    def poll_result(
        self, response: requests.Response, timeout_seconds: int = 180, interval_seconds: float = 2.0
    ) -> Dict[str, Any]:
        """Poll the LRO ``operation-location`` until it succeeds; return the JSON."""
        op_location = response.headers.get("operation-location") or response.headers.get(
            "Operation-Location"
        )
        if not op_location:
            raise ValueError("No operation-location header on the analyze response.")
        deadline = time.time() + timeout_seconds
        while True:
            poll = requests.get(op_location, headers=self._headers, timeout=60)
            self._raise(poll)
            body = poll.json()
            status = str(body.get("status", "")).lower()
            if status in ("succeeded", "completed"):
                return body
            if status in ("failed", "canceled", "cancelled"):
                raise RuntimeError(f"Content Understanding analysis {status}: {body}")
            if time.time() > deadline:
                raise TimeoutError(
                    f"CU analysis did not finish within {timeout_seconds}s (last status: {status})."
                )
            time.sleep(interval_seconds)

    # --- convenience ---------------------------------------------------------
    def analyze_document(
        self, file_location: str, analyzer_id: str = PREBUILT_DOCUMENT_SEARCH, timeout_seconds: int = 180
    ) -> Dict[str, Any]:
        """One-call helper: submit a local file and return the finished result JSON."""
        response = self.begin_analyze_binary(analyzer_id, file_location)
        return self.poll_result(response, timeout_seconds=timeout_seconds)


# --- result parsing helpers (work on the JSON poll_result returns) -----------
def _first_content(result: Dict[str, Any]) -> Dict[str, Any]:
    contents = (result or {}).get("result", {}).get("contents", [])
    return contents[0] if contents else {}


def get_markdown(result: Dict[str, Any]) -> str:
    """Return the clean Markdown extracted from the (first) document content."""
    return _first_content(result).get("markdown", "")


def get_tables(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return the detected tables (each has ``rowCount``/``columnCount``/``cells``)."""
    return _first_content(result).get("tables", []) or []


def get_fields(result: Dict[str, Any]) -> Dict[str, Any]:
    """Return the structured fields extracted by a **custom** field analyzer."""
    return _first_content(result).get("fields", {}) or {}


def field_value(field: Dict[str, Any]) -> Any:
    """Unwrap a CU field object to its scalar/array value regardless of type.

    CU returns fields typed like ``{"type": "string", "valueString": "..."}`` or
    ``{"type": "array", "valueArray": [...]}``. This returns the payload without
    the caller needing to know the type key.
    """
    if not isinstance(field, dict):
        return field
    for key in (
        "valueString", "valueNumber", "valueInteger", "valueDate", "valueBoolean",
        "valueArray", "valueObject", "value",
    ):
        if key in field:
            val = field[key]
            if key == "valueArray" and isinstance(val, list):
                return [field_value(v) for v in val]
            if key == "valueObject" and isinstance(val, dict):
                return {k: field_value(v) for k, v in val.items()}
            return val
    return field
