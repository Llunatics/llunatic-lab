---
title: "From PoC to Detection in Minutes: Your First Nuclei Template"
date: 2026-10-19
tags: [nuclei, vulnerability-scanning, hands-on, tools]
excerpt: "When a critical CVE drops, exploit PoCs hit GitHub within hours — and mass scanning follows. Nuclei lets you scan your own estate just as fast by turning a proof of concept into a shareable YAML template. Here's how the tool works, how to write your first template, and the guardrails that keep it from burning you."
cover: /assets/covers/nuclei-poc-to-template.jpg
---

A critical [[CVE]] drops on a Tuesday morning. By lunch, someone has published a working exploit [[proof of concept]]. By evening, botnets are mass-scanning the internet for it. Somewhere between "published" and "pwned" there is a window measured in hours — and the only real question is who scans *your* infrastructure first: you, or them.

That race is exactly why [[Nuclei]] exists. Built by ProjectDiscovery as an open-source scanner written in Go, it doesn't ship with a fixed checklist of checks. Instead it ships with an engine — and the checks themselves are plain YAML files called templates. The community maintains more than 12,000 of them, covering CVEs, misconfigurations, exposed files, and default credentials, and the project has earned tens of thousands of GitHub stars precisely because the model works: the moment a new [[vulnerability]] is understood, anyone can encode it as a template and share it.

## The idea: vulnerability as code

A template is a [[vulnerability]] description that a machine can execute. It says: send *this* request, look for *that* in the response, and call it a finding if it matches. The format is YAML, the learning curve is an afternoon, and the payoff is that your detection logic travels — from one analyst's laptop into CI pipelines, nightly scans, and team-wide automation.

Here's a real, runnable example. It detects an exposed `.git/HEAD` file — the classic "we deployed the repository" mistake that leaks branch names and commit hashes:

```yaml
id: git-head-exposure

info:
  name: Exposed Git HEAD Detection
  author: llunatic
  severity: medium
  description: Detects publicly accessible .git/HEAD files leaking repository metadata.
  tags: exposure,git,config

http:
  - method: GET
    path:
      - "{{BaseURL}}/.git/HEAD"

    matchers:
      - type: word
        words:
          - "ref: refs/heads"
        condition: and
```

Read it top to bottom: the `id` is a unique slug, `info` carries the metadata humans need (name, severity, tags), and the `http` block is the machine part — one GET request, one matcher that fires only when the response literally contains `ref: refs/heads`. That matcher discipline is what separates a scanner from a noise machine: the condition must describe the vulnerable state, not merely "the server answered."

Matchers come in flavors — `word`, `regex`, `status`, `binary`, `dsl` — and they compose with `and`/`or`. The DSL flavor is the power tool: you can write expressions over the response like `contains(body, 'admin') && status_code == 200`, which is how researchers encode the subtle logic of real exploit PoCs.

## Running it: the five-minute setup

```bash
# install (Go 1.24+)
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest

# pull the community template library
nuclei -update-templates

# scan one target, high and critical findings only
nuclei -u https://your-target.example -severity high,critical -silent
```

A few flags do most of the heavy lifting. `-t` selects which templates run (a directory like `exposures/`, a tag, or a single file). `-severity` filters the noise. `-tc` lets you write template conditions such as `"contains(tags, 'xss') && contains(tags, 'cve')"`. And `-as` runs an automatic scan that fingerprints the target's technology stack first — Wappalyzer-style — and then fires only the templates relevant to what it found, so you're not throwing WordPress checks at a Django app.

The engine is fast by default — tunable rate limits, parallel hosts, and parallel templates — which is exactly why you must point it only at what you own. Nuclei sends real requests and real probes. Running it against infrastructure you aren't authorized to test isn't "research"; in most jurisdictions it's a legal problem. Scope it, get sign-off, log what you scan.

## The pipeline: recon into scanning

Nuclei rarely runs alone. The standard community pattern chains it behind reconnaissance, each tool feeding the next through stdin:

```bash
subfinder -d example.com -silent \
  | httpx -silent \
  | nuclei -t exposures/ -severity medium,high,critical -o findings.txt
```

`subfinder` enumerates subdomains, `httpx` keeps only the live ones, and Nuclei checks the survivors for exposures. Never scan a raw subdomain list directly — dead hosts just burn time and quota. Results land in JSON, JSONL, SARIF, or Markdown, ready for `jq` triage or a ticketing system.

## From PoC to template: the conversion

Here's the workflow that wins the Tuesday-morning race. A researcher publishes a PoC for a new CVE — say, a path-traversal where requesting `/download?file=../../../../etc/passwd` returns the file's contents. Converting it is mechanical:

1. **Reproduce** the PoC against a lab target and capture the exact request and response.
2. **Identify the invariant** — the part of the response that only a vulnerable server produces (e.g., the string `root:x:0:0`).
3. **Encode it**: one `http` request block with the payload path, one `word` matcher on the invariant, severity and CVE metadata in `info`.
4. **Validate** against a known-vulnerable and a known-patched target. A template that fires on both is worse than no template.

When the invariant is behavioral rather than textual — a timing delay, a DNS callback — Nuclei's `interactsh` integration handles out-of-band detection: the template plants a unique callback URL and the finding fires when the target phones home.

## The guardrails (learned the hard way)

Two advisories from the Nuclei v3.8.0 release (April 18, 2026) are worth every scanner operator's attention: GHSA-29rg-wmcw-hpf4, where a JavaScript-protocol template could read local files outside its sandbox, and GHSA-jm34-66cf-qpvr, where expressions evaluated from non-template sources opened a remote-code-execution vector from malicious templates. The lesson is blunt: **templates are code, and code from strangers runs with your privileges.** Pull templates from sources you trust, pin versions you audit, and upgrade promptly — the same release also shipped PDF result export, an XSS reflection-context analyzer, and a honeypot detector, so staying current pays twice.

And the oldest guardrail still applies: a scanner tells you *where to look*, not *what is true*. Every finding deserves manual verification before it becomes a ticket, a report, or a 2 AM page.

## What to build this week

If you're on the defensive side, the highest-leverage move is boring: a nightly Nuclei run against your external asset list, cross-matched with the freshest [[KEV]] feed, with findings routed somewhere a human reads them. The gap that gets organizations breached is rarely exploit sophistication — it's the weeks a known-vulnerable system sits exposed between disclosure and someone actually checking. A scanner that runs nightly closes that gap. One that runs quarterly doesn't.

The exploit clock starts the moment a PoC is published. With a template engine in your hands, your detection clock can start at the same moment. Write the template, scan the estate, patch before lunch — and the Tuesday-morning CVE becomes a routine Tuesday, not an incident.
