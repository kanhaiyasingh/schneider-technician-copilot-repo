"""Generate a deliberately *complex* synthetic Schneider field-service report PDF.

Lab 07 (Content Understanding) needs a document that a naive text-dump handles
badly but a layout-aware service handles well: multi-column tables, a fault-code
matrix, a torque table, an embedded single-line **wiring diagram** (a figure),
and a preventive-maintenance checklist with selection marks. All values are
synthetic but domain-real — they line up with the workshop's manuals and
installed base (asset ``GVS-0002`` at the Grenoble Data Center, Galaxy VS fault
codes E07/E12/E21/E33).

Run::

    .venv/Scripts/python.exe src/gen_complex_doc.py

Writes ``data/complex-docs/galaxy-vs-field-service-report.pdf``.
"""
from __future__ import annotations

from pathlib import Path

from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "complex-docs"
OUT_PATH = OUT_DIR / "galaxy-vs-field-service-report.pdf"

SE_GREEN = colors.HexColor("#3DCD58")
SE_DARK = colors.HexColor("#1A1A1A")
SE_GREY = colors.HexColor("#5A5A5A")
LIGHT = colors.HexColor("#EEF7EF")


# --- shared styles -----------------------------------------------------------
_ss = getSampleStyleSheet()
BODY = ParagraphStyle("body", parent=_ss["BodyText"], fontSize=9, leading=12, textColor=SE_DARK)
CELL = ParagraphStyle("cell", parent=BODY, fontSize=8.5, leading=11)
CELL_HDR = ParagraphStyle("cellh", parent=CELL, textColor=colors.white, fontName="Helvetica-Bold")
H2 = ParagraphStyle(
    "h2", parent=_ss["Heading2"], fontSize=12, leading=15, textColor=SE_GREEN,
    fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=4,
)
TITLE = ParagraphStyle("title", parent=_ss["Title"], fontSize=18, leading=21, textColor=SE_DARK)
SUB = ParagraphStyle("sub", parent=BODY, fontSize=10, textColor=SE_GREY)
CAPTION = ParagraphStyle("cap", parent=BODY, fontSize=8, textColor=SE_GREY, alignment=TA_CENTER)
DISCLAIMER = ParagraphStyle("disc", parent=BODY, fontSize=7.5, textColor=SE_GREY, alignment=TA_LEFT)


def _p(text: str, style: ParagraphStyle = CELL):
    return Paragraph(text, style)


