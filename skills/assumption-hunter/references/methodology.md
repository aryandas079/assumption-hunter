# Extraction and prioritization

Start with the decision the user might change. Ask what would have to be true about dependencies, inputs, users, environment, and measurement for the proposed outcome to follow. Look for words such as “will,” “always,” “already,” and “representative,” plus places where two components assume the other handles a failure. Search for disconfirming evidence before settling on a status.

Split independent properties. “The queue is durable and jobs run once” contains a persistence assumption and a delivery assumption with separate evidence and tests. Capture the relevant scope, such as “for worker restarts with one in-flight job.” Ignore generic risks with no material connection to the scoped decision.

| Category | When to use it |
| --- | --- |
| `observed` | Directly documented or measured within the stated scope |
| `inferred` | Follows from identified observations with a stated reasoning step |
| `hypothesis` | A testable premise with no decisive evidence yet |
| `preference` | A choice or value judgment. Check any implied empirical claim separately |
| `unknown` | A material condition whose basis has yet to be identified |

| Status | Meaning |
| --- | --- |
| `untested` | No relevant check or corroboration available |
| `supported` | Inspected evidence supports the scoped claim |
| `contradicted` | Inspected evidence conflicts with the scoped claim |
| `inconclusive` | Available results are mixed, weak, or unable to resolve the claim |
| `not_testable` | A preference or a claim with no meaningful test within scope |

| Input | 1 | 3 | 5 |
| --- | --- | --- | --- |
| Impact | Minor inconvenience | Significant rework or delay | Core failure or material safety or security consequence |
| Uncertainty | Strong, applicable evidence | Partial or mixed evidence | No reliable evidence |
| Test cost | Minutes or negligible resources | Hours or modest resources | Major resources or currently impractical |

Use 2 or 4 for intermediate cases. Score test candidates as `impact × uncertainty ÷ test_cost`. Sort with exact arithmetic, then by descending impact, descending uncertainty, and ascending ID. Put untested or inconclusive impact-5 items into the critical group first. Bring confirmed contradictions to the decision maker directly, even if certainty lowers their triage score. Treat the score as a scheduling heuristic.

Pick tests that could change the decision. State what you would observe if the claim holds and what observation would falsify it. Decide the threshold before viewing results. Control for plausible alternative explanations and separate “the test could not run” from a failed premise. Where possible, use a small, permission-cleared fixture or observational check and say what broader validation is still needed.
