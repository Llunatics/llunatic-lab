#!/usr/bin/env python3
"""llunatic-lab static site generator — stdlib only, no dependencies."""
import re, json, html, shutil
from pathlib import Path
from datetime import datetime
from email.utils import format_datetime

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content" / "articles"
GLOSSARY = ROOT / "content" / "glossary.json"
TEMPLATES = ROOT / "templates"
ASSETS = ROOT / "assets"
PUBLIC = ROOT / "public"
SITE_URL = "https://llunatic-lab.vercel.app"

BULAN = ["", "January", "February", "March", "April", "May", "June",
         "July", "August", "September", "October", "November", "December"]

# ---------------- frontmatter ----------------
def parse_md(path):
    text = path.read_text(encoding="utf-8")
    fm, body = {}, text
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip().strip('"').strip("'")
        body = m.group(2)
    tags = [t.strip() for t in fm.get("tags", "").strip("[]").split(",") if t.strip()]
    slug = fm.get("slug") or re.sub(r"^\d{4}-\d{2}-\d{2}-", "", path.stem)
    date = fm.get("date", "2026-01-01")
    return {"slug": slug, "date": date, "title": fm.get("title", slug),
            "tags": tags, "excerpt": fm.get("excerpt", ""),
            "cover": fm.get("cover", ""), "body": body}

def tgl_id(d):
    dt = datetime.strptime(d, "%Y-%m-%d")
    return f"{dt.day} {BULAN[dt.month]} {dt.year}"

