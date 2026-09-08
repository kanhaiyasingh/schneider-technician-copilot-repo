# PowerLogic PM8000 Power Quality Meter — Service Manual (Synthetic)

> **Workshop sample document.** This is synthetic sample documentation created for a hands-on training lab. Product names are used only for realism and this content is **not affiliated with, produced by, or endorsed by Schneider Electric**. Within this workshop, treat the specifications and fault codes below as the authoritative reference for the exercises.

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
