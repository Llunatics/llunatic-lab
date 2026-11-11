---
title: "Audit Your Own Repos for Leaked Secrets: A Hands-On Gitleaks and TruffleHog Walkthrough"
date: 2026-11-11
tags: [hands-on, secrets, gitleaks, git-security]
excerpt: "GitGuardian counted 28.65 million new hardcoded secrets on public GitHub in 2025, and attackers now go from a leaked key to a drained cloud vault in five minutes. This walkthrough sets up Gitleaks and TruffleHog on your own repos — scan the history, block the next leak at commit time, and know exactly what to rotate when one slips through."
cover: /assets/covers/audit-your-repos-for-leaked-secrets.jpg
---

Your code is probably leaking credentials right now, and the leak is not in the file you are looking at. It is in a commit from two years ago, in a `.env` file someone deleted but never purged, in an MCP config that got committed alongside a dotfile backup. On October 13, 2026, Meta told SecurityWeek it was notifying roughly 1,500 people — mostly its own US employees — after intruders used stolen employee credentials to reach its GitHub repositories. The repositories held secrets as well as code, and Meta rotated them. The company was not breached through a product vulnerability. Someone's credentials opened the front door, and the secrets were simply sitting inside.

That is the normal shape of a secrets incident. GitGuardian counted 28.65 million new [[hardcoded secret]]s on public GitHub in 2025, up 34% on the year before, and more than 64% of the secrets it confirmed valid in 2022 were still valid when retested in January 2026. Secrets leaked to AI services rose 81% year over year, to 1,275,105. And the window between leak and abuse has collapsed: Microsoft observed an agentic framework go from a GitHub secret search to exfiltrating an Azure Key Vault in five minutes. Five minutes is not enough time to notice an alert, let alone hold a meeting about one. The only defence that works at that speed is one that was already in place before the leak happened.

This article builds that defence on your own machine, hands-on: scan the history you already have, block new leaks at commit time, catch the rest in CI, and keep a rotation runbook ready for the day something slips through. The tools are free and open source — [[Gitleaks]] v8.30.1 and [[TruffleHog]] v3.99.3, versions verified on October 20, 2026 — and the whole setup takes about an hour.

## Why `grep` is not an audit

The first mistake is reaching for `grep -r "API_KEY" .`. That only searches the files that exist right now. A secret committed in 2023 and deleted in 2024 is invisible to it — but it is still sitting in git history, one `git log -p` away from anyone who clones the repository. Any audit that does not walk every commit is a performance, not a check.

The two scanners in this walkthrough attack the problem from opposite directions, which is why they work well together. Gitleaks is regex- and [[entropy]]-based: it matches known credential formats (AWS keys, GitHub tokens, Stripe keys, hundreds more) and flags high-entropy strings that look random enough to be a secret. It is fast, works offline, and is ideal for a hook that runs on every commit. TruffleHog classifies over 800 secret types and, crucially, can *verify* a candidate by calling the provider's API — turning "this looks like a Stripe key" into "this is a live Stripe key". That verification is what makes it useful in CI, where you want few alerts and every one of them real.

## Step 1: Install the tools

On macOS or Linux with Homebrew, one command installs everything, including the two tools you will need later for history cleanup:

```bash
brew install gitleaks trufflehog pre-commit git-filter-repo

gitleaks version        # expect: 8.30.1
trufflehog --version    # expect: trufflehog 3.99.3
pre-commit --version    # expect: pre-commit 4.7.0
git filter-repo --version
```

The Python tools are also available through pipx (`pipx install pre-commit==4.7.0` and `pipx install git-filter-repo==2.47.0`). Pin the versions in CI later; on your laptop, the latest Homebrew formula is fine.

## Step 2: Scan the history you already have

Before adding any hook, find out what is already in the repository. Otherwise the first CI run will fail on a key committed years ago and someone will disable the job. Run both scanners over the full history:

```bash
cd your-repo

# Gitleaks: scan every commit reachable from all refs, redact secrets in output
gitleaks git --redact -v --log-opts="--all" --report-path gitleaks-report.json .

# TruffleHog: scan full history, show only credentials it could verify as live
trufflehog git file://. --results=verified,unknown
```

Always pass `--redact` to Gitleaks: without it, the secret itself lands in your terminal scrollback and in the report file. Keep the report out of git (`echo "gitleaks-report.json" >> .gitignore`) — it can contain partial secrets.

A Gitleaks finding looks like this, trimmed and redacted:

```
Finding:     aws_secret_access_key = REDACTED
Secret:      REDACTED
RuleID:      aws-access-token
File:        deploy/old-config.env
Line:        4
Commit:      9f2c1e7...
Fingerprint: 9f2c1e7...:deploy/old-config.env:aws-access-token:4
```

