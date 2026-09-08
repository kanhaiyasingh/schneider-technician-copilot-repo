"""Deterministic synthetic data generator for the Schneider Technician Copilot workshop.

Run:  python src/data_gen.py

Produces (all SYNTHETIC — not affiliated with or endorsed by Schneider Electric;
product names are used only to make the workshop feel realistic):
  data/manuals/*.md          - short product manuals with fault codes + jargon
  data/installed_base.json   - customer sites and installed assets
  data/eval/technician_qa.jsonl - ground-truth Q&A for the evaluation lab

Everything is seeded so every attendee gets identical data (reproducible labs
and stable evaluation scores).
"""
from __future__ import annotations

import json
import random
from pathlib import Path

SEED = 2026
random.seed(SEED)

WORKSHOP_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = WORKSHOP_ROOT / "data"
MANUALS_DIR = DATA_DIR / "manuals"
EVAL_DIR = DATA_DIR / "eval"

DISCLAIMER = (
    "> **Workshop sample document.** This is synthetic sample documentation "
    "created for a hands-on training lab. Product names are used only for realism "
    "and this content is **not affiliated with, produced by, or endorsed by "
    "Schneider Electric**. Within this workshop, treat the specifications and fault "
    "codes below as the authoritative reference for the exercises.\n"
)

