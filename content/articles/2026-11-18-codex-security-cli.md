---
title: "Codex Security CLI: OpenAI's Open-Source Scanner That Finds, Validates, and Fixes Bugs"
date: 2026-11-18
tags: [tools, ai-security, code-audit, openai]
excerpt: "OpenAI's codex-security CLI scans your repo, argues with its own findings until only the real ones survive, then drafts the patch and re-checks it. Version 0.10.0 just made it resumable, budget-capped, and CI-ready — here's how to run it, and the two catches nobody should skip."
cover: /assets/covers/codex-security-cli.jpg
---

Most AI code reviewers have the same flaw: they never doubt themselves. Point one at a repository and it returns a confident list of vulnerabilities, half of which evaporate the moment a human reads the source. OpenAI's answer to that problem is `codex-security` — a command-line scanner that treats its own findings as suspects, not verdicts. It finds candidate bugs, tries to disprove each one, generates a patch for the survivors, and then re-checks the fix. The tool has been public since late July 2026, but version 0.10.0, released on 12 November, is what pushed it onto GitHub's trending page and past 13,000 stars in a matter of days.

## What it actually is

Codex Security is OpenAI's CLI and TypeScript SDK for finding, validating, and fixing security vulnerabilities in your own code. It ships as the npm package `@openai/codex-security`, licensed Apache-2.0, with the source at `github.com/openai/codex-security`. You can use it three ways: as a plugin inside Codex, from the terminal with the `cs` command, or in automation through the SDK or a GitHub Action.

The repository was created on 13 July 2026 and open-sourced in late July, with the first npm release, 0.1.0, landing on 31 July. For three months it grew quietly. Then the 0.10.0 release on 12 November coincided with OpenAI's "Cyber at the Frontier" keynote — the same day the company announced Daybreak Red Team and Defense Factory, its managed offensive and defensive agent products. Codex Security is the open, self-hosted building block underneath that story: the part you can install and run yourself, rather than buy as a service.

The star count tells the story of the surge: about 12,900 stars on 13 November, roughly 13,350 the next day, and close to 13,900 by 17 November — more than 2,000 new stars in a single week.

## How a scan works: find, validate, patch, re-check

The workflow has four stages, and the second one is the whole point:

1. **Find.** The scanner reads your repository — a full tree, a selected path, or just the changes in a git diff — and proposes candidate vulnerabilities.
2. **Validate.** Each candidate is checked against the source before it is reported. The design goal is explicit: a finding from the source is not necessarily a reproduced exploit, and an unconfirmed suspicion should not reach you dressed as a fact. This is the step most AI reviewers skip, and it is why the tool's output is meant to be shorter and more trustworthy than a raw model dump.
3. **Patch.** For validated findings, it drafts a fix.
4. **Re-check.** It verifies the fix actually addresses the finding, rather than assuming the patch worked.

Deep scans repeat Standard scans and return deduplicated findings, so a second pass is meant to catch what the first missed rather than repeat it. The scanner covers Python, JavaScript, TypeScript, Go, Java, C, C++, Rust, Ruby, and PHP.

It also plays well with tools you already run. Findings from existing scanners can be imported — importers for AWS and CrowdStrike arrived in the week before 0.10.0, and 0.10.0 itself added ArmorCode [[SAST]] imports — and results export as [[SARIF]], JSON, or CSV, with tracking into Linear, Jira, or GitHub. The obvious use is a security step in CI that a coding agent can act on, rather than a PDF nobody reads.

## Install and run it

Requirements are Node.js 22.13.0 or later within the 22.x line, or 24.x or 26.x, plus Python 3.10 or later. Install globally and sign in:

```bash
npm install --global @openai/codex-security
cs login
```

Then scan from inside the repository:

```bash
cs scan .
```

`cs` and `codex-security` are the same command — use the long form if the short name conflicts with something else on your system, or `npx @openai/codex-security` to skip the global install entirely. Scope the scan with flags:

