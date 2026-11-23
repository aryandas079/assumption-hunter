# Receipt queue demonstration

The worker ACKs the invoice job after writing the receipt. The queue redelivers unacknowledged jobs after a restart.
Design premise: redelivery of the same invoice job produces at most one receipt for that invoice.
Staging objective: process a burst of 200 jobs in under ten minutes.

## Synthetic staging record

2026-11-23 06:50 UTC — The fixture delivered job J-001 twice for synthetic invoice I-001.
Two receipt rows were recorded. Outgoing email was disabled.

This is a fictional input for the example audit and snapshot comparison.
