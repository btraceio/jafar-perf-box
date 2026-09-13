# jafar-perf-box

A Claude Code plugin marketplace for the [Jafar](https://github.com/btraceio/jafar) JFR / heap dump
/ profile analysis toolkit.

```
/plugin marketplace add btraceio/jafar-perf-box
/plugin install jafar-perf@btraceio
```

Two names, because they name two different things: **`jafar-perf-box`** is this repository, which is
the *marketplace*, and **`jafar-perf`** is the *plugin* inside it. `@btraceio` is the marketplace's
name as declared in `.claude-plugin/marketplace.json`, not the GitHub organisation. So you add the
repository and install the plugin.

This repository is deliberately small — a few hundred kilobytes of Markdown. Adding a marketplace
clones its repository, so the plugin lives here rather than in the Jafar source tree, which carries
several megabytes of binary test recordings that a plugin user has no use for.

## What is in it

**`jafar-perf`** — the methodology layer over Jafar's MCP server: nine skills (`triage`, `cpu`,
`latency`, `gc`, `memory-leak`, `heap-diff`, `compare`, `jfrpath`, `report`) and seven agents that
know *which* analysis to run on an unfamiliar recording or heap dump, not just how to run one. See
[plugins/jafar-perf/README.md](plugins/jafar-perf/README.md).

The plugin bundles `.mcp.json`, so installing it also registers the `jafar` MCP server
(`jbang jfr-mcp@btraceio --stdio`). [JBang](https://www.jbang.dev) must be on your PATH; it fetches
the server on first use. No separate `claude mcp add` is needed.

## Keeping the skills honest

The skills name MCP tools and their parameters explicitly. Nothing in Jafar's test suite knows this
repository exists, so a tool renamed there turns a skill here into confident instructions for a call
that fails — the one real cost of keeping the plugin separate.

`scripts/check_tool_references.py` closes it. It starts the published server the same way the README
tells users to, asks it for `tools/list`, and fails if any name in a skill or agent is missing,
reporting the exact file and line. Run it locally against a build of your own:

```
python3 scripts/check_tool_references.py --jar path/to/jfr-mcp-all.jar
```

The [`tool-drift`](.github/workflows/tool-drift.yml) workflow runs it weekly, not only on push:
the drift originates in *another* repository, so a push trigger would never fire at the moment it
matters. A failing scheduled run opens an issue, because nobody watches a cron job.

## Relationship to the Jafar repository

The plugin drives the MCP tools built in [btraceio/jafar](https://github.com/btraceio/jafar). When a
tool's output shape changes there, the affected skill changes here — the two are versioned
separately, so a skill referencing a tool that does not exist in the user's installed server is the
failure mode to watch for. Each skill names the tools it uses.
