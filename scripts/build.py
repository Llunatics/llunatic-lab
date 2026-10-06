#!/usr/bin/env python3
"""llunatic-lab static site generator — stdlib only, bilingual EN/ID."""
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

MONTHS = {
    "en": ["", "January", "February", "March", "April", "May", "June",
           "July", "August", "September", "October", "November", "December"],
    "id": ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
           "Juli", "Agustus", "September", "Oktober", "November", "Desember"],
}

S = {
"en": {
    "lang": "en", "other_lang": "id", "other_label": "ID",
    "nav_archive": "Archive", "nav_about": "About",
    "search_ph": "search articles…",
    "search_hint": "type at least 2 characters · esc to close · ctrl+k anywhere",
    "search_empty": "nothing found — try another keyword.",
    "foot_tag": "security notes from the dark side of the internet",
    "kicker_hero": "security notes — from the dark side of the internet",
    "hero_h1": "Security <em>notes</em> for those who refuse to be the <em>next victim.</em>",
    "lede": ("Threat intel, tutorials, and cybersecurity case breakdowns. "
             "Technical terms come with explanations: just <strong>hover</strong> "
             "over dotted-underlined words."),
    "stats_articles": "articles", "stats_topics": "topics",
    "stats_freq": "published 3–4× a week",
    "latest": "Latest writings", "all_archive": "full archive →",
    "topics_head": "Browse topics",
    "min_read": "min read", "article": "article",
    "prev": "← previous", "next": "next →",
    "contents": "Contents",
    "archive_kicker": "archive", "archive_h1": "All <em>writings.</em>",
    "archive_title": "Archive", "archive_desc": "Every article on llunatic-lab.",
    "topic_kicker": "topic",
    "about_kicker": "about", "about_h1": "A small lab for <em>cybersecurity.</em>",
    "about_title": "About", "about_desc": "About llunatic-lab.",
    "home_title": "Cybersecurity notes",
    "home_desc": "Threat intel, tutorials, and cybersecurity case breakdowns — llunatic-lab.",
    "rss_desc": "Security notes from the dark side of the internet",
    "author_kicker": "written by",
    "author_bio": ("<strong>kou</strong> documents what’s learned about threat intel, "
                  "attack surface, and practical defense — from the dark side of the internet."),
    "about_p1": ("llunatic-lab is a public notebook for cybersecurity: threat intelligence, "
                 "attack surface, ethical hacking, and defense."),
    "about_p2": ("Written in a style beginners can follow but practitioners still find useful. "
                 "Every technical term has a hover explanation — nothing is left hanging."),
    "about_p3": ("Every article here is written and published through an automated pipeline: "
                 "research → write → review → publish, 3–4 times a week, in English and Indonesian. "
                 "If anything is technically wrong, that’s on the author — corrections are always welcome."),
    "about_s1": "articles published", "about_s2": "topics covered",
    "about_s3": "published per week",
},
"id": {
    "lang": "id", "other_lang": "en", "other_label": "EN",
    "nav_archive": "Arsip", "nav_about": "Tentang",
    "search_ph": "cari artikel…",
    "search_hint": "ketik minimal 2 huruf · esc untuk tutup · ctrl+k dari mana saja",
    "search_empty": "nggak ketemu — coba kata kunci lain.",
    "foot_tag": "catatan keamanan dari sisi gelap internet",
    "kicker_hero": "catatan keamanan — dari sisi gelap internet",
    "hero_h1": "Catatan <em>keamanan</em> untuk yang tidak mau jadi korban <em>berikutnya.</em>",
    "lede": ("Threat intel, tutorial, dan bedah kasus keamanan siber. "
             "Istilah teknis ada penjelasannya: cukup <strong>arahkan kursor</strong> "
             "ke kata bergaris titik-titik. Istilah teknis dibiarkan dalam bahasa Inggris."),
    "stats_articles": "artikel", "stats_topics": "topik",
    "stats_freq": "terbit 3–4× seminggu",
    "latest": "Tulisan terbaru", "all_archive": "semua arsip →",
    "topics_head": "Jelajahi topik",
    "min_read": "mnt baca", "article": "artikel",
    "prev": "← sebelumnya", "next": "berikutnya →",
    "contents": "Daftar isi",
    "archive_kicker": "arsip", "archive_h1": "Semua <em>tulisan.</em>",
    "archive_title": "Arsip", "archive_desc": "Semua artikel di llunatic-lab.",
    "topic_kicker": "topik",
    "about_kicker": "tentang", "about_h1": "Lab kecil untuk <em>keamanan siber.</em>",
    "about_title": "Tentang", "about_desc": "Tentang llunatic-lab.",
    "home_title": "Catatan keamanan siber",
    "home_desc": "Threat intel, tutorial, dan bedah kasus keamanan siber — llunatic-lab.",
    "rss_desc": "Catatan keamanan dari sisi gelap internet",
    "author_kicker": "ditulis oleh",
    "author_bio": ("<strong>kou</strong> mendokumentasikan threat intel, "
                  "attack surface, dan pertahanan praktis — dari sisi gelap internet."),
    "about_p1": ("llunatic-lab adalah catatan publik untuk keamanan siber: threat intelligence, "
                 "attack surface, ethical hacking, dan defense."),
    "about_p2": ("Ditulis dengan gaya yang bisa diikuti pemula tapi tetap berguna buat praktisi. "
                 "Setiap istilah teknis punya penjelasan sekali hover — tidak ada yang dibiarkan menggantung. "
                 "Istilah teknis dibiarkan dalam bahasa Inggris."),
    "about_p3": ("Semua artikel di sini ditulis dan diterbitkan lewat pipeline otomatis: "
                 "riset → tulis → review → terbit, 3–4 kali seminggu, dalam bahasa Inggris dan Indonesia. "
                 "Kalau ada yang keliru secara teknis, itu tanggung jawab penulis — koreksi selalu diterima."),
    "about_s1": "artikel terbit", "about_s2": "topik dibahas",
    "about_s3": "terbit per minggu",
},
}

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
    stem = path.stem
    lang = "id" if stem.endswith(".id") else "en"
    if lang == "id":
        stem = stem[:-3]
    tags = [t.strip() for t in fm.get("tags", "").strip("[]").split(",") if t.strip()]
    slug = fm.get("slug") or re.sub(r"^\d{4}-\d{2}-\d{2}-", "", stem)
    return {"slug": slug, "lang": lang, "date": fm.get("date", "2026-01-01"),
            "title": fm.get("title", slug), "tags": tags,
            "excerpt": fm.get("excerpt", ""), "cover": fm.get("cover", ""),
            "body": body}

