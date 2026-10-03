# jafar-perf-box

> **This repository has moved and is archived.** The `jafar-perf` plugin now lives in
> [btraceio/agent-plugins](https://github.com/btraceio/agent-plugins), alongside the other btraceio
> agent plugins, and is maintained there. Switch to it:
>
> ```
> /plugin marketplace remove btraceio
> /plugin marketplace add btraceio/agent-plugins
> /plugin install jafar-perf@btraceio-agent-plugins
> ```
>
> pi users: `pi remove git:github.com/btraceio/jafar-perf-box`, then
> `pi install git:github.com/btraceio/agent-plugins`. Or re-run Jafar's installer
> (`curl -Ls https://raw.githubusercontent.com/btraceio/jafar/main/install.sh | bash`), which
> moves both Claude Code and pi installs over for you.
>
> The plugin is unchanged apart from starting the server with `--attach` (one shared daemon instead
> of one JVM per session). What follows describes the archived layout.

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

## Using it with pi

The same skills and MCP server also install into the [pi](https://pi.dev) coding agent. The root
`package.json` makes this repository a pi package: its `pi` key points at the plugin's `skills/`
and its `.mcp.json`, so both harnesses read one copy of each.

```
pi install npm:pi-mcp-adapter
pi install git:github.com/btraceio/jafar-perf-box
```

pi has no built-in MCP support; the MCP server needs the third-party
[pi-mcp-adapter](https://github.com/nicobailon/pi-mcp-adapter) extension. The adapter exposes the
server's tools through its `mcp` proxy tool (`mcp({ tool: "jfr_open", args: {...} })`) rather than
as individual tools, and it names the server `jafar-perf-box__jafar`. The skills name tools by their
bare names, which the proxy resolves. The seven agents are Claude Code subagents and do not load in
pi, which has no subagent support of its own.

Jafar's own installer (`install.sh` in btraceio/jafar) runs both commands for you.

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