# --- Product manuals ---------------------------------------------------------
# Each manual mixes authentic-sounding jargon with invented fault codes so the
# file-search / retrieval labs have something concrete to cite.
MANUALS = {
    "galaxy-vs-ups.md": {
        "title": "Galaxy VS Uninterruptible Power Supply (UPS) — Service Manual (Synthetic)",
        "family": "Galaxy VS",
        "body": """
## 1. Overview
The Galaxy VS is a 3-phase, double-conversion (online) UPS rated 10-100 kVA with
unity power factor output. It supports **eco-mode**, **double-conversion**, and
**static bypass** operating modes. Nominal DC bus voltage is 480 V DC across the
capacitor bank; power conversion uses IGBT rectifier and inverter stages.

## 2. Key Specifications
- Topology: online double-conversion, VFI-SS-111 per IEC 62040-3
- Rated power: 10-100 kVA / 10-100 kW (pf = 1.0)
- Input THD: < 3% at full load
- Typical efficiency: up to 97% (double-conversion), up to 99% (eco-mode)
- Expected battery design life: 5 years at 25 degC
- Recommended preventive maintenance (PM) interval: every 12 months

## 3. Fault Codes
| Code | Meaning | First technician action |
|------|---------|-------------------------|
| E07  | DC bus overvoltage detected on the capacitor bank | Transfer load to static bypass, isolate the UPS, then inspect the DC bus and rectifier IGBT stage before restart. |
| E12  | Battery string voltage below threshold (end-of-discharge) | Verify battery breaker is closed; measure per-block voltage; replace any block below 1.75 V/cell. |
| E21  | Overtemperature on inverter heatsink | Check air filters and fan operation; confirm intake temperature is below 40 degC; clear obstruction, then reset. |
| E33  | Static bypass out of tolerance (voltage/frequency) | Confirm upstream source is within +/-10% voltage and +/-1 Hz; do NOT force bypass while out of tolerance. |

## 4. Safety
Follow lockout-tagout (LOTO) before servicing. Arc-flash PPE is mandatory when
the cabinet is energized. The DC capacitor bank can retain a lethal charge for up
to 5 minutes after isolation — verify zero energy with a meter before contact.

## 5. Maintenance Notes
Record firmware baseline at each PM visit. Torque all power terminations to spec
and log MTBF / MTTR observations in the service report.
""",
    },
    "powerlogic-pm8000.md": {
        "title": "PowerLogic PM8000 Power Quality Meter — Service Manual (Synthetic)",
        "family": "PowerLogic PM8000",
        "body": """
## 1. Overview
The PowerLogic PM8000 is a revenue-accuracy power quality meter measuring active
(kW), reactive (kVAR), and apparent (kVA) power, power factor, and harmonics up to
the 63rd order. It reports total harmonic distortion (THD) for voltage and current
and integrates with EcoStruxure Power Monitoring Expert.

## 2. Key Specifications
- Accuracy class: 0.2S (IEC 62053-22) for active energy
- Sampling: 1024 samples/cycle
- Communications: Modbus TCP, BACnet/IP
- Firmware baseline: v3.x series
- Recommended PM interval: every 24 months (verification of CT/PT wiring)

## 3. Fault / Event Codes
| Code | Meaning | First technician action |
|------|---------|-------------------------|
| A101 | CT (current transformer) polarity reversed | Verify CT dot orientation and phase mapping; correct wiring; re-run the phasor diagram check. |
| A140 | Voltage THD exceeds 8% alarm threshold | Investigate nonlinear loads / VFDs on the feeder; confirm the alarm setpoint against site power quality standard. |
| A205 | Loss of voltage on one phase | Check upstream breaker and PT fuse for the affected phase before assuming meter failure. |
| A310 | Time synchronization lost (NTP) | Confirm network path to the NTP server; re-apply time sync so energy intervals stay aligned. |

## 4. Safety
Never open-circuit an energized CT secondary — dangerous voltages result. Use
shorting blocks. Follow LOTO and arc-flash PPE requirements for the switchgear class.

## 5. Maintenance Notes
Confirm CT/PT ratios match the meter configuration. Log THD trends; sustained
voltage THD above 5% typically indicates harmonic-rich loads needing mitigation.
""",
    },
    "altivar-atv630.md": {
        "title": "Altivar Process ATV630 Variable Speed Drive — Service Manual (Synthetic)",
        "family": "Altivar ATV630",
        "body": """
## 1. Overview
The Altivar Process ATV630 is a variable speed drive (VSD/VFD) for pumps and fans,
0.75-160 kW. It regulates motor speed via PWM control of the IGBT inverter bridge
fed from a DC bus. Supports energy-saving quadratic V/f and sensorless flux vector
control.

## 2. Key Specifications
- Output frequency range: 0-599 Hz
- Overload: 110% continuous, 150% for 60 s (heavy duty)
- DC bus capacitor reforming required after > 2 years in storage
- Firmware baseline: V1.x
- Recommended PM interval: every 12 months (fan + capacitor inspection)

## 3. Fault Codes
| Code | Meaning | First technician action |
|------|---------|-------------------------|
| OCF  | Motor overcurrent (short circuit or ground fault) | De-energize, follow LOTO, megger the motor and cabling for insulation failure before restart. |
| OHF  | Drive overheating (heatsink) | Verify cooling fan runs and ambient is below 50 degC; clean the heatsink and confirm derating for altitude. |
| SCF3 | Ground fault detected at output | Inspect motor windings and output cabling for insulation breakdown; do not reset repeatedly. |
| OBF  | DC bus overvoltage during deceleration | Extend deceleration ramp or add a braking resistor; check regen from the driven load. |

## 4. Safety
The DC bus retains lethal voltage after power-off. Wait a minimum of 15 minutes and
verify zero DC bus voltage before touching terminals. Arc-flash PPE and LOTO apply.

## 5. Maintenance Notes
Reform DC bus capacitors on drives stored longer than 2 years. Record firmware
baseline and log OCF/OHF/SCF3 events with load conditions for trend analysis.
""",
    },
    "masterpact-mtz.md": {
        "title": "Masterpact MTZ Air Circuit Breaker — Service Manual (Synthetic)",
        "family": "Masterpact MTZ",
        "body": """
## 1. Overview
The Masterpact MTZ is a low-voltage air circuit breaker (ACB) with the MicroLogic X
trip unit, rated 800-6300 A. It provides protection (LSIG), metering, and
EcoStruxure connectivity for switchgear applications.

## 2. Key Specifications
- Rated current: 800-6300 A
- Breaking capacity (Icu): up to 150 kA
- Trip unit: MicroLogic X with LSIG protection
- Recommended PM interval: every 12 months or per operation count
- Firmware baseline: MicroLogic X v2.x

## 3. Fault / Status Codes
| Code | Meaning | First technician action |
|------|---------|-------------------------|
| TU-01 | Trip unit self-test failed | Do not rely on protection; schedule trip unit replacement and place breaker out of service if protection is compromised. |
| TU-14 | Ground fault (G) protection tripped | Investigate the downstream feeder for insulation fault before reclosing; log the trip current from the event log. |
| MX-02 | Communication loss to trip unit | Check the ULP module wiring and firmware baseline; restore comms so metering and events report correctly. |
| OP-99 | Operation count exceeds maintenance threshold | Schedule mechanism inspection and lubrication per the maintenance program. |

## 4. Safety
Racking a breaker must be done with the enclosure closed where possible. Arc-flash
boundary and PPE category must be verified from the site study. Apply LOTO and confirm
the breaker is in the disconnected (racked-out) position before servicing.

## 5. Maintenance Notes
Record operation count and the MicroLogic X firmware baseline at each visit. Verify
LSIG settings against the coordination study.
""",
    },
}