def tgl(lang, d):
    dt = datetime.strptime(d, "%Y-%m-%d")
    return f"{dt.day} {MONTHS[lang][dt.month]} {dt.year}"

# ---------------- urls ----------------
def pfx(lang):
    return "id/" if lang == "id" else ""

def art_url(slug, lang):
    return f"/{pfx(lang)}artikel/{slug}/"

def tag_url(t, lang):
    return f"/{pfx(lang)}tag/{t}/"

# ---------------- inline markdown ----------------
def inline_md(s, glossary, lang):
    s = html.escape(s)
    def gterm(m):
        term = m.group(1)
        key = next((k for k in glossary if k.lower() == term.lower()), None)
        if not key:
            return term
        d = glossary[key]
        definition = d.get(lang, d.get("en", "")) if isinstance(d, dict) else d
        return (f'<span class="gterm" data-term="{html.escape(key)}" '
                f'data-def="{html.escape(definition)}">{html.escape(term)}</span>')
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
def md_to_html(body, glossary, lang):
    codes = []
    def stash(m):
        codes.append((m.group(1) or "code", m.group(2)))
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
            lg, code = codes[int(mcode.group(1))]
            out.append(f'<pre><code class="language-{html.escape(lg)}">'
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
            inner = inline_md(txt, glossary, lang)
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
            out.append("<blockquote>" + "<br>".join(inline_md(q, glossary, lang) for q in qs) + "</blockquote>")
            continue
        mu = re.match(r"^[-*]\s+(.*)", s)
        if mu:
            if in_ol: out.append("</ol>"); in_ol = False
            if not in_ul: out.append("<ul>"); in_ul = True
            out.append(f"<li>{inline_md(mu.group(1), glossary, lang)}</li>")
            i += 1; continue
        mo = re.match(r"^\d+[.)]\s+(.*)", s)
        if mo:
            if in_ul: out.append("</ul>"); in_ul = False
            if not in_ol: out.append("<ol>"); in_ol = True
            out.append(f"<li>{inline_md(mo.group(1), glossary, lang)}</li>")
            i += 1; continue
        close_lists()
        buf = [s]; i += 1
        while i < len(lines) and lines[i].strip() and not re.match(
                r"^(#{1,4}\s|```|[-*]\s|\d+[.)]\s|>|---+$|\x00CODE)", lines[i].strip()):
            buf.append(lines[i].strip()); i += 1
        out.append(f"<p>{inline_md(' '.join(buf), glossary, lang)}</p>")

    close_lists()
    return "\n".join(out), toc

# ---------------- templates ----------------
def page(title, desc, content, lang, lang_url=None, extra=""):
    t = (TEMPLATES / "base.html").read_text(encoding="utf-8")
    st = dict(S[lang])
    st["nav_archive_url"] = f"/{pfx(lang)}arsip/"
    st["nav_about_url"] = f"/{pfx(lang)}tentang/"
    st["home_url"] = f"/{pfx(lang)}"
    hreflang = ""
    if lang_url:
        other = st["other_lang"]
        hreflang = (f'<link rel="alternate" hreflang="{lang}" href="{SITE_URL}{page._cur}">'
                    f'<link rel="alternate" hreflang="{other}" href="{SITE_URL}{lang_url}">')
    t = (t.replace("{{title}}", html.escape(title))
          .replace("{{description}}", html.escape(desc))
          .replace("{{content}}", content)
          .replace("{{extra_head}}", extra + hreflang))
    for k, v in st.items():
        t = t.replace("{{s:" + k + "}}", v)
    if lang_url:
        t = t.replace("{{s:lang_url}}", lang_url)
    else:
        t = re.sub(r'<a class="lang-toggle"[^>]*>.*?</a>', "", t)
        t = t.replace("{{s:lang_url}}", "#")
    return t

def index_row(a, n, lang):
    thumb = (f'<img class="thumb" src="{a["cover"]}" alt="" loading="lazy">'
             if a["cover"] else "")
    tags = " ".join(f'<a class="tag" href="{tag_url(t, lang)}">{t}</a>' for t in a["tags"])
    return f"""<li class="index-row rv">
      <span class="num">/{n:02d}</span>
      <div>
        <h3><a href="{art_url(a['slug'], lang)}">{html.escape(a['title'])}</a></h3>
        <p class="excerpt">{html.escape(a['excerpt'])}</p>
        <div class="meta"><span>{tgl(lang, a['date'])}</span><span>·</span>
        <span>{a['mins']} {S[lang]['min_read']}</span>{tags}</div>
      </div>
      {thumb}
      <span class="arrow">→</span>
    </li>"""

def toc_html(toc, lang):
    if not toc: return ""
    items = "".join(
        f'<li style="margin-left:{(lvl-2)*14}px"><a href="#{hid}">{html.escape(txt)}</a></li>'
        for lvl, hid, txt in toc)
    return (f'<aside class="toc"><h4>{S[lang]["contents"]}</h4><ol>{items}</ol></aside>')

def author_box(lang):
    st = S[lang]
    return (f'<div class="author-box"><div class="kicker"><span class="dot"></span>'
            f'{st["author_kicker"]}</div><p>{st["author_bio"]}</p></div>')

# ---------------- build ----------------
def main():
    glossary = json.loads(GLOSSARY.read_text(encoding="utf-8"))
    parsed = [parse_md(p) for p in CONTENT.glob("*.md")]
    # pair by slug
    pairs = {}
    for a in parsed:
        pairs.setdefault(a["slug"], {})[a["lang"]] = a
    slugs = sorted(pairs, key=lambda s: pairs[s].get("en", pairs[s].get("id"))["date"],
                   reverse=True)

    for slug, versions in pairs.items():
        for lang, a in versions.items():
            a["html"], a["toc"] = md_to_html(a["body"], glossary, lang)
            words = len(re.findall(r"\w+", a["body"]))
            a["mins"] = max(1, round(words / 200))

    if PUBLIC.exists(): shutil.rmtree(PUBLIC)
    (PUBLIC / "assets").mkdir(parents=True)
    for sub in ("css", "js", "covers"):
        src = ASSETS / sub
        if src.exists():
            shutil.copytree(src, PUBLIC / "assets" / sub)

    for lang in ("en", "id"):
        st = S[lang]
        arts = [pairs[s][lang] for s in slugs if lang in pairs[s]]
        if not arts:
            continue
        all_tags = sorted({t for a in arts for t in a["tags"]})
        pre = PUBLIC / pfx(lang)
        pre.mkdir(parents=True, exist_ok=True)

        # ---- home ----
        rows = "\n".join(index_row(a, i + 1, lang) for i, a in enumerate(arts[:6]))
        ticker_items = "".join(f"<span>{html.escape(a['title'])}</span>" for a in arts[:8])
        chips = "".join(f'<a class="chip" href="{tag_url(t, lang)}">{t}</a>' for t in all_tags)
        home = f"""
        <section class="hero"><div class="wrap">
          <div class="kicker"><span class="dot"></span>{st['kicker_hero']}</div>
          <h1>{st['hero_h1']}</h1>
          <p class="lede">{st['lede']}</p>
          <div class="hero-meta"><span><b>{len(arts):02d}</b> {st['stats_articles']}</span>
          <span><b>{len(all_tags):02d}</b> {st['stats_topics']}</span><span>{st['stats_freq']}</span></div>
        </div>
        <div class="ticker"><div class="ticker-track">{ticker_items}</div></div>
        </section>
        <section><div class="wrap">
          <div class="sec-head"><h2><span class="idx">01</span>{st['latest']}</h2>
          <a class="more" href="/{pfx(lang)}arsip/">{st['all_archive']}</a></div>
          <ol class="index-list">{rows}</ol>
          <div class="sec-head"><h2><span class="idx">02</span>{st['topics_head']}</h2></div>
          <div class="chips">{chips}</div>
        </div></section>"""
        page._cur = f"/{pfx(lang)}"
        (pre / "index.html").write_text(
            page(st["home_title"], st["home_desc"], home, lang,
                 lang_url=f"/{'id/' if lang == 'en' else ''}"), encoding="utf-8")

        # ---- article pages ----
        for idx, slug in enumerate([s for s in slugs if lang in pairs[s]]):
            a = pairs[slug][lang]
            others = [s for s in slugs if lang in pairs[s]]
            prev_a = pairs[others[idx + 1]][lang] if idx + 1 < len(others) else None
            next_a = pairs[others[idx - 1]][lang] if idx - 1 >= 0 else None
            tags = " ".join(f'<a class="tag" href="{tag_url(t, lang)}">{t}</a>' for t in a["tags"])
            cover = (f'<img class="cover" src="{a["cover"]}" alt="{html.escape(a["title"])}">'
                     if a["cover"] else "")
            other_lang = st["other_lang"]
            has_other = other_lang in pairs[slug]
            lang_url = art_url(slug, other_lang) if has_other else None
            pager = '<div class="pager">'
            pager += (f'<a href="{art_url(prev_a["slug"], lang)}"><span class="dir">{st["prev"]}</span>'
                      f'<span class="t">{html.escape(prev_a["title"])}</span></a>'
                      if prev_a else "<span></span>")
            pager += (f'<a class="next" href="{art_url(next_a["slug"], lang)}"><span class="dir">{st["next"]}</span>'
                      f'<span class="t">{html.escape(next_a["title"])}</span></a>'
                      if next_a else "<span></span>")
            pager += "</div>"
            art = f"""
            <article class="article-hero"><div class="wrap-narrow">
              <div class="kicker"><span class="dot"></span>{st['article']}</div>
              <h1>{html.escape(a['title'])}</h1>
              <div class="meta"><span>{tgl(lang, a['date'])}</span><span>·</span>
              <span>{a['mins']} {st['min_read']}</span>{tags}</div>
              {cover}
            </div></article>
            <div class="article-body"><div class="wrap">
              <div class="article-grid">
                <div class="prose">{a['html']}{author_box(lang)}{pager}</div>
                {toc_html(a['toc'], lang)}
              </div>
            </div></div>"""
            d = pre / "artikel" / slug
            d.mkdir(parents=True)
            page._cur = art_url(slug, lang)
            (d / "index.html").write_text(
                page(a["title"], a["excerpt"], art, lang, lang_url=lang_url,
                     extra=(f'<meta property="og:image" content="{a["cover"]}">' if a["cover"] else "")),
                encoding="utf-8")

        # ---- archive ----
        by_year = {}
        for a in arts:
            by_year.setdefault(a["date"][:4], []).append(a)
        arch = (f'<div class="page-head"><div class="wrap"><div class="kicker">'
                f'<span class="dot"></span>{st["archive_kicker"]}</div>'
                f'<h1>{st["archive_h1"]}</h1></div></div><div class="wrap">')
        for year in sorted(by_year, reverse=True):
            arch += f'<div class="arch-year">— {year}</div><ol class="index-list">'
            arch += "\n".join(index_row(a, i + 1, lang)
                              for i, a in enumerate(sorted(by_year[year],
                                                           key=lambda x: x["date"], reverse=True)))
            arch += "</ol>"
        arch += "</div>"
        d = pre / "arsip"; d.mkdir(parents=True)
        page._cur = f"/{pfx(lang)}arsip/"
        (d / "index.html").write_text(
            page(st["archive_title"], st["archive_desc"], arch, lang,
                 lang_url=f"/{'id/' if lang == 'en' else ''}arsip/"), encoding="utf-8")

        # ---- tag pages ----
        for t in all_tags:
            tagged = [a for a in arts if t in a["tags"]]
            rows = "\n".join(index_row(a, i + 1, lang) for i, a in enumerate(tagged))
            c = (f'<div class="page-head"><div class="wrap"><div class="kicker">'
                 f'<span class="dot"></span>{st["topic_kicker"]}</div><h1>#{t}</h1></div></div>'
                 f'<div class="wrap"><ol class="index-list">{rows}</ol></div>')
            d = pre / "tag" / t; d.mkdir(parents=True)
            page._cur = tag_url(t, lang)
            (d / "index.html").write_text(
                page(f"#{t}", f"{st['topic_kicker']}: {t}", c, lang,
                     lang_url=tag_url(t, st["other_lang"])), encoding="utf-8")

        # ---- about ----
        about = f"""
        <div class="page-head"><div class="wrap">
          <div class="kicker"><span class="dot"></span>{st['about_kicker']}</div>
          <h1>{st['about_h1']}</h1>
        </div></div>
        <div class="wrap"><div class="about-grid"><div>
          <p class="big">{st['about_p1']}</p>
          <p style="margin-top:20px;color:var(--ink-dim)">{st['about_p2']}</p>
        </div><div>
          <p style="color:var(--ink-dim)">{st['about_p3']}</p>
        </div></div>
        <div class="stat-row">
          <div class="stat"><b>{len(arts):02d}</b><span>{st['about_s1']}</span></div>
          <div class="stat"><b>{len(all_tags):02d}</b><span>{st['about_s2']}</span></div>
          <div class="stat"><b>3–4×</b><span>{st['about_s3']}</span></div>
        </div></div>"""
        d = pre / "tentang"; d.mkdir(parents=True)
        page._cur = f"/{pfx(lang)}tentang/"
        (d / "index.html").write_text(
            page(st["about_title"], st["about_desc"], about, lang,
                 lang_url=f"/{'id/' if lang == 'en' else ''}tentang/"), encoding="utf-8")

        # ---- search.json ----
        (pre / "search.json").write_text(json.dumps(
            [{"title": a["title"], "excerpt": a["excerpt"], "tags": a["tags"],
              "date": tgl(lang, a["date"]), "url": art_url(a["slug"], lang)}
             for a in arts], ensure_ascii=False), encoding="utf-8")

        # ---- rss ----
        items = "".join(
            f"""<item><title>{html.escape(a['title'])}</title>
            <link>{SITE_URL}{art_url(a['slug'], lang)}</link>
            <description>{html.escape(a['excerpt'])}</description>
            <pubDate>{format_datetime(datetime.strptime(a['date'], '%Y-%m-%d'))}</pubDate>
            <guid>{SITE_URL}{art_url(a['slug'], lang)}</guid></item>"""
            for a in arts[:20])
        rss = (f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0">\n<channel>\n'
               f"<title>llunatic-lab ({lang})</title><link>{SITE_URL}/{pfx(lang)}</link>\n"
               f"<description>{html.escape(st['rss_desc'])}</description>\n"
               f"<language>{lang}</language>\n{items}\n</channel>\n</rss>")
        (pre / "rss.xml").write_text(rss, encoding="utf-8")

    # ---- sitemap (both langs) ----
    urls = []
    for lang in ("en", "id"):
        arts = [pairs[s][lang] for s in slugs if lang in pairs[s]]
        if not arts:
            continue
        urls.append((f"{pfx(lang)}", "2026-10-06"))
        urls.append((f"{pfx(lang)}arsip/", "2026-10-06"))
        urls.append((f"{pfx(lang)}tentang/", "2026-10-06"))
        urls += [(f"{pfx(lang)}artikel/{a['slug']}/", a["date"]) for a in arts]
        urls += [(f"{pfx(lang)}tag/{t}/", "2026-10-06")
                 for t in sorted({t for a in arts for t in a["tags"]})]
    sm = ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset '
          'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(
          f"  <url><loc>{SITE_URL}/{u}</loc><lastmod>{d}</lastmod></url>\n"
          for u, d in urls) + "</urlset>")
    (PUBLIC / "sitemap.xml").write_text(sm, encoding="utf-8")

    total = sum(1 for v in pairs.values() for _ in v)
    print(f"built {total} pages ({len(slugs)} slugs) -> {PUBLIC}")

if __name__ == "__main__":
    main()
