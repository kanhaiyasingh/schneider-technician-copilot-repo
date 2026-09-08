"""Function tools for the Schneider Technician Copilot.

These are plain Python functions with ``Annotated`` type hints and Pydantic
``Field`` descriptions — the pattern the Foundry agents SDK uses to expose them
as callable tools. They read the synthetic ``installed_base.json``.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field

_DATA = Path(__file__).resolve().parent.parent / "data" / "installed_base.json"


@lru_cache(maxsize=1)
def _load_assets() -> list[dict]:
    return json.loads(_DATA.read_text(encoding="utf-8"))["assets"]


def lookup_asset_by_serial(
    serial: Annotated[
        str, Field(description="Equipment serial number, e.g. 'GVS-0001' or 'ATV630-0002'.")
    ],
) -> str:
    """Look up a single installed asset by its serial number.

    Returns model, site, install date, firmware baseline, warranty status, and
    service-contract tier as a JSON string, or an error message if not found.
    """
    serial_norm = serial.strip().upper()
    for asset in _load_assets():
        if asset["serial"].upper() == serial_norm:
            return json.dumps(asset)
    return json.dumps({"error": f"No asset found with serial '{serial}'."})


def list_assets_for_site(
    site_id: Annotated[
        str, Field(description="Site identifier, e.g. 'SITE-CHN-01', 'SITE-GRE-02', 'SITE-DAL-03'.")
    ],
) -> str:
    """List all installed assets at a given customer site (JSON list)."""
    site_norm = site_id.strip().upper()
    matches = [a for a in _load_assets() if a["site_id"].upper() == site_norm]
    if not matches:
        return json.dumps({"error": f"No assets found for site '{site_id}'."})
    return json.dumps({"site_id": site_id, "count": len(matches), "assets": matches})


def check_warranty_and_contract(
    serial: Annotated[
        str, Field(description="Equipment serial number to check coverage for, e.g. 'MTZ-0003'.")
    ],
) -> str:
    """Return warranty status and service-contract tier for an asset.

    Includes an ``escalate`` flag that is true when the asset is out of warranty
    and has no active service contract — used by the routing lab to decide when a
    case needs human escalation.
    """
    serial_norm = serial.strip().upper()
    for asset in _load_assets():
        if asset["serial"].upper() == serial_norm:
            out_of_warranty = asset["warranty_status"].lower().startswith("out")
            no_contract = asset["service_contract_tier"].lower() == "none"
            return json.dumps(
                {
                    "serial": asset["serial"],
                    "model": asset["model"],
                    "warranty_status": asset["warranty_status"],
                    "warranty_expiry": asset["warranty_expiry"],
                    "service_contract_tier": asset["service_contract_tier"],
                    "escalate": out_of_warranty and no_contract,
                }
            )
    return json.dumps({"error": f"No asset found with serial '{serial}'."})


# Convenience list for passing to an agent definition's ``tools=[...]``.
INSTALLED_BASE_TOOLS = [
    lookup_asset_by_serial,
    list_assets_for_site,
    check_warranty_and_contract,
]


def search_product_manuals(
    query: Annotated[
        str,
        Field(
            description="A natural-language question or keywords about equipment "
            "fault codes, specifications, safety, or procedures."
        ),
    ],
) -> str:
    """Search the product-manual knowledge base and return the most relevant excerpts.

    Use this whenever a technician asks about a fault code, specification, safety
    step, or maintenance procedure. Returns manual excerpts with their product and
    section so you can cite them.
    """
    import config

    return config.search_manuals(query, k=3)
