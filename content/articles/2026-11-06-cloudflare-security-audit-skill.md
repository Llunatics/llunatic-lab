---
title: "Turn Your Coding Agent Into a Security Auditor: Inside Cloudflare's Security-Audit Skill"
date: 2026-11-06
tags: [tools, ai-security, code-audit, cloudflare]
excerpt: "Cloudflare open-sourced the skill that seeded its fleet-wide vulnerability discovery harness: a six-phase audit workflow where a fresh agent tries to disprove every finding before it counts. Here's how it works, what it costs, and the sandbox rule you must not skip."
cover: /assets/covers/cloudflare-security-audit-skill.jpg
---

Ask a coding agent to "review this code for security issues" and you will get an answer. Ask it twice and you will get two different answers. Ask it to prove the bug is real and it will usually just repeat itself more confidently. That is the gap Cloudflare's security team ran into when it tried to turn AI code review into something it could run across its fleet — and it is the gap the company's newly open-sourced `security-audit-skill` is built to close.

The repository, `cloudflare/security-audit-skill`, is MIT licensed and picked up tens of thousands of GitHub stars within weeks of release. But the star count is the least interesting thing about it. What matters is the design: it does not trust the model that found the bug. Every candidate finding is handed to a fresh agent whose only job is to disprove it — and only the findings that survive that attack get filed as confirmed.

## Where it came from

In June 2026, Cloudflare published a blog post, "Build your own vulnerability harness", describing how the team went from a single skill to a multi-stage system. The starting point was a roughly 450-line [[agent skill]] run against one repository, tuned until it surfaced real bugs. From the first slash-command run to a scanner covering 128 repositories took about six weeks. Along the way the team hit three walls a single skill cannot solve: context exhaustion, no persistence after a crash, and no cross-repo reasoning. The open-source repo is that single-repo starting point — the seed the harness grew from, not the harness itself. One detail from that post explains most of the design: Cloudflare uses one model for discovery and a different model for validation, so the two double-check each other.

## The six phases

A full audit runs as a pipeline, and each stage hands structured state to the next instead of passing prose around:

1. **Reconnaissance.** Map the architecture, trust boundaries, input surfaces, and prior evidence into `architecture.md` and a [[coverage ledger]] (`coverage-ledger.json`) — a deterministic record of what exists, and therefore what must be examined.
2. **Coverage-led hunting.** Isolated hunter agents are assigned units drawn from the ledger, record every check they perform, and coverage critics hunt for the gaps the hunters left.
3. **Candidate validation.** Every unique candidate goes to a fresh verifier whose instruction is to disprove it.
4. **Structured output.** Findings are written as `confirmed`, `needs_validation`, or `rejected` records in `findings.json`, validated against a JSON schema (`report-schema.json`).
5. **Independent record verification.** Fresh agents re-check the final source claims, and any material replacement gets yet another independent verifier.
6. **Target-neutral reporting.** Human-readable `REPORT.md`, `FINDINGS-DETAIL.md`, and `NEEDS-VALIDATION.md` are derived from the verified records and the coverage ledger.

Two small scripts enforce the structure instead of trusting the model to hold the format: `validate-coverage-ledger.cjs` runs after the ledger is created and after each update, and `validate-findings.cjs` runs in phase 4 and after every phase 5 replacement. Both are zero-dependency Node scripts, so the discipline does not depend on the model's memory.

The skill ships with eleven domain attack matrices — memory safety and binaries, AI and LLM targets, web protocols and auth, client-side code, [[supply chain attack]] and release, cloud and deployment, RPC and messaging, resource exhaustion, data isolation, and desktop, mobile, and local IPC. It picks the classes that match the target, so a TypeScript web app does not get kernel-fuzzing prompts.

## The three verdicts — and why the middle one matters most

| Verdict | Meaning |
|---|---|
| `confirmed` | Complete source trace and a bounded, observed result |
| `needs_validation` | An exact unresolved fact, and no severity assigned |
| `rejected` | A candidate that was disproved |

The middle category is the useful one. Most AI audit tools present every suspicion as a finding. Here, a lead that cannot be proven stays labeled as unproven, with the specific question that blocks it. An independent field test of the skill reported 46 records from one codebase: 10 confirmed and 36 held at `needs_validation`, each with the exact fact a human would need to resolve.

Five design principles sit underneath the workflow, and they read like a checklist for any agentic review:

