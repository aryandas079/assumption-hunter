# Examples

These are synthetic premises. Tailor their scope, thresholds, and fixtures to the decision under review.

| Domain | Input cue | Audit target | Small check |
| --- | --- | --- | --- |
| Software | “Retries are safe.” | A duplicate job produces at most one processed invoice. | Deliver a duplicate to a test queue and count outputs. |
| Software | “The old client can read new records.” | The oldest supported reader accepts records with the new field omitted. | Run that reader against an authorized synthetic record. |
| Software | “We can roll back.” | The previous release can read a row written using the migrated schema. | Write one fixture with the new version and read it with the previous version. |
| Research | “Recruitment is representative.” | The group characteristics used in the analysis match the target population within declared bounds. | Compare recruitment counts with an agreed population baseline. |
| Research | “Our treatment improves the result.” | The improvement persists against a matched baseline with a fixed evaluation protocol. | Compare the treatment and baseline on the same held-out fixture. |
| Research | “The sensor stays calibrated.” | Drift remains within the measurement error budget across the collection window. | Measure a known reference at both ends of the window. |
| Business | “We can launch next month.” | The dependency owner can deliver the required approval before the cutoff. | Compare the approval lead time and current queue with the cutoff. |
| Business | “Every sale pays for itself.” | Contribution margin stays positive after refunds and support time. | Calculate it on a permission-cleared transaction sample. |
| Business | “The new flow is self-service.” | First-time users can complete setup without staff help. | Observe a small consenting group using a staged flow. |
| Hardware | “The battery lasts all shift.” | The unit exceeds the required runtime under the defined duty cycle. | Measure draw during a representative cycle and document temperature. |
| Hardware | “Parts are interchangeable.” | Both approved variants remain within the circuit's tolerance budget. | Compare worst-case data sheet tolerances against that budget. |
| Hardware | “The enclosure has enough clearance.” | The specified cable bend radius fits across the assembly tolerance range. | Check a worst-case mock-up or tolerance drawing. |

“Use the blue enclosure” is a preference. “The unit must fit on this shelf” is a requirement. “We measured 23 mm in prototype A” is an observation if the record is available. Audit whether the design can satisfy the requirement or whether that observation generalizes to production.
