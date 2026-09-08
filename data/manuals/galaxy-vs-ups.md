# Galaxy VS Uninterruptible Power Supply (UPS) — Service Manual (Synthetic)

> **Workshop sample document.** This is synthetic sample documentation created for a hands-on training lab. Product names are used only for realism and this content is **not affiliated with, produced by, or endorsed by Schneider Electric**. Within this workshop, treat the specifications and fault codes below as the authoritative reference for the exercises.

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