Note the exit codes, because CI will depend on them: Gitleaks exits `1` when it finds leaks; TruffleHog exits `183` when results were found and `--fail` was passed. TruffleHog's `--results=verified,unknown` is the right default for triage — verified findings are live credentials, exploitable right now, and they go first.

For every real finding, jump to the rotation runbook in Step 6 *before* touching history. Then decide whether historical findings should block future scans: Gitleaks supports a baseline, so you can record the old findings and only fail on new ones:

```bash
gitleaks git --baseline-path gitleaks-report.json --report-path findings.json .
```

## Step 3: Block the next leak at commit time

A hook that runs before the commit exists is the cheapest layer you will ever build. Create `.pre-commit-config.yaml` at the repository root:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.30.1
    hooks:
      - id: gitleaks          # runs: gitleaks git --pre-commit --redact --staged --verbose
  - repo: https://github.com/trufflesecurity/trufflehog
    rev: v3.99.3
    hooks:
      - id: trufflehog        # runs: trufflehog git file://. --since-commit HEAD --results=verified --fail
```

Then install it and run it once against every file:

```bash
pre-commit install            # writes .git/hooks/pre-commit
pre-commit run --all-files    # first run builds both Go hooks, so it is slow once
```

Test it with a fake token that matches a real format (random, not a credential):

```bash
echo 'token = "ghp_A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"' > leak-test.py
git add leak-test.py
git commit -m "test"
```

The commit should be refused with `Detect hardcoded secrets... Failed`, a `RuleID: github-pat`, and exit code 1. Clean up with `git rm --cached leak-test.py && rm leak-test.py`. The TruffleHog hook will stay silent on this fake token, because it only reports verified results and the token is not live. That is by design — Gitleaks is the one that blocks locally.

Be honest about what a hook is: a seatbelt, not a lock. Anyone can skip it with `git commit --no-verify`, and a fresh clone has no hooks until someone runs `pre-commit install`. That is why the next two layers exist.

## Step 4: Handle false positives without disabling the scanner

The fastest way to kill a security tool is to let it cry wolf until someone turns it off. You have three tools for false positives, from narrowest to broadest. An inline comment for a known test value on one line:

```python
STRIPE_TEST_KEY = "sk_test_placeholder_not_real"  # gitleaks:allow
```

A `.gitleaksignore` entry for one specific finding, copied by fingerprint from the report (`commit:file:rule:line` for history scans):

```
9f2c1e7d4b1a0c8e6f3d2b1a09f8e7d6c5b4a3f2:tests/fixtures/jwt.txt:jwt:12
```

And a `.gitleaks.toml` to extend the default rules with path allowlists — note the v8.25.0 syntax change to `[[allowlists]]`:

```toml
# .gitleaks.toml (picked up automatically from the repo root)
title = "repo gitleaks config"

[extend]
useDefault = true                 # keep all built-in rules

[[allowlists]]
description = "test fixtures and lockfiles"
paths = [
  '''tests/fixtures/.*''',
  '''(.*?)package-lock\.json$''',
]
```

Be stingy with path allowlists. A `tests/` exclusion is exactly where someone pastes a real staging key "just for this test". And scan your agent tooling configs too: GitGuardian found 24,008 unique secrets in MCP-related configuration files in 2025. Directories like `.cursor/`, `.claude/`, and MCP config files belong inside the scan, not outside it.

## Step 5: Push protection and CI — the layers nobody can skip

[[Push protection]] is GitHub's server-side check: it rejects a push containing a recognised secret before it lands. User-level push protection is on by default for pushes to public repositories; repository-level protection on private repositories requires GitHub Secret Protection, priced at $19 per active committer per month. Enable it with the GitHub CLI:

```bash
OWNER=your-org REPO=your-repo
gh api -X PATCH "repos/$OWNER/$REPO" \
  -f 'security_and_analysis[secret_scanning][status]=enabled' \
  -f 'security_and_analysis[secret_scanning_push_protection][status]=enabled'

# Confirm
gh api "repos/$OWNER/$REPO" --jq '.security_and_analysis'
```

A blocked push looks like `remote: error: GH013: Repository rule violations found` followed by "Push cannot contain secrets". Anyone with write access can bypass it with a reason, and every bypass lands in the audit log and emails repository admins — review those weekly, and enable delegated bypass if you want only security staff to approve them.

CI is the layer everyone passes through, because hooks can be skipped and push protection only knows provider token formats. A minimal workflow runs both scanners on every pull request, with every third-party action pinned to a full commit SHA:

```yaml
# .github/workflows/secret-scan.yml
name: secret-scan
on:
  pull_request:
  push:
    branches: [main]
