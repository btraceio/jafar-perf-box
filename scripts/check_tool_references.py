#!/usr/bin/env python3
"""Fail when a skill or agent names an MCP tool the server does not expose.

The skills and agents in this repository name Jafar's MCP tools explicitly, and the server that
provides them is developed in a different repository (btraceio/jafar). Nothing in either repository's
tests connects the two, so a tool rename there turns a skill here into confident instructions for a
call that will fail. This script is the connection.

Ground truth is the server itself — started, handshaken, and asked `tools/list` — rather than a
regex over Jafar's Java. A tool is registered by a chain of builder calls, so parsing the source
would encode assumptions about how registration happens today; asking the server is exactly what a
Claude Code client does, and it also catches a tool that fails to register at runtime.

Usage:
  check_tool_references.py                     # default: jbang jfr-mcp@btraceio --stdio
  check_tool_references.py --jar path/to.jar   # a locally built shadow jar
  check_tool_references.py --command "..."     # any command speaking MCP over stdio
"""

import argparse
import json
import pathlib
import re
import subprocess
import sys

# The four namespaces Jafar's MCP tools live in. A token with one of these prefixes is a tool
# reference; anything else in the prose is not our business.
TOOL_TOKEN = re.compile(r"\b(?:jfr|hdump|pprof|otlp)_[a-z_]+\b")

# Agents declare their allowlist as `mcp__<server>__<tool>` in YAML frontmatter.
MCP_QUALIFIED = re.compile(r"\bmcp__[a-z0-9_]+__([a-z0-9_]+)\b")

HANDSHAKE = [
    {"jsonrpc": "2.0", "id": 1, "method": "initialize",
     "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                "clientInfo": {"name": "tool-drift-check", "version": "1"}}},
    {"jsonrpc": "2.0", "method": "notifications/initialized"},
    {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
]


def server_tools(command, timeout):
    """Returns the set of tool names the MCP server advertises."""
    stdin = "".join(json.dumps(m) + "\n" for m in HANDSHAKE)
    try:
        proc = subprocess.run(command, input=stdin, capture_output=True, text=True,
                              timeout=timeout, shell=isinstance(command, str))
    except subprocess.TimeoutExpired as e:
        # The server holds stdio open waiting for more requests; whatever it wrote before the
        # timeout is what we came for.
        out = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
    else:
        out = proc.stdout
        if not out.strip():
            sys.exit("server produced no output on stdout.\nstderr:\n" + (proc.stderr or "")[-2000:])

    for line in out.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        if msg.get("id") == 2 and "result" in msg:
            return {t["name"] for t in msg["result"].get("tools", [])}
    sys.exit("no tools/list response found in the server's output")


def referenced_tools(root):
    """Returns {tool name: [locations]} for every tool named in a skill or agent."""
    found = {}
    files = sorted(root.glob("plugins/*/skills/*/SKILL.md")) + sorted(root.glob("plugins/*/agents/*.md"))
    if not files:
        sys.exit(f"no skill or agent files found under {root} — wrong working directory?")
    for path in files:
        rel = path.relative_to(root)
        for lineno, line in enumerate(path.read_text().splitlines(), 1):
            names = set(MCP_QUALIFIED.findall(line))
            # Strip the qualified forms before scanning for bare ones, so a `tools:` line does not
            # report the same name twice.
            names |= set(TOOL_TOKEN.findall(MCP_QUALIFIED.sub("", line)))
            for name in names:
                found.setdefault(name, []).append(f"{rel}:{lineno}")
    return found


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--command", default="jbang jfr-mcp@btraceio --stdio",
                    help="command that starts the MCP server on stdio")
    ap.add_argument("--jar", help="shortcut for: java -jar <jar> --stdio")
    ap.add_argument("--timeout", type=int, default=180, help="seconds to wait for the server")
    ap.add_argument("--root", default=".", help="repository root")
    args = ap.parse_args()

    command = f"java -jar {args.jar} --stdio" if args.jar else args.command
    root = pathlib.Path(args.root).resolve()

    print(f"asking the server for its tools: {command}", flush=True)
    available = server_tools(command, args.timeout)
    print(f"server exposes {len(available)} tools\n", flush=True)

    referenced = referenced_tools(root)
    missing = {name: locs for name, locs in referenced.items() if name not in available}

    if missing:
        print("FAIL — these tools are named here but the server does not expose them:\n")
        for name in sorted(missing):
            print(f"  {name}")
            for loc in missing[name]:
                print(f"      {loc}")
        print("\nEither the tool was renamed or removed in btraceio/jafar and the skill needs")
        print("updating, or the name is a typo. Both send an agent to a call that will fail.")
        return 1

    print(f"OK — all {len(referenced)} referenced tools exist on the server.")
    unused = sorted(available - set(referenced))
    if unused:
        # Not a failure: a tool no skill mentions is a coverage gap, not a broken reference.
        print(f"\n{len(unused)} server tools are not mentioned by any skill or agent:")
        print("  " + " ".join(unused))
    return 0


if __name__ == "__main__":
    sys.exit(main())
