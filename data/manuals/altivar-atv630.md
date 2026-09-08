# Altivar Process ATV630 Variable Speed Drive — Service Manual (Synthetic)

> **Workshop sample document.** This is synthetic sample documentation created for a hands-on training lab. Product names are used only for realism and this content is **not affiliated with, produced by, or endorsed by Schneider Electric**. Within this workshop, treat the specifications and fault codes below as the authoritative reference for the exercises.

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