- **Only confirm established boundary failures.** A blocked but source-grounded lead stays `needs_validation`.
- **[[Adversarial validation]].** The agent that checks a finding is never the agent that found it.
- **Severity requires impact.** Likelihood times impact, not deviation from a checklist.
- **Defense-in-depth gaps are not vulnerabilities.** If layer A prevents the attack, the missing layer B is a hardening note.
- **Multiple runs improve coverage.** Cloudflare says a single run found roughly half of what repeated runs found in total.

## How to install and run it

Install with the Skills CLI:

```bash
npx skills add https://github.com/cloudflare/security-audit-skill \
  --skill security-audit
```

Add `--global` for a user-level install. Then start your coding agent — Claude Code, Codex, Cursor, or another agent with tool use and parallel sub-agents — in the target codebase and ask in plain language:

```text
security audit this codebase
find security vulnerabilities in ./src
do a security review, output to ~/audits/my-project
```

A direct audit request uses full audit mode; security questions and focused [[vulnerability]] work use a lighter guidance mode unless you ask for report artifacts. In full mode, an unspecified output directory defaults to `~/security-audit-skill/<repo-name>/run-<N>`, and the workflow writes inside the target repository only if you explicitly choose a directory there. Repeat runs are additive: they reuse the prior ledger to target gaps and revalidate changed source instead of starting from zero.

## The requirement people skip: the sandbox

The README is explicit about what you need: a coding agent whose model supports tool use and parallel sub-agents, Node.js for the validators, and an OS-enforced [[sandbox]] for anything target-controlled — builds, tests, processes, browsers, emulators, fuzzers, fixtures. That sandbox must disable external networking, use a sanitized allowlisted environment, enforce resource limits, and allow writes only to assigned scratch paths. Without those controls, the workflow keeps the lead as `needs_validation` instead of executing target code.

Why it matters: to validate a bug, the skill may build and run the code under audit, and an untrusted repository can execute anything in its build scripts. If you point this at code you did not write, treat the sandbox as mandatory. This is the same class of risk as [[prompt injection]] and [[tool poisoning]] in [[MCP]] servers — only here the skill itself is the one running the code. A container or VM with networking disabled is the minimum; a bare host checkout is not a place to run this.

## What it costs, and what it does not promise

The honest part of the story is the cost. Cloudflare publishes no per-run token figure in the README. One Hacker News commenter reported spending about 1M tokens on a medium codebase without a result to show for it — a single commenter's report, not a verified measurement, but consistent with what a multi-agent, multi-phase audit should cost. The fair reply to skeptics who call it "just a markdown file" is that the value lies in the orchestration and the validators, not in any one prompt — they make the output machine-checkable, which a plain code-review prompt does not.

Cloudflare has also not published precision or false-positive rates for the open-source skill, and how many real vulnerabilities it has found outside Cloudflare's own fleet is unknown. Treat it as what it is: a strong starting point for structured auditing, not a scanner with a benchmark.

## What to do this week

1. **Run it on a repo you own**, inside a container or VM with networking disabled.
2. **Run it at least twice.** Repeat runs find more, and the skill uses prior ledgers to target gaps.
3. **Read `NEEDS-VALIDATION.md` first.** The unresolved leads show where the agent could not prove something — and what fact is missing.
4. **Do not file bug reports from `confirmed` records without reading the source trace yourself.** A verified trace is still a claim until a human reads it.
5. **Track token cost per run** before scheduling it in CI.

The bigger pattern here is worth naming. Labs and vendors are moving from "can a model find a bug" to "how do you run this as a repeatable pipeline" — Anthropic's Frontier Red Team publishing AI-built exploit research, OpenAI rolling out GPT-6 Cyber to vetted customers, Trail of Bits publishing agent plugins for patching. Cloudflare's contribution is the least glamorous and possibly the most useful: a workflow that assumes the finder is wrong until a stranger proves it right. That is not how most AI tools are built. It is how audits are supposed to work.

---

*Sources: [Cloudflare security-audit-skill: 6 Phases, 25.6k Stars (explainx.ai, November 2026)](https://explainx.ai/blog/cloudflare-security-audit-skill-open-source-agent-vulnerability-hunting-2026); [Cloudflare Security Audit Skill for Claude Code (devpik.com)](https://www.devpik.com/open-source/security-audit-skill); [Who Audits the Agent? Security Review Is a Category (dev.to, November 2026)](https://dev.to/max_quimby/who-audits-the-agent-security-review-is-a-category-g4e); [Field notes: running Cloudflare's open-source security-audit-skill on a real codebase (norforge.com)](https://norforge.com/blog/field-notes-cloudflare-security-audit-skill); [cloudflare/security-audit-skill (GitHub)](https://github.com/cloudflare/security-audit-skill).*
