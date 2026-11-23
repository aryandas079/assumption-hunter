# Assumption Hunter

[![CI](https://github.com/aryandas079/assumption-hunter/actions/workflows/ci.yml/badge.svg)](https://github.com/aryandas079/assumption-hunter/actions/workflows/ci.yml)

Assumption Hunter is an Agent Skill for Codex and Claude Code. It audits the premises behind a plan, codebase, or research proposal, connects them to evidence, and proposes the smallest check that could change a decision. When you rerun an audit, it can compare snapshots and show which conclusions changed.

The host performs the audit. The bundled Python tools provide deterministic validation, ranking, and comparison. The optional local MCP server exposes the same operations alongside the audit guide.

## Install the skill

### Codex CLI plugin

With [uv](https://docs.astral.sh/uv/getting-started/installation/) on your PATH, run:

```sh
codex plugin marketplace add aryandas079/assumption-hunter
codex plugin add assumption-hunter@assumption-hunter-marketplace
```

Open a new session and invoke `$assumption-hunter`. The plugin bundles the MCP server. Use the manual install for the skill alone or for a host without plugin support. [Codex plugin packaging](https://developers.openai.com/plugins/build/plugins)

### Claude Code plugin

With [uv](https://docs.astral.sh/uv/getting-started/installation/) on your PATH, run these commands inside Claude Code:

```text
/plugin marketplace add aryandas079/assumption-hunter
/plugin install assumption-hunter@assumption-hunter-marketplace
/reload-plugins
```

Invoke `/assumption-hunter:assumption-hunter`. The plugin includes the MCP server. Its first launch can download Python and locked dependencies if needed. Use the manual install below for the skill alone. [Claude Code plugin docs](https://code.claude.com/docs/en/plugins)

### Codex or Claude Code manual install

Clone the repository and copy the entire `skills/assumption-hunter` folder into your destination, or extract it from the [skill ZIP](https://github.com/aryandas079/assumption-hunter/releases/latest/download/assumption-hunter-skill.zip). The skill instructions can run without Python. The offline scripts require Python 3.11 or later.

| Host | Project destination | Invocation |
| --- | --- | --- |
| Codex | `.agents/skills/assumption-hunter/` | `$assumption-hunter` |
| Claude Code | `.claude/skills/assumption-hunter/` | `/assumption-hunter` |

For example, from the **project you want to audit** on PowerShell:

```powershell
git clone https://github.com/aryandas079/assumption-hunter.git ../assumption-hunter
New-Item -ItemType Directory -Force .agents/skills | Out-Null
Copy-Item -Recurse ../assumption-hunter/skills/assumption-hunter .agents/skills/
```

On macOS or Linux:

```sh
git clone https://github.com/aryandas079/assumption-hunter.git ../assumption-hunter
mkdir -p .agents/skills
cp -R ../assumption-hunter/skills/assumption-hunter .agents/skills/
```

Use `.claude/skills/` in place of `.agents/skills/` for Claude Code. Open a fresh host session in the audited project. In ChatGPT Work or Claude on the web, custom skill availability and execution permissions depend on the account and surface. Where an import is offered, use the skill folder or its ZIP for the instructions. Local stdio MCP requires a host that can launch a local process. [Codex skills](https://learn.chatgpt.com/docs/build-skills) · [Claude Code skills](https://code.claude.com/docs/en/skills) · [Claude custom skill upload](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills)

## Connect the MCP server

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and run the following from the **Assumption Hunter clone**. Choose the command for your host. Skip this step if you installed a bundled plugin.

PowerShell:

```powershell
$repo = (Get-Location).Path
$server = Join-Path $repo "skills/assumption-hunter/scripts/mcp_server.py"
codex mcp add assumption-hunter -- uv run --locked --no-dev --extra mcp --project "$repo" python "$server"
# Or, for Claude Code
claude mcp add --transport stdio --scope user assumption-hunter -- uv run --locked --no-dev --extra mcp --project "$repo" python "$server"
```

macOS or Linux:

```sh
repo="$(pwd -P)"
server="$repo/skills/assumption-hunter/scripts/mcp_server.py"
codex mcp add assumption-hunter -- uv run --locked --no-dev --extra mcp --project "$repo" python "$server"
# Or, for Claude Code
claude mcp add --transport stdio --scope user assumption-hunter -- uv run --locked --no-dev --extra mcp --project "$repo" python "$server"
```

Check `codex mcp list` or `claude mcp list` and open a new session. For another stdio-compatible client, configure command `uv` and arguments `["run", "--locked", "--no-dev", "--extra", "mcp", "--project", "<absolute clone path>", "python", "<absolute server script path>"]`. Use `get_audit_guide` in clients that surface tools only. [Codex MCP](https://learn.chatgpt.com/docs/extend/mcp?surface=cli) · [Claude Code MCP](https://code.claude.com/docs/en/mcp)

| MCP capability | Inputs and output |
| --- | --- |
| `get_audit_guide` | Optional `section` such as `state`, `methodology`, or `sample`. Returns bundled content. |
| `validate_audit_snapshot` | `snapshot_json` as JSON text. Returns validation and count. |
| `rank_audit_assumptions` | `snapshot_json` as JSON text. Returns ranked IDs and score details. |
| `compare_audit_snapshots` | `old_snapshot_json` and `new_snapshot_json` as JSON text. Returns changed IDs, fields, statuses, and priorities. |
| `audit_assumptions` | Reusable MCP prompt with the audit workflow. |
| MCP resources | `assumption-hunter://guide/workflow`, `assumption-hunter://guide/state`, and `assumption-hunter://assets/example`. |

The MCP runtime reads bundled guides and processes supplied JSON in memory. It accepts no arbitrary filesystem paths, commands, URLs to fetch, or state-changing operations. The first `uv` launch can install dependencies. Subsequent runs can use `--offline` after the dependencies are available. The host's own permissions and data policies still apply, including whether it sends audit text to its model provider.

## Try an audit

- “Use Assumption Hunter to audit our queue retry design. Cite the relevant source and propose a staging check for the highest-impact premise.”
- “Stress-test this research proposal. Check whether the sample and baseline support the conclusion, and identify what result would overturn it.”
- “Re-audit the revised design against my previous snapshot. Tell me which assumptions changed and what new evidence explains each change.”

Try the offline tools from the repository root. On Windows, use `py -3` in place of `python` if that is your Python launcher.

```sh
python skills/assumption-hunter/scripts/validate_state.py skills/assumption-hunter/assets/assumptions.example.json
python skills/assumption-hunter/scripts/rank_assumptions.py skills/assumption-hunter/assets/assumptions.example.json
python skills/assumption-hunter/scripts/compare_snapshots.py skills/assumption-hunter/assets/assumptions.example.json examples/updated.json
```

In the [synthetic receipt queue audit](examples/receipt-queue.md), a staging record shows two receipt rows for one invoice after redelivery. The comparison identifies `ASM-001` as moving from `untested` to `contradicted`. The queue throughput premise remains untested.

Use `--json` for structured ranking or comparison. The comparison can create a new report with `--output report.md`, or use `--json --output report.json`. The destination must be a new relative path inside the working directory. The CLI refuses to overwrite reports.

### Save and re-audit

When you want persistent state, ask the host to save the snapshot, or run:

```sh
python skills/assumption-hunter/scripts/save_snapshot.py first-audit.json --project .
python skills/assumption-hunter/scripts/save_snapshot.py revised-audit.json --project . --base 2026-11-23T06:00:00Z
```

Use the real `audited_at` from the current snapshot as `--base`. The helper preserves previous snapshots in `.assumption-hunter/history/` and writes the latest to `.assumption-hunter/assumptions.json`. Ignore `.assumption-hunter/` in the audited project's version control if it holds private material. For comparisons without persistence, pass both snapshots to the CLI or MCP server. [State schema and conventions](skills/assumption-hunter/references/state-format.md)

## Review and development

An audit can surface uncertain or contradictory claims. Its accuracy depends on the inspected evidence, and the schema validator only verifies shape and invariants. Review conclusions and experiment thresholds before acting. Audits and re-audits run on demand. The skill treats instructions embedded in evidence as data and requires user authorization for write operations and external transfers.

```sh
uv sync --locked --extra mcp
uv run --locked --extra mcp pytest -q
uv run --locked --extra mcp ruff check .
```

The test suite covers malformed snapshots, source paths, scoring, diffs, persistence, and real MCP stdio calls. Use the [synthetic evaluation cases](examples/evaluation.md) to review audit quality with a host model.

[MIT License](LICENSE) · [Agent Skills specification](https://agentskills.io/specification)