# ---------------- inline markdown ----------------
def inline_md(s, glossary):
    s = html.escape(s)
    # [[Istilah]] -> glossary tooltip (process before links)
    def gterm(m):
        term = m.group(1)
        key = next((k for k in glossary if k.lower() == term.lower()), None)
        if not key:
            return term
        return (f'<span class="gterm" data-term="{html.escape(key)}" '
                f'data-def="{html.escape(glossary[key])}">{html.escape(term)}</span>')
    s = re.sub(r"\[\[([^\]]+)\]\]", gterm, s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", s)
    s = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r'<img src="\2" alt="\1" loading="lazy">', s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    return s

def slugify(t):
    t = re.sub(r"<[^>]+>", "", t).lower()
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t or "bagian"

# ---------------- block markdown ----------------
def md_to_html(body, glossary):
    # extract fenced code blocks first
    codes = []
    def stash(m):
        lang = m.group(1) or "code"
        codes.append((lang, m.group(2)))
        return f"\x00CODE{len(codes)-1}\x00"
    body = re.sub(r"```(\w*)\n(.*?)```", stash, body, flags=re.S)

    out, toc = [], []
    lines = body.split("\n")
    i, h2n = 0, 0
    in_ul, in_ol = False, False

    def close_lists():
        nonlocal in_ul, in_ol
        if in_ul: out.append("</ul>"); in_ul = False
        if in_ol: out.append("</ol>"); in_ol = False

    while i < len(lines):
        line = lines[i]
        s = line.strip()

        mcode = re.match(r"\x00CODE(\d+)\x00", s)
        if mcode:
            close_lists()
            lang, code = codes[int(mcode.group(1))]
            out.append(f'<pre><code class="language-{html.escape(lang)}">'
                       f'{html.escape(code.rstrip())}</code></pre>')
            i += 1; continue
        if not s:
            close_lists(); i += 1; continue
        if re.match(r"^---+$", s):
            close_lists(); out.append("<hr>"); i += 1; continue
        mh = re.match(r"^(#{1,4})\s+(.*)", s)
        if mh:
            close_lists()
            lvl, txt = len(mh.group(1)), mh.group(2)
            hid = slugify(txt)
            inner = inline_md(txt, glossary)
            if lvl == 2:
                h2n += 1
                toc.append((2, hid, re.sub(r"<[^>]+>", "", txt)))
                out.append(f'<h2 id="{hid}"><span class="hnum">{h2n:02d}</span>{inner}</h2>')
            elif lvl == 3:
                toc.append((3, hid, re.sub(r"<[^>]+>", "", txt)))
                out.append(f'<h3 id="{hid}">{inner}</h3>')
            else:
                out.append(f"<h{lvl}>{inner}</h{lvl}>")
            i += 1; continue
        if s.startswith(">"):
            close_lists()
            qs = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                qs.append(lines[i].strip()[1:].strip()); i += 1
            out.append("<blockquote>" + "<br>".join(inline_md(q, glossary) for q in qs) + "</blockquote>")
            continue
        mu = re.match(r"^[-*]\s+(.*)", s)
        if mu:
            if in_ol: out.append("</ol>"); in_ol = False
            if not in_ul: out.append("<ul>"); in_ul = True
            out.append(f"<li>{inline_md(mu.group(1), glossary)}</li>")
            i += 1; continue
        mo = re.match(r"^\d+[.)]\s+(.*)", s)
        if mo:
            if in_ul: out.append("</ul>"); in_ul = False
            if not in_ol: out.append("<ol>"); in_ol = True
            out.append(f"<li>{inline_md(mo.group(1), glossary)}</li>")
            i += 1; continue
        # paragraph (join wrapped lines)
        close_lists()
        buf = [s]; i += 1
        while i < len(lines) and lines[i].strip() and not re.match(
                r"^(#{1,4}\s|```|[-*]\s|\d+[.)]\s|>|---+$|\x00CODE)", lines[i].strip()):
            buf.append(lines[i].strip()); i += 1
        out.append(f"<p>{inline_md(' '.join(buf), glossary)}</p>")

    close_lists()
    return "\n".join(out), toc

# ---------------- templates ----------------
def tpl(name):
    return (TEMPLATES / name).read_text(encoding="utf-8")

def page(title, desc, content, extra=""):
    t = tpl("base.html")
    return (t.replace("{{title}}", html.escape(title))
             .replace("{{description}}", html.escape(desc))
             .replace("{{content}}", content)
             .replace("{{extra_head}}", extra))

def index_row(a, n):
    thumb = (f'<img class="thumb" src="{a["cover"]}" alt="" loading="lazy">'
             if a["cover"] else "")
    tags = " ".join(f'<a class="tag" href="/tag/{t}/">{t}</a>' for t in a["tags"])
    words = len(re.findall(r"\w+", a["body"]))
    mins = max(1, round(words / 200))
    return f"""<li class="index-row rv">
      <span class="num">/{n:02d}</span>
      <div>
        <h3><a href="/artikel/{a['slug']}/">{html.escape(a['title'])}</a></h3>
        <p class="excerpt">{html.escape(a['excerpt'])}</p>
        <div class="meta"><span>{tgl_id(a['date'])}</span><span>·</span>
        <span>{mins} min read</span>{tags}</div>
      </div>
      {thumb}
      <span class="arrow">→</span>
    </li>"""

def toc_html(toc):
    if not toc: return ""
    items = "".join(
        f'<li style="margin-left:{(lvl-2)*14}px"><a href="#{hid}">{html.escape(txt)}</a></li>'
        for lvl, hid, txt in toc)
    return f'<aside class="toc"><h4>Contents</h4><ol>{items}</ol></aside>'

# ---------------- build ----------------
def main():
    glossary = json.loads(GLOSSARY.read_text(encoding="utf-8"))
    articles = sorted((parse_md(p) for p in CONTENT.glob("*.md")),
                      key=lambda a: a["date"], reverse=True)
    for a in articles:
        a["html"], a["toc"] = md_to_html(a["body"], glossary)
        words = len(re.findall(r"\w+", a["body"]))
        a["mins"] = max(1, round(words / 200))

    if PUBLIC.exists(): shutil.rmtree(PUBLIC)
    (PUBLIC / "assets").mkdir(parents=True)
    for sub in ("css", "js", "covers"):
        src = ASSETS / sub
        if src.exists():
            shutil.copytree(src, PUBLIC / "assets" / sub)

    all_tags = sorted({t for a in articles for t in a["tags"]})

    # ---- home ----
    latest = articles[:6]
    rows = "\n".join(index_row(a, i + 1) for i, a in enumerate(latest))
    ticker_items = "".join(
        f"<span>{html.escape(a['title'])}</span>" for a in articles[:8])
    chips = "".join(f'<a class="chip" href="/tag/{t}/">{t}</a>' for t in all_tags)
    home = f"""
    <section class="hero"><div class="wrap">
      <div class="kicker"><span class="dot"></span>security notes — from the dark side of the internet</div>
      <h1>Security <em>notes</em> for those who refuse to be the <em>next victim.</em></h1>
      <p class="lede">Written by <strong>kou</strong> — threat intel, tutorials, and cybersecurity case breakdowns.
      Technical terms come with explanations: just <strong>hover</strong> over dotted-underlined words.</p>
      <div class="hero-meta"><span><b>{len(articles):02d}</b> articles</span>
      <span><b>{len(all_tags):02d}</b> topics</span><span>published 3–4× a week</span></div>
    </div>
    <div class="ticker"><div class="ticker-track">{ticker_items}</div></div>
    </section>
    <section><div class="wrap">
      <div class="sec-head"><h2><span class="idx">01</span>Latest writings</h2>
      <a class="more" href="/arsip/">full archive →</a></div>
      <ol class="index-list">{rows}</ol>
      <div class="sec-head"><h2><span class="idx">02</span>Browse topics</h2></div>
      <div class="chips">{chips}</div>
    </div></section>"""
    (PUBLIC / "index.html").write_text(
        page("Cybersecurity notes",
             "Threat intel, tutorials, and cybersecurity case breakdowns by kou — llunatic-lab.",
             home), encoding="utf-8")

    # ---- article pages ----
    for idx, a in enumerate(articles):
        prev_a = articles[idx + 1] if idx + 1 < len(articles) else None
        next_a = articles[idx - 1] if idx - 1 >= 0 else None
        tags = " ".join(f'<a class="tag" href="/tag/{t}/">{t}</a>' for t in a["tags"])
        cover = (f'<img class="cover" src="{a["cover"]}" alt="{html.escape(a["title"])}">'
                 if a["cover"] else "")
        pager = '<div class="pager">'
        pager += (f'<a href="/artikel/{prev_a["slug"]}/"><span class="dir">← previous</span>'
                  f'<span class="t">{html.escape(prev_a["title"])}</span></a>'
                  if prev_a else "<span></span>")
        pager += (f'<a class="next" href="/artikel/{next_a["slug"]}/"><span class="dir">next →</span>'
                  f'<span class="t">{html.escape(next_a["title"])}</span></a>'
                  if next_a else "<span></span>")
        pager += "</div>"
        art = f"""
        <article class="article-hero"><div class="wrap-narrow">
          <div class="kicker"><span class="dot"></span>article</div>
          <h1>{html.escape(a['title'])}</h1>
          <div class="meta"><span>{tgl_id(a['date'])}</span><span>·</span>
          <span>{a['mins']} mnt baca</span><span>·</span><span>by kou</span>{tags}</div>
          {cover}
        </div></article>
        <div class="article-body"><div class="wrap">
          <div class="article-grid">
            <div class="prose">{a['html']}{pager}</div>
            {toc_html(a['toc'])}
          </div>
        </div></div>"""
        d = PUBLIC / "artikel" / a["slug"]
        d.mkdir(parents=True)
        (d / "index.html").write_text(
            page(a["title"], a["excerpt"], art,
                 f'<meta property="og:image" content="{a["cover"]}">' if a["cover"] else ""),
            encoding="utf-8")

    # ---- archive ----
    by_year = {}
    for a in articles:
        by_year.setdefault(a["date"][:4], []).append(a)
    arch = '<div class="page-head"><div class="wrap"><div class="kicker"><span class="dot"></span>archive</div>'
    arch += "<h1>All <em>writings.</em></h1></div></div><div class='wrap'>"
    for year in sorted(by_year, reverse=True):
        arch += f'<div class="arch-year">— {year}</div><ol class="index-list">'
        arch += "\n".join(index_row(a, i + 1)
                           for i, a in enumerate(sorted(by_year[year],
                                                        key=lambda x: x["date"], reverse=True)))
        arch += "</ol>"
    arch += "</div>"
    d = PUBLIC / "arsip"; d.mkdir(parents=True)
    (d / "index.html").write_text(page("Archive", "Every article on llunatic-lab.", arch),
                                  encoding="utf-8")

    # ---- tag pages ----
    for t in all_tags:
        tagged = [a for a in articles if t in a["tags"]]
        rows = "\n".join(index_row(a, i + 1) for i, a in enumerate(tagged))
        c = (f'<div class="page-head"><div class="wrap"><div class="kicker">'
             f'<span class="dot"></span>topic</div><h1>#{t}</h1></div></div>'
             f'<div class="wrap"><ol class="index-list">{rows}</ol></div>')
        d = PUBLIC / "tag" / t; d.mkdir(parents=True)
        (d / "index.html").write_text(page(f"#{t}", f"Articles about {t}.", c),
                                     encoding="utf-8")

    # ---- about ----
    about = """
    <div class="page-head"><div class="wrap">
      <div class="kicker"><span class="dot"></span>about</div>
      <h1>A small lab for <em>cybersecurity.</em></h1>
    </div></div>
    <div class="wrap"><div class="about-grid"><div>
      <p class="big">llunatic-lab is the public notebook of <b>kou</b> — a place to
      document what&apos;s learned about cybersecurity: threat intelligence, attack
      surface, ethical hacking, and defense.</p>
      <p style="margin-top:20px;color:var(--ink-dim)">Written in a style beginners can
      follow but practitioners still find useful. Every technical term has a hover
      explanation — nothing is left hanging.</p>
    </div><div>
      <p style="color:var(--ink-dim)">Every article on this site is written and published
      through an automated pipeline: research → write → review → publish, 3–4 times
      a week. If anything is technically wrong, that&apos;s on the author — and
      corrections are always welcome.</p>
    </div></div>
    <div class="stat-row">
      <div class="stat"><b>{{n_artikel}}</b><span>articles published</span></div>
      <div class="stat"><b>{{n_topik}}</b><span>topics covered</span></div>
      <div class="stat"><b>3–4×</b><span>published per week</span></div>
    </div></div>""".replace("{{n_artikel}}", f"{len(articles):02d}").replace(
        "{{n_topik}}", f"{len(all_tags):02d}")
    d = PUBLIC / "tentang"; d.mkdir(parents=True)
    (d / "index.html").write_text(page("About", "About llunatic-lab and kou.", about),
                                  encoding="utf-8")

    # ---- search.json ----
    (PUBLIC / "search.json").write_text(json.dumps(
        [{"title": a["title"], "excerpt": a["excerpt"], "tags": a["tags"],
          "date": tgl_id(a["date"]), "url": f"/artikel/{a['slug']}/"}
         for a in articles], ensure_ascii=False), encoding="utf-8")

    # ---- sitemap ----
    urls = [("", "2026-10-06"), ("arsip/", "2026-10-06"), ("tentang/", "2026-10-06")]
    urls += [(f"artikel/{a['slug']}/", a["date"]) for a in articles]
    urls += [(f"tag/{t}/", "2026-10-06") for t in all_tags]
    sm = ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset '
          'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(
          f"  <url><loc>{SITE_URL}/{u}</loc><lastmod>{d}</lastmod></url>\n"
          for u, d in urls) + "</urlset>")
    (PUBLIC / "sitemap.xml").write_text(sm, encoding="utf-8")

    # ---- rss ----
    items = "".join(
        f"""<item><title>{html.escape(a['title'])}</title>
        <link>{SITE_URL}/artikel/{a['slug']}/</link>
        <description>{html.escape(a['excerpt'])}</description>
        <pubDate>{format_datetime(datetime.strptime(a['date'], '%Y-%m-%d'))}</pubDate>
        <guid>{SITE_URL}/artikel/{a['slug']}/</guid></item>"""
        for a in articles[:20])
    rss = (f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0">\n<channel>\n'
           f"<title>llunatic-lab</title><link>{SITE_URL}</link>\n"
           f"<description>Security notes by kou</description>\n{items}\n</channel>\n</rss>")
    (PUBLIC / "rss.xml").write_text(rss, encoding="utf-8")

    print(f"built {len(articles)} artikel, {len(all_tags)} topik -> {PUBLIC}")

if __name__ == "__main__":
    main()
