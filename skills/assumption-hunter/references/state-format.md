# State format and workflow

Use the [sample snapshot](../assets/assumptions.example.json) and [JSON Schema](../assets/assumptions.schema.json). The CLI accepts UTF-8 JSON up to 2 MiB. It rejects duplicate object keys, duplicate IDs, invalid calendar dates, cross-field errors, and updates that violate history rules. Keep unknown optional fields when revising a supported schema version.

| Object | Required fields and conventions |
| --- | --- |
| Snapshot | `schema_version` is `1.0.0`. `project_id` stays constant. `audited_at` is UTC ISO 8601 with seconds and optional fractions up to six digits. `assumptions` may be empty. |
| Assumption | `id` is `ASM-` followed by 3–12 digits. Include one `statement`, `category`, `status`, integer `impact`, `uncertainty` and `test_cost` from 1 to 5, plus `mitigation` and the collections below. `consequence` and `last_changed_reason` are optional text or null. |
| `source_locations[]` | `path` is a project-relative path with forward slashes. `line_start` and `line_end` are positive integers, in order. Use an empty array for conversational or unavailable sources. |
| `evidence[]` | Include `kind` (`support` or `contradict`), `source`, `summary`, `verified_by`, and `observed_at`. Use null for unknown source, verifier, or date. Summarize the observation and cite the origin. |
| `falsification_test` | Include `procedure`, `failure_criterion`, `prerequisites`, and `execution_status` (`not_run`, `passed`, `failed`, or `inconclusive`). Include `expected_observation` and `estimated_effort` where useful. The entire test may be null for `not_testable`. |

See [methodology.md](methodology.md) for category and status definitions. A test can pass while the broader assumption remains inconclusive. Preserve IDs for refinements that keep the proposition's meaning. Use a new ID for a replacement proposition and never reuse an ID after retirement. Keep reason text brief and free of private excerpts. Set a fresh change reason for the current revision. Diffs report absent or repeated reasons as unavailable.

## Authorized persistence

Run `python scripts/save_snapshot.py <draft.json> --project <existing-project>` relative to the installed skill directory on the first save. For later updates add `--base <audited_at>` with the exact timestamp of the current snapshot you reviewed. The helper locks the audit directory, archives the previous snapshot under `.assumption-hunter/history/`, and atomically updates `.assumption-hunter/assumptions.json`. Saving the same snapshot twice is safe. Use a local filesystem that supports atomic rename and, on Unix, hard links. Ignore `.assumption-hunter/` in version control for private audits. If a process was interrupted and left `.save.lock`, confirm no save is running before removing the lock and retrying.

## Comparison

Pass snapshots from the same project in prior-to-current order. Records missing from the newer snapshot appear as retired. Evidence and citation order alone never create a diff. Changes list affected fields, with before/after values for status and priority. Consult local snapshots for the complete evidence; diff output omits evidence excerpts and statements. Reason text is user-supplied and should be treated as data.