def _table(data, col_widths, header=True, zebra=True):
    """Build a styled table; first row treated as header when ``header``."""
    style = [
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#C8D8CC")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    if header:
        style += [
            ("BACKGROUND", (0, 0), (-1, 0), SE_GREEN),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ]
    if zebra:
        style.append(("ROWBACKGROUNDS", (0, 1 if header else 0), (-1, -1), [colors.white, LIGHT]))
    t = Table(data, colWidths=col_widths, repeatRows=1 if header else 0)
    t.setStyle(TableStyle(style))
    return t


def _wiring_diagram() -> Drawing:
    """A simple single-line power path: Mains -> Rectifier -> DC Bus -> Inverter
    -> Static Bypass -> Load. A real *figure* for Content Understanding to detect
    and describe (Mermaid/description) rather than plain text.
    """
    w, h = 460, 150
    d = Drawing(w, h)
    d.add(Rect(0, 0, w, h, strokeColor=colors.HexColor("#C8D8CC"), fillColor=colors.white))

    blocks = [
        ("AC MAINS\n400 V 50 Hz", 12),
        ("RECTIFIER\n(IGBT)", 92),
        ("DC BUS\n480 V DC", 172),
        ("INVERTER\n(IGBT)", 252),
        ("STATIC\nBYPASS", 332),
        ("LOAD\n(Critical)", 412),
    ]
    bw, bh, by = 66, 46, 74
    centers = []
    for label, bx in blocks:
        d.add(Rect(bx, by, bw, bh, rx=4, ry=4, strokeColor=SE_DARK, fillColor=LIGHT, strokeWidth=1))
        for i, line in enumerate(label.split("\n")):
            d.add(String(bx + bw / 2, by + bh - 16 - i * 12, line,
                         fontName="Helvetica-Bold", fontSize=7, fillColor=SE_DARK, textAnchor="middle"))
        centers.append((bx, bx + bw))

    # series power path arrows between adjacent blocks
    for (left_end, _), (right_start, _) in zip(
        [(c[0], c[1]) for c in centers][:-1], [(c[0], c[1]) for c in centers][1:]
    ):
        y = by + bh / 2
        d.add(Line(left_end + 0, y, right_start, y, strokeColor=SE_GREEN, strokeWidth=2))
        d.add(Polygon([right_start, y, right_start - 6, y + 3, right_start - 6, y - 3], fillColor=SE_GREEN, strokeColor=SE_GREEN))
    # the bypass path (mains straight to load, drawn above)
    d.add(Line(centers[0][0] + 33, by + bh, centers[0][0] + 33, by + bh + 18, strokeColor=SE_GREY, strokeWidth=1))
    d.add(Line(centers[0][0] + 33, by + bh + 18, centers[4][0] + 33, by + bh + 18, strokeColor=SE_GREY, strokeWidth=1, strokeDashArray=[3, 2]))
    d.add(Line(centers[4][0] + 33, by + bh + 18, centers[4][0] + 33, by + bh, strokeColor=SE_GREY, strokeWidth=1))
    d.add(String(w / 2, by + bh + 24, "Static bypass path (dashed) — engages on inverter fault",
                 fontName="Helvetica-Oblique", fontSize=6.5, fillColor=SE_GREY, textAnchor="middle"))
    d.add(String(w / 2, 12, "Figure 1 — Galaxy VS single-line power path (double-conversion online UPS)",
                 fontName="Helvetica", fontSize=7, fillColor=SE_GREY, textAnchor="middle"))
    return d


def build() -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUT_PATH), pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm,
        title="Galaxy VS UPS — On-Site Field Service Report (Synthetic)",
        author="EcoStruxure Field Services (synthetic workshop sample)",
    )
    story = []

    # --- branded header band -------------------------------------------------
    band = Table(
        [[
            _p("<b>Schneider Electric</b>", ParagraphStyle("bh", parent=BODY, fontSize=13, textColor=colors.white)),
            _p("EcoStruxure™ Field Services", ParagraphStyle("bh2", parent=BODY, fontSize=10, textColor=colors.white, alignment=2)),
        ]],
        colWidths=[95 * mm, 79 * mm],
    )
    band.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SE_GREEN),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (0, 0), 10), ("RIGHTPADDING", (-1, -1), (-1, -1), 10),
    ]))
    story += [band, Spacer(1, 8)]
    story += [Paragraph("On-Site Field Service Report", TITLE)]
    story += [Paragraph("Uninterruptible Power Supply — Corrective &amp; Preventive Maintenance", SUB), Spacer(1, 8)]

    # --- report + asset identification (two side-by-side tables) -------------
    report_tbl = _table(
        [[_p("<b>Report</b>", CELL_HDR), _p("<b>Detail</b>", CELL_HDR)],
         [_p("Report No."), _p("FSR-2025-GRE-0417")],
         [_p("Service date"), _p("2025-04-17")],
         [_p("Technician"), _p("A. Moreau (Cert. L2)")],
         [_p("Dispatch type"), _p("Corrective — fault alarm")],
         [_p("Work order"), _p("WO-88213")]],
        col_widths=[28 * mm, 55 * mm],
    )
    asset_tbl = _table(
        [[_p("<b>Asset</b>", CELL_HDR), _p("<b>Value</b>", CELL_HDR)],
         [_p("Serial no."), _p("GVS-0002")],
         [_p("Model"), _p("Galaxy VS (3-phase UPS)")],
         [_p("Site"), _p("Grenoble Data Center — SITE-GRE-02")],
         [_p("Firmware"), _p("v2.4")],
         [_p("Warranty"), _p("In warranty (exp. 2027-12-31)")]],
        col_widths=[26 * mm, 57 * mm],
    )
    side = Table([[report_tbl, asset_tbl]], colWidths=[86 * mm, 88 * mm])
    side.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (1, 0), (1, 0), 6)]))
    story += [side, Spacer(1, 6)]

    # --- specifications ------------------------------------------------------
    story += [Paragraph("1. Equipment Specifications", H2)]
    story += [_table(
        [[_p("<b>Parameter</b>", CELL_HDR), _p("<b>Rating</b>", CELL_HDR), _p("<b>Measured</b>", CELL_HDR)],
         [_p("Topology"), _p("Online double-conversion (VFI-SS-111)"), _p("—")],
         [_p("Rated power"), _p("10–100 kVA / kW (pf = 1.0)"), _p("80 kVA")],
         [_p("Nominal DC bus"), _p("480 V DC"), _p("511 V DC ⚠")],
         [_p("Input THD"), _p("&lt; 3% at full load"), _p("2.4%")],
         [_p("Efficiency"), _p("up to 97% (double-conv.)"), _p("96.1%")],
         [_p("Battery design life"), _p("5 years @ 25 °C"), _p("Year 3")],
         [_p("PM interval"), _p("12 months"), _p("Due 2025-05")]],
        col_widths=[38 * mm, 78 * mm, 58 * mm],
    )]

    # --- fault code matrix ---------------------------------------------------
    story += [Paragraph("2. Fault Code Reference", H2)]
    story += [_table(
        [[_p("<b>Code</b>", CELL_HDR), _p("<b>Meaning</b>", CELL_HDR), _p("<b>First technician action</b>", CELL_HDR)],
         [_p("<b>E07</b>"), _p("DC bus overvoltage on the capacitor bank"),
          _p("Transfer load to static bypass, isolate the UPS, then inspect the DC bus and rectifier IGBT stage before restart.")],
         [_p("E12"), _p("Battery string below end-of-discharge threshold"),
          _p("Verify battery breaker closed; measure per-block voltage; replace any block &lt; 1.75 V/cell.")],
         [_p("E21"), _p("Overtemperature on inverter heatsink"),
          _p("Check air filters and fans; confirm intake &lt; 40 °C; clear obstruction, then reset.")],
         [_p("E33"), _p("Static bypass out of tolerance (V/Hz)"),
          _p("Confirm source within ±10% V and ±1 Hz; do NOT force bypass while out of tolerance.")]],
        col_widths=[16 * mm, 66 * mm, 92 * mm],
    )]

    # --- torque specifications ----------------------------------------------
    story += [Paragraph("3. Power Termination Torque Specifications", H2)]
    story += [_table(
        [[_p("<b>Termination</b>", CELL_HDR), _p("<b>Thread</b>", CELL_HDR), _p("<b>Torque (N·m)</b>", CELL_HDR), _p("<b>Torque (lb·in)</b>", CELL_HDR), _p("<b>Re-torque</b>", CELL_HDR)],
         [_p("Input bus bar"), _p("M10"), _p("40"), _p("354"), _p("✔")],
         [_p("Output bus bar"), _p("M10"), _p("40"), _p("354"), _p("✔")],
         [_p("Battery cabinet link"), _p("M8"), _p("20"), _p("177"), _p("✔")],
         [_p("Earth / PE stud"), _p("M8"), _p("20"), _p("177"), _p("✔")],
         [_p("Control terminal"), _p("M3.5"), _p("0.8"), _p("7"), _p("—")]],
        col_widths=[46 * mm, 22 * mm, 30 * mm, 32 * mm, 24 * mm],
    )]

    # --- wiring diagram figure ----------------------------------------------
    story += [Paragraph("4. Single-Line Power Path", H2)]
    story += [_wiring_diagram(), Spacer(1, 4)]

    # --- preventive maintenance checklist (selection marks) ------------------
    story += [Paragraph("5. Preventive Maintenance Checklist", H2)]
    story += [_table(
        [[_p("<b>Check</b>", CELL_HDR), _p("<b>Pass</b>", CELL_HDR), _p("<b>Fail</b>", CELL_HDR), _p("<b>Note</b>", CELL_HDR)],
         [_p("Air filters &amp; fan operation"), _p("☑"), _p("☐"), _p("Cleaned")],
         [_p("Battery block voltages"), _p("☑"), _p("☐"), _p("All &gt; 1.9 V/cell")],
         [_p("DC bus voltage within tolerance"), _p("☐"), _p("☑"), _p("511 V — E07 raised")],
         [_p("Torque audit of power terminations"), _p("☑"), _p("☐"), _p("Per section 3")],
         [_p("Firmware baseline recorded"), _p("☑"), _p("☐"), _p("v2.4")],
         [_p("Static bypass transfer test"), _p("☑"), _p("☐"), _p("Nominal")]],
        col_widths=[74 * mm, 16 * mm, 16 * mm, 48 * mm],
    )]

    # --- technician observations --------------------------------------------
    story += [Paragraph("6. Technician Observations", H2)]
    story += [Paragraph(
        "During a routine preventive-maintenance visit the unit raised <b>fault code E07</b> "
        "(DC bus overvoltage). Measured DC bus was 511 V DC against a 480 V nominal. Load was "
        "transferred to <b>static bypass</b> and the UPS isolated per lockout-tagout (LOTO). The "
        "DC capacitor bank was verified to zero energy with a meter before contact (arc-flash PPE "
        "worn throughout). Inspection of the <b>rectifier IGBT stage</b> found no visible damage; a "
        "gate-driver anomaly is suspected. Recommend firmware review and a follow-up with the "
        "escalation engineering team for asset GVS-0002.", BODY)]

    # --- warranty / contract block ------------------------------------------
    story += [Paragraph("7. Warranty &amp; Service Contract", H2)]
    story += [_table(
        [[_p("<b>Field</b>", CELL_HDR), _p("<b>Value</b>", CELL_HDR)],
         [_p("Service plan"), _p("EcoStruxure Service Plan — Premium")],
         [_p("Warranty status"), _p("In warranty")],
         [_p("Coverage end"), _p("2027-12-31")],
         [_p("Escalation candidate"), _p("Yes — recurring DC bus event")]],
        col_widths=[46 * mm, 128 * mm],
    )]

    story += [Spacer(1, 10)]
    story += [Paragraph(
        "<b>Synthetic workshop sample.</b> This document was fabricated for a hands-on Microsoft "
        "Foundry training lab. Product names, serial numbers, sites, fault codes, torque values and "
        "warranty records are fictitious and are used only for realism. This content is <b>not "
        "affiliated with, produced by, or endorsed by Schneider Electric.</b>", DISCLAIMER)]

    doc.build(story)
    return OUT_PATH


if __name__ == "__main__":
    path = build()
    print("Wrote", path, f"({path.stat().st_size:,} bytes)")
