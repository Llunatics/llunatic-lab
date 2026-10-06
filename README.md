# llunatic-lab

Security notes from the dark side of the internet — written by **kou**.

A static site (no framework, no server-side build step). Articles are written in
Markdown under `content/articles/`, then `scripts/build.py` (stdlib Python only,
zero dependencies) renders everything into `public/`.

## Structure

```
content/articles/*.md    articles (frontmatter: title, date, tags, excerpt, cover)
content/glossary.json    technical terms + English explanations (for hover tooltips)
assets/css, assets/js    noir-editorial theme (dark default, light toggle)
assets/covers            one cover image per article
templates/base.html      page shell
scripts/build.py         static site generator
public/                  deploy-ready output (committed)
```

## Adding an article

1. Write `content/articles/YYYY-MM-DD-slug.md` with frontmatter.
2. Mark technical terms with `[[Term]]` — they automatically become hover
   tooltips if the term exists in `glossary.json`. If it doesn't, add it first.
3. Generate a dark 21:9 cover with lime accents, save to `assets/covers/`,
   reference as `/assets/covers/name.jpg`.
4. Run `python3 scripts/build.py`, check `public/`, commit + push.
   Vercel auto-deploys from the main branch.

## Writing standards

- English, 800–1500 words, mixed audience (beginners to practitioners).
- Never hallucinate CVE numbers / breach names — verify via research first.
- Wrap technical terms in `[[...]]` on first mention.
