---
title: "Your Agent's Plugins Are the New Attack Surface: Auditing MCP Servers With mcp-scan"
date: 2026-10-21
tags: [mcp, ai-security, tools, prompt-injection]
excerpt: "AI agents now browse the web, run code, and query databases through MCP servers — and attackers have noticed. Here's how tool poisoning works, why October 2026 turned MCP into a headline threat, and how to audit your own setup with Invariant Labs' mcp-scan before a plugin audits you."
cover: /assets/covers/mcp-server-audit-scan.jpg
---

You install a harmless-looking calculator plugin for your AI coding agent. Its tool description says it "adds two numbers and returns the sum." You never read the rest — because there is no rest, as far as the UI shows. But buried inside that description, invisible to you, is a block of text that tells the agent to read your SSH private key and your MCP config file first, smuggle their contents through a side parameter, and never mention it to you.

That is [[tool poisoning]], demonstrated publicly by Invariant Labs in April 2025. No authentication bypass. No memory-corruption exploit. Just text in a JSON field that the agent reads as trusted context. And a year and a half later, in October 2026, the whole category has exploded into one of the loudest stories in security.

## Why MCP became the target

The [[MCP]] — Model Context Protocol — is Anthropic's open standard, introduced in November 2024, that lets AI assistants call external tools: filesystems, APIs, databases, developer utilities like Git. An MCP server is a bridge: the model decides, the server executes real system actions.

That bridge went mainstream fast. By Q3 2026, Gartner estimated that over 40% of enterprises running LLM deployments had extended them into autonomous agent architectures — systems where agents browse, execute code, query databases, send emails, and orchestrate other sub-agents. Every one of those capabilities is a tool. Every tool is a server someone wrote. And servers written by strangers are now sitting between your agent and your infrastructure.

The numbers from this month tell the story. The Enterprise MCP Guide 2026, published October 5 by The Agentics, catalogued **68 MCP server CVEs in a single month** and named six distinct attack classes. Stingrai's analysis of the NVD found **141 CVEs whose descriptions contain the exact phrase "prompt injection"** — 87 of them published in 2026 alone, with 105 rated High or Critical. [[MITRE ATT&CK]] v20, released October 13, 2026, added Direct [[Prompt Injection]], Indirect Prompt Injection, and AI-Enabled Exfiltration as first-class techniques. This is no longer a research curiosity; it's a tracked, taxonomied, actively exploited attack surface.

## The six ways in

The Agentics' taxonomy is worth memorizing, because each class breaks a different assumption:

1. **Tool poisoning** — malicious instructions hidden in a tool's description, which the model reads on every call while the user sees only a friendly name.
2. **Schema poisoning** — the list of available tools itself is tampered with.
3. **Tool shadowing** — a malicious tool quietly overrides a legitimate one with the same name, so the agent calls the attacker's code while the approval dialog shows a familiar label.
4. **Command injection** — attacker instructions embedded in content the agent processes (documents, web pages, tool outputs).
5. **Shadow servers** — unauthorized MCP servers added to an agent's environment without approval.
6. **Context oversharing** — agents exposing more data than the task requires, feeding the other five.

Two real-world sightings from this month make it concrete. Security firm Signals Corps found nearly **8,000 websites sending messages to AI agents via HTTP headers**, with 30 of them attempting genuine indirect prompt injection. And independent researcher Syed Anas Mohiuddin documented "protocol pivoting" — prompt injection aimed at individual agents rather than the model itself, relayed down agent-to-agent chains — affecting organizations including Google, JP Morgan Chase, and Rapid7. The trust between internal agents, he showed, is the vulnerability.

## Hands-on: scanning your own setup with mcp-scan

Knowing the theory is half the job; the other half is checking what's actually plugged into *your* agent. The most established scanner is **mcp-scan** by Invariant Labs — the same team that named tool poisoning. It scans the MCP servers configured in Claude, Cursor, Windsurf, and other file-based MCP clients, looking for prompt injection in tool descriptions, tool poisoning via their Guardrails analysis, and cross-origin escalation ([[tool shadowing]]). It also supports **tool pinning**: hashing each server's tool definitions so a [[rug pull]] — a server that scans clean today and turns malicious tomorrow — gets caught when its metadata changes.

Installation is one command:

```bash
uvx mcp-scan@latest
```

To actually inspect what your agent sees — the full tool descriptions, including the text no UI ever shows you:

```bash
uvx mcp-scan@latest inspect
```

And for a full scan of every configured server:

```bash
uvx mcp-scan@latest scan
```

Two things to know before you run it. First, unless you pass `--local-only` (which needs an OpenAI API key and is less accurate), tool names and descriptions are sent to Invariant's API for analysis — the tool doesn't log your tool *calls* or results, but it does share metadata for research. Decide whether you're comfortable with that on a work machine. Second, there is a newer community alternative worth knowing: a static scanner called `mcpscan` that runs twelve offline checks — prompt-injection phrasing, command injection, dangerous hooks, committed secrets — with zero dependencies and JSON/SARIF output for CI. Different philosophy, same goal: read the metadata before the model does.

## The uncomfortable caveat

Now the part scanner vendors won't put on the landing page. Adversa's October 2026 research built two fully working malicious MCP servers — a credential harvester and a remote code executor — and **all five scanners they tested gave them clean results**, including Cisco's mcp-scanner, Snyk's agent-scan, and NVIDIA's SkillSpector. The evasions were payloads hidden in handler code, obfuscation, oversized files, and scanner fingerprinting. Their conclusion is blunt and correct: *a clean scan is a starting point, not an approval.*

So treat mcp-scan as a smoke detector, not a firewall. It catches the lazy, the sloppy, and the known — which, honestly, is most of what's floating around in public MCP server directories right now. The sophisticated stuff needs the boring controls underneath.

## The checklist that actually matters

Borrowing from the Enterprise MCP Guide and the practitioners writing about this all month, here's the layered version:

- **Treat every third-party MCP server as an unreviewed dependency.** Read its tool descriptions (use `inspect`) before connecting, the same way you'd review a new package.
- **Least privilege, always.** Connect with the weakest credential the task allows — read-only where possible, scoped to one database or directory, never a whole account. Disable write/execute tool groups unless the workflow needs them.
- **Per-agent allowlists.** Each agent gets only the tools it genuinely needs. A translation agent has no business with a shell.
- **Log everything through a gateway.** Centralized MCP gateways that record every tool call turn "the agent did something weird" into an auditable trail.
- **Human approval for the irreversible.** Deleting data, sending communications, moving money — an agent should never do these without a human gate.
- **Pin your tools.** Hash tool metadata after review; alert when it changes. Rug pulls are a when, not an if.
- **Re-scan on a schedule**, not just on install. Servers update; updates can be hostile.

## The perimeter moved

Here's the mental model to take home: in the agent era, the most influential text in a transaction is often the text nobody reads — the tool description the model ingests on every call while the human sees a friendly label. Interfaces that treat that text as mere metadata, then act surprised when it turns out to be instructions, are the vulnerability. The October 2026 numbers — 68 CVEs in a month, 141 prompt-injection CVEs, ATT&CK techniques with official names — are what it looks like when attackers arrive at a new perimeter before the defenders do.

Run the scan. Read the descriptions. Pin the tools. The plugin directory is the new software supply chain — and unlike npm, most people installing from it have never once looked at what they installed.