# --- Installed base ----------------------------------------------------------
SITES = [
    {"site_id": "SITE-CHN-01", "name": "Chennai Manufacturing Plant", "region": "APAC"},
    {"site_id": "SITE-GRE-02", "name": "Grenoble Data Center", "region": "EMEA"},
    {"site_id": "SITE-DAL-03", "name": "Dallas Distribution Hub", "region": "AMER"},
]

MODELS = [
    ("Galaxy VS", "GVS"),
    ("PowerLogic PM8000", "PM8K"),
    ("Altivar ATV630", "ATV630"),
    ("Masterpact MTZ", "MTZ"),
]

CONTRACT_TIERS = [
    "EcoStruxure Service Plan - Premium",
    "EcoStruxure Service Plan - Preventive",
    "EcoStruxure Service Plan - Advantage",
    "None",
]


def _serial(prefix: str, n: int) -> str:
    return f"{prefix}-{n:04d}"


def build_installed_base() -> list[dict]:
    assets = []
    counter = {p: 0 for _, p in MODELS}
    # 15 assets spread across sites and models, deterministic.
    for i in range(15):
        model_name, prefix = MODELS[i % len(MODELS)]
        counter[prefix] += 1
        site = SITES[i % len(SITES)]
        install_year = 2018 + (i % 6)  # 2018..2023
        warranty_years = 5
        warranty_expiry = install_year + warranty_years
        in_warranty = warranty_expiry >= 2026
        tier = CONTRACT_TIERS[i % len(CONTRACT_TIERS)]
        assets.append(
            {
                "serial": _serial(prefix, counter[prefix]),
                "model": model_name,
                "site_id": site["site_id"],
                "site_name": site["name"],
                "region": site["region"],
                "install_date": f"{install_year}-0{(i % 9) + 1}-15",
                "firmware_baseline": f"v{1 + (i % 3)}.{i % 5}",
                "warranty_status": "In warranty" if in_warranty else "Out of warranty",
                "warranty_expiry": f"{warranty_expiry}-12-31",
                "service_contract_tier": tier,
                "last_preventive_maintenance": f"{2024 + (i % 2)}-0{(i % 8) + 1}-10",
            }
        )
    return assets