```bash
# Only one directory
cs scan . --path src/auth/

# Only what changed against main — the pull-request workflow
cs scan . --diff origin/main

# Cap the spend and fail CI on high-severity findings
cs scan . --max-cost 5.00 --fail-on-severity high
```

In CI, skip the interactive login and set `OPENAI_API_KEY` or `CODEX_API_KEY` instead. The GitHub Action example caps each scan at an estimated $5 — a cap, not a price, but a useful default to copy. For bulk work across many repositories, the repo ships a Docker Compose configuration built on the `ghcr.io/openai/codex-security` image. And if you want it in code rather than on the command line, the SDK is one import away:

```typescript
import { CodexSecurity } from "@openai/codex-security";
```

## What's new in 0.10.0

Three changes matter in practice:

- **Resumable scans.** An interrupted Standard scan can be picked up where it stopped with `cs scans resume SCAN_ID`, instead of starting over and paying twice.
- **A shared cost budget.** `--max-total-cost` puts one budget across a batch of scans, which is what you actually want when a nightly job sweeps dozens of repositories.
- **Clearer blocked-patch explanations.** When a fix cannot be applied, the tool now says why instead of failing silently — the difference between a dead end and a next step.

None of this changes what the scanner finds. It changes whether you can run it as a repeatable pipeline instead of a one-off experiment — the same direction the whole category is moving. Cloudflare's open-source security-audit skill, covered here two weeks ago, makes the same bet: the value is in validation and orchestration, not in the model's first guess.

## The two catches

The first is cost and access. Codex Security is open source, but it is not a free standalone scanner. Scans that use OpenAI inference require Codex Security access or an API key, and your code is sent to OpenAI's servers for analysis. Some cybersecurity requests additionally require OpenAI's Trusted Access for Cyber programme, a gated access route — not every feature is available to every user by default. The README also notes alternative inference providers, including Amazon Bedrock, OpenRouter, and Fireworks. Budget for tokens the way you would budget for any [[LLM]]-powered tool, and check the data-handling terms before pointing it at proprietary code.

The second is the one every scanner shares: a validated finding still needs a human to decide whether it matters. Version 0.10.0 is, by the project's own numbering, not a finished product. Validation cuts [[false positive]]s; it does not remove judgement. A real bug in a dead code path and a real bug on your login page are both "confirmed" — only one of them deserves your afternoon.

## What to do this week

1. **Install it and scan a repo you own** — start with `--diff origin/main` on a pull request, where the blast radius is small and the findings are fresh.
2. **Set `--max-cost` before your first full-repo scan.** Learn what a scan costs on your codebase before it runs unattended.
3. **Read the validated findings, then read the source trace behind one of them.** Trust is earned per finding, not per tool.
4. **Wire the GitHub Action into one repository** with the $5 example cap, exporting SARIF so findings land where your team already triages issues.
5. **Do not auto-merge its patches.** Let the fix sit in a pull request with its re-check result attached, and review it like any other diff.

The pattern across this month's open-source releases is hard to miss: the money has moved from generation to verification. Chrome is teaching coding agents the modern web before they write, a 10,000-star tool now puts a human between the agent and the merge, and OpenAI's scanner argues with itself before it argues with you. The tools that survive this shift will not be the ones that find the most bugs. They will be the ones whose findings you can believe — and whose patches you can merge without holding your breath.

---

*Sources: [Open Source Radar — November 14: OpenAI's Codex Security CLI (siliconnoon.com, 14 November 2026)](https://siliconnoon.com/open-source-radar-november-14-openais-codex-security-cli/); [OpenAI's Codex Security Hits 12,500 Stars (inoryva.blogspot.com, 13 November 2026)](http://inoryva.blogspot.com/2026/11/openais-codex-security-hits-12500-stars.html); [Codex Security: OpenAI's vulnerability scanner, explained (systemdesign.academy, November 2026)](https://www.systemdesign.academy/explained/codex-security); [openai/codex-security (GitHub)](https://github.com/openai/codex-security).*
