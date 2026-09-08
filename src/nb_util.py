"""Tiny helpers to author workshop notebooks with nbformat.

Keeping notebook construction in code (rather than hand-writing JSON) means the
labs are reproducible and easy to edit — the same convention the foundry-workshop
repo uses for its generated notebooks.
"""
from __future__ import annotations

from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

LABS_DIR = Path(__file__).resolve().parent.parent / "labs"
SOLUTIONS_DIR = Path(__file__).resolve().parent.parent / "solutions"


def md(text: str):
    return new_markdown_cell(text.strip("\n"))


def code(text: str):
    return new_code_cell(text.strip("\n"))


def save(cells, filename: str, *, kernel: str = "python3") -> Path:
    """Write a notebook to labs/ and a copy to solutions/. Returns the labs path."""
    nb = new_notebook(cells=cells)
    nb.metadata["kernelspec"] = {
        "display_name": "Python (FoundryLabs .venv)",
        "language": "python",
        "name": kernel,
    }
    nb.metadata["language_info"] = {"name": "python", "version": "3.12"}
    LABS_DIR.mkdir(parents=True, exist_ok=True)
    SOLUTIONS_DIR.mkdir(parents=True, exist_ok=True)
    out = LABS_DIR / filename
    nbformat.write(nb, out)
    nbformat.write(nb, SOLUTIONS_DIR / filename)
    return out
