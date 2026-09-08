# Masterpact MTZ Air Circuit Breaker — Service Manual (Synthetic)

> **Workshop sample document.** This is synthetic sample documentation created for a hands-on training lab. Product names are used only for realism and this content is **not affiliated with, produced by, or endorsed by Schneider Electric**. Within this workshop, treat the specifications and fault codes below as the authoritative reference for the exercises.

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