# --- Evaluation Q&A ----------------------------------------------------------
# Ground-truth technician questions with expected answers and the manual section
# that grounds them. Includes happy-path plus edge cases.
EVAL_QA = [
    {
        "id": "qa-01",
        "question": "A Galaxy VS UPS is showing fault code E07. What is the first thing I should do?",
        "ground_truth": "E07 is a DC bus overvoltage on the capacitor bank. Transfer the load to static bypass, isolate the UPS, then inspect the DC bus and rectifier IGBT stage before restarting.",
        "source": "galaxy-vs-ups.md#3-fault-codes",
        "category": "fault-code",
    },
    {
        "id": "qa-02",
        "question": "My ATV630 drive keeps tripping on OCF. What does that mean and what should I check?",
        "ground_truth": "OCF is a motor overcurrent (short circuit or ground fault). De-energize, apply LOTO, and megger the motor and cabling for insulation failure before restarting.",
        "source": "altivar-atv630.md#3-fault-codes",
        "category": "fault-code",
    },
    {
        "id": "qa-03",
        "question": "The PM8000 is reporting A140. Is that a meter failure?",
        "ground_truth": "A140 means voltage THD exceeds the 8% alarm threshold. It usually indicates nonlinear loads or VFDs on the feeder, not a meter failure; investigate the loads and confirm the alarm setpoint.",
        "source": "powerlogic-pm8000.md#3-fault--event-codes",
        "category": "fault-code",
    },
    {
        "id": "qa-04",
        "question": "How often should a Galaxy VS UPS get preventive maintenance?",
        "ground_truth": "The recommended preventive maintenance interval for the Galaxy VS is every 12 months.",
        "source": "galaxy-vs-ups.md#2-key-specifications",
        "category": "maintenance",
    },
    {
        "id": "qa-05",
        "question": "How long can the DC bus on an ATV630 stay dangerous after power-off?",
        "ground_truth": "The DC bus retains lethal voltage after power-off; wait a minimum of 15 minutes and verify zero DC bus voltage before touching terminals.",
        "source": "altivar-atv630.md#4-safety",
        "category": "safety",
    },
    {
        "id": "qa-06",
        "question": "On a Masterpact MTZ I see TU-01. Can I keep it in service?",
        "ground_truth": "TU-01 is a trip unit self-test failure. Do not rely on protection; schedule trip unit replacement and take the breaker out of service if protection is compromised.",
        "source": "masterpact-mtz.md#3-fault--status-codes",
        "category": "safety",
    },
    {
        "id": "qa-07",
        "question": "What is the recommended action for a PM8000 A101 event?",
        "ground_truth": "A101 indicates reversed CT polarity. Verify CT dot orientation and phase mapping, correct the wiring, and re-run the phasor diagram check.",
        "source": "powerlogic-pm8000.md#3-fault--event-codes",
        "category": "fault-code",
    },
    {
        "id": "qa-08",
        "question": "The customer wants to know why their ATV630 trips on OBF when the pump slows down.",
        "ground_truth": "OBF is a DC bus overvoltage during deceleration. Extend the deceleration ramp or add a braking resistor, and check for regeneration from the driven load.",
        "source": "altivar-atv630.md#3-fault-codes",
        "category": "fault-code",
    },
    {
        "id": "qa-09",
        "question": "Is it safe to open-circuit the CT secondary on a PM8000 to reconnect it live?",
        "ground_truth": "No. Never open-circuit an energized CT secondary because dangerous voltages result; use shorting blocks and follow LOTO and arc-flash requirements.",
        "source": "powerlogic-pm8000.md#4-safety",
        "category": "safety",
    },
    {
        "id": "qa-10",
        "question": "What firmware detail should I always capture during a Galaxy VS PM visit?",
        "ground_truth": "Record the firmware baseline at each preventive maintenance visit (and torque power terminations to spec, logging MTBF/MTTR observations).",
        "source": "galaxy-vs-ups.md#5-maintenance-notes",
        "category": "maintenance",
    },
    {
        "id": "qa-11",
        "question": "The UPS shows E33 and I want to force it onto bypass to keep the load up. Should I?",
        "ground_truth": "E33 means the static bypass source is out of tolerance. Do not force bypass while out of tolerance; first confirm the upstream source is within +/-10% voltage and +/-1 Hz.",
        "source": "galaxy-vs-ups.md#3-fault-codes",
        "category": "safety",
    },
    {
        "id": "qa-12",
        "question": "What was the assassination date of Abraham Lincoln?",
        "ground_truth": "This question is out of scope for a field service copilot. The agent should decline and redirect the technician to equipment-related questions rather than answer from outside the manuals.",
        "source": "out-of-scope",
        "category": "out-of-scope",
    },
]


def main() -> None:
    MANUALS_DIR.mkdir(parents=True, exist_ok=True)
    EVAL_DIR.mkdir(parents=True, exist_ok=True)

    for filename, spec in MANUALS.items():
        content = f"# {spec['title']}\n\n{DISCLAIMER}\n{spec['body'].strip()}\n"
        (MANUALS_DIR / filename).write_text(content, encoding="utf-8")
    print(f"Wrote {len(MANUALS)} manuals to {MANUALS_DIR}")

    assets = build_installed_base()
    (DATA_DIR / "installed_base.json").write_text(
        json.dumps({"assets": assets}, indent=2), encoding="utf-8"
    )
    print(f"Wrote {len(assets)} installed-base assets to {DATA_DIR / 'installed_base.json'}")

    with (EVAL_DIR / "technician_qa.jsonl").open("w", encoding="utf-8") as f:
        for row in EVAL_QA:
            f.write(json.dumps(row) + "\n")
    print(f"Wrote {len(EVAL_QA)} eval Q&A rows to {EVAL_DIR / 'technician_qa.jsonl'}")


if __name__ == "__main__":
    main()