permissions:
  contents: read
jobs:
  gitleaks:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v7.0.1
        with:
          fetch-depth: 0
      - name: Install gitleaks 8.30.1 (checksum verified)
        run: |
          V=8.30.1
          curl -sSLO "https://github.com/gitleaks/gitleaks/releases/download/v${V}/gitleaks_${V}_linux_x64.tar.gz"
          curl -sSLO "https://github.com/gitleaks/gitleaks/releases/download/v${V}/gitleaks_${V}_checksums.txt"
          grep "gitleaks_${V}_linux_x64.tar.gz" "gitleaks_${V}_checksums.txt" | sha256sum -c -
          tar -xzf "gitleaks_${V}_linux_x64.tar.gz" gitleaks
      - name: Scan commits in this PR or push
        run: |
          if [ "${{ github.event_name }}" = "pull_request" ]; then
            RANGE="${{ github.event.pull_request.base.sha }}..${{ github.event.pull_request.head.sha }}"
          else
            RANGE="${{ github.event.before }}..${{ github.sha }}"
          fi
          ./gitleaks git --redact -v --log-opts="$RANGE" .
  trufflehog:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v7.0.1
        with:
          fetch-depth: 0
      - uses: trufflesecurity/trufflehog@v3.99.3
        with:
          version: 3.99.3
          extra_args: --results=verified,unknown
```

Make both jobs required status checks in your branch protection or ruleset — otherwise a red check is only a suggestion. One detail worth knowing: the official gitleaks GitHub Action needs a free `GITLEAKS_LICENSE` for organisation-owned repositories, which is why the workflow above runs the binary directly.

## Step 6: A secret leaked. Rotate first.

GitHub's own guidance is blunt: revoke or rotate the credential before anything else, because once it cannot be used, you may not need to rewrite history at all. Assume a secret in a public repository was scraped within minutes — the five-minute Key Vault story above is the proof — and remember that the npm worms of the past year harvested credentials straight from developer machines and CI runners, not only from repositories.

For an AWS IAM user access key, the sequence is create, deploy, deactivate, investigate, delete:

```bash
USER=ci-deployer
OLD=AKIA...LEAKED   # the leaked access key ID
# 1. Create the replacement (an IAM user can have at most two keys)
aws iam create-access-key --user-name "$USER"
# 2. Deploy the new key to your secret manager and consumers, then:
aws iam update-access-key --user-name "$USER" --access-key-id "$OLD" --status Inactive
# 3. See what the leaked key did (CloudTrail event history covers 90 days)
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=AccessKeyId,AttributeValue="$OLD" \
  --max-results 50 --query 'Events[].[EventTime,EventName,Username]' --output table
# 4. Once nothing breaks, delete it
aws iam delete-access-key --user-name "$USER" --access-key-id "$OLD"
```

The same pattern applies everywhere: GitHub tokens are revoked from Developer settings, Stripe and OpenAI keys are rolled from their dashboards, database passwords are changed and connection strings redeployed. Better still, remove the long-lived key entirely — workload identity federation lets CI authenticate to AWS, GCP, and Azure without a stored secret to leak.

Only after rotation should you remove the secret from git history, with `git filter-repo`. Rewriting history changes every commit hash after the leak, breaks open pull requests, and invalidates signatures, so it is a deliberate, announced operation — never the first step, and never a substitute for rotation. A rotated secret in old history is a dead string. An unrotated secret with clean history is still a live credential.

## The thirty-minute version

If you do one thing today, do Step 2: scan the history of your most important repository. It takes minutes, and the result is either relief or the most valuable finding of your week. If you do two things, add the pre-commit hook — it costs one file and stops the next leak at the keyboard where it starts. The full stack — hook, push protection, CI, runbook — is the difference between Meta's October and a quieter one: the secret still leaks, but it is dead before anyone can use it, and the next one never reaches the repository at all.

Secrets do not leak because developers are careless. They leak because the convenient place to put a key and the safe place to put a key are never the same place, and every workflow quietly pushes toward the convenient one. Build the safe place first, make it the default, and let the scanners guard the gap. Your future self — the one who does not have to notify 1,500 people — will be grateful.

*Sources: GitGuardian State of Secrets Sprawl 2026; SecurityWeek, October 13, 2026 (Meta GitHub repository access); Ajay Kumar, "How to Stop Secrets Leaking Into Git" (tool versions verified October 20, 2026); GitHub documentation on secret scanning and push protection.*
