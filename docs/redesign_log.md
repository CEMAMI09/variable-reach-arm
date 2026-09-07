# Redesign Log

Template for each failure → fix cycle (spec §51).

| ID | Date | Problem | Measurement | Hypothesis | Change | New measurement | Result |
|----|------|---------|-------------|------------|--------|-----------------|--------|
| R0 | — | Pitch torque vs budget | τ_req 16.3 Nm | NEMA23@8:1 borderline | Counterbalance 45% + SERVO57 | τ_req 11.9 Nm; capacity 17.6 | Resolved on paper |
| R1 | — | Yaw NEMA17 short | capacity 3 vs 7.2 Nm | Underpowered | NEMA23 @ 6:1 | 13.2 Nm capacity | Resolved on paper |
