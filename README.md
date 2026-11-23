# Assumption Hunter

[![CI](https://github.com/aryandas079/assumption-hunter/actions/workflows/ci.yml/badge.svg)](https://github.com/aryandas079/assumption-hunter/actions/workflows/ci.yml)
[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Find the assumptions that could derail a plan, design, or research proposal. Assumption Hunter helps Codex and Claude Code cite evidence for each premise, flag the most consequential unknowns, and propose a test that could change the decision. Save snapshots to see what changes on the next audit.

## Install

The plugins include the skill and a local MCP server. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and make sure it is on your PATH before starting your host.

### Codex CLI

Install the [Codex CLI](https://learn.chatgpt.com/docs/cli) and check that `codex --version` works in your terminal. On Windows with Node.js installed, you can install the CLI with `npm.cmd install -g @openai/codex`. Open a new PowerShell window after installation so it picks up your PATH.

Then run:

```sh
codex plugin marketplace add aryandas079/assumption-hunter
codex plugin add assumption-hunter@assumption-hunter-marketplace
```

Open a new Codex session and type `$assumption-hunter`.

### Claude Code

Run inside a Claude Code session:

```text
/plugin marketplace add aryandas079/assumption-hunter
/plugin install assumption-hunter@assumption-hunter-marketplace
/reload-plugins
```

Type `/assumption-hunter:assumption-hunter`.

### Install just the skill

Download and extract the [skill ZIP](https://github.com/aryandas079/assumption-hunter/releases/latest/download/assumption-hunter-skill.zip). Copy the entire `assumption-hunter` folder into one of these locations inside the project you want to audit, then start a new session in that project.

| Host | Project location | Invoke |
| --- | --- | --- |
| Codex CLI or IDE | `.agents/skills/assumption-hunter/` | `$assumption-hunter` |
| Claude Code | `.claude/skills/assumption-hunter/` | `/assumption-hunter` |

The instructions work on their own. The offline scripts require Python 3.11 or later. If you clone the repo, the folder to copy is [`skills/assumption-hunter`](skills/assumption-hunter).

## Run your first audit

> Use Assumption Hunter to stress-test this plan. Cite the evidence for each critical premise and suggest the smallest test that could change our decision.

Ask it to save a snapshot if you want to track changes. On a later audit, provide the previous snapshot and ask what changed and why. The CLI can preserve history in the project's `.assumption-hunter/` directory. [Snapshot format and save commands](skills/assumption-hunter/references/state-format.md)

To see a complete example, read the [synthetic receipt queue design](examples/receipt-queue.md). The [first snapshot](skills/assumption-hunter/assets/assumptions.example.json) marks duplicate receipts as a possibility. The [updated snapshot](examples/updated.json) records a staged redelivery that produced two receipt rows.

## Use MCP on its own

If you installed a bundled plugin, its MCP server is already configured. For another local stdio client, clone the repo and configure the command below. Replace `/path/to/assumption-hunter` with the absolute path to your clone in both arguments.

```sh
uv run --locked --no-dev --extra mcp --project "/path/to/assumption-hunter" python "/path/to/assumption-hunter/skills/assumption-hunter/scripts/mcp_server.py"
```

For Codex, prefix the command with `codex mcp add assumption_hunter --`. For Claude Code, prefix it with `claude mcp add --transport stdio --scope user assumption_hunter --`. Open a new host session after registering it. [Codex MCP setup](https://learn.chatgpt.com/docs/extend/mcp?surface=cli) · [Claude Code MCP setup](https://code.claude.com/docs/en/mcp)

The server exposes `get_audit_guide`, `validate_audit_snapshot`, `rank_audit_assumptions`, and `compare_audit_snapshots`. It takes snapshot JSON text and reads only its bundled guides. The host interprets evidence and makes audit judgments.

## Development

From the repository root:

```sh
uv sync --locked --extra mcp
uv run --locked --extra mcp ruff check .
uv run --locked --extra mcp pytest -q
```

[Audit methodology](skills/assumption-hunter/references/methodology.md) · [Evidence policy](skills/assumption-hunter/references/evidence-policy.md) · [Evaluation cases](examples/evaluation.md)

## License

Assumption Hunter is open source under the [MIT License](LICENSE).
