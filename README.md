# jafar-perf-box

A Claude Code plugin marketplace for the [Jafar](https://github.com/btraceio/jafar) JFR / heap dump
/ profile analysis toolkit.

```
/plugin marketplace add btraceio/jafar-perf-box
/plugin install jafar-perf@btraceio
```

`jafar-perf-box` is this repository — the *marketplace*. `jafar-perf` is the *plugin* inside it,
declared under the `@btraceio` marketplace name in `.claude-plugin/marketplace.json` (not the
GitHub organisation name). You add the repository and install the plugin.

## What is in it

**`jafar-perf`** — the methodology layer over Jafar's MCP server: nine skills (`triage`, `cpu`,
`latency`, `gc`, `memory-leak`, `heap-diff`, `compare`, `jfrpath`, `report`) and seven agents that
know *which* analysis to run on an unfamiliar recording or heap dump, not just how to run one. See
[plugins/jafar-perf/README.md](plugins/jafar-perf/README.md).

The plugin bundles `.mcp.json`, so installing it also registers the `jafar` MCP server
(`jbang jfr-mcp@btraceio --stdio`). [JBang](https://www.jbang.dev) must be on your PATH; it fetches
the server on first use. No separate `claude mcp add` is needed.

## Keeping the skills honest

The skills name MCP tools and their parameters explicitly. `scripts/check_tool_references.py`
starts the published server the same way the README above tells users to, asks it for
`tools/list`, and fails if any name referenced by a skill or agent is missing, reporting the exact
file and line. Run it locally against a build of your own:

```
python3 scripts/check_tool_references.py --jar path/to/jfr-mcp-all.jar
```

The [`tool-drift`](.github/workflows/tool-drift.yml) workflow runs it weekly and opens an issue on
a failing run.

## Relationship to the Jafar repository

The plugin drives the MCP tools built in [btraceio/jafar](https://github.com/btraceio/jafar). The
two repositories are versioned separately: if a tool's output shape changes there, the affected
skill needs to change here. Each skill names the tools it uses.
