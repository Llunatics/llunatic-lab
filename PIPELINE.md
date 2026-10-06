# Automated article pipeline — cron worker playbook

Schedule: Monday, Wednesday, Friday, Sunday at 07:00 WIB (4x/week).
Goal: research → write → build → push, with no user intervention.
Repo: `Llunatics/llunatic-lab`. Push via stored git credential helper.
Vercel auto-deploys on every push to the main branch.

## Steps

1. **Pick a topic.** Read titles + tags of existing articles (`content/articles/`),
   don't repeat a topic covered in the last 8 weeks. Rotate categories:
   threat-intel → hands-on tutorial → concept explainer → tools → case
   breakdown → repeat. Prefer what's hot: new critical CVEs, major breaches,
   or techniques the community is discussing.

2. **Research (mandatory, no hallucinating).** Use `browser.search` (`news`
   vertical for fresh stories) or `browser.deep_research` for heavy topics.
   Record: key facts, numbers, names, dates, and 2–4 source URLs. NEVER invent
   CVE numbers, victim company names, or incident dates.

3. **Write the article** — in TWO languages:
   - `content/articles/YYYY-MM-DD-slug.md`: ENGLISH version.
   - `content/articles/YYYY-MM-DD-slug.id.md`: INDONESIAN version (same
     frontmatter, translated title/excerpt/body; keep IT/technical terms in
     ENGLISH, e.g. "EASM", "attack surface", "subdomain" — explain them in
     Indonesian around the terms).
   - Frontmatter: title, date (today), tags (2–4, lowercase, hyphens),
     excerpt (1–2 sentences), cover (`/assets/covers/<slug>.jpg`, same file
     for both languages).
   - 800–1500 words each, mixed audience.
   - Structure: strong hook → explanation → technical detail → mitigation /
     practical steps → memorable closing.
   - Wrap technical terms in `[[Term]]` on first mention. If a term isn't in
     `content/glossary.json` yet, add it with a concise, accurate English
     explanation.
   - Code blocks always declare a language (```bash, ```python, etc.).

4. **Generate the cover** via `media.generate_image`:
   - `output_dir`: `/home/hatch/workspace/llunatic-lab/assets/covers`
   - `name`: article slug, `output_format`: `jpg`
   - Prompt: dark editorial illustration, lime-green accents, cinematic,
     minimalist, **absolutely no text, letters, or numbers**.

5. **Build**: `cd /home/hatch/workspace/llunatic-lab && python3 scripts/build.py`.
   Must complete with no errors and the new article must appear in `public/`.

6. **Push**: `git add -A && git commit -m "article: <slug>"` then push
   (`git push origin main` — auth is stored, just push). Don't push if the
   build failed.

7. **Notify the user** on WhatsApp (this chat): "🤖 New article published:
   <title> — <1 sentence on what it's about>. Read it: <link> (llunatic-lab)".
   Link INLINE followed by text, NEVER at the end of the message. First check
   that https://llunatic-lab.vercel.app/artikel/<slug>/ loads; if it's not live
   yet (user hasn't connected Vercel), link the markdown file on GitHub instead.

## Hard rules

- No facts without verified sources from step 2.
- No plagiarism: rewrite everything in llunatic-lab's voice, never copy-paste sources.
- If research stalls (not enough sources), switch topics — don't force it.
- One article per run. If something fails midway, don't commit a half-done state.
