#!/usr/bin/env python3
"""Builds the blog of katianacordoba.com.

What it does, from blog/_src/:
  * one page per article and per language   blog/<slug>/  ·  blog/en/<slug>/  ·  blog/es/<slug>/
  * one blog page per language               blog/  ·  blog/en/  ·  blog/es/
  * the "latest article" section on the three home pages (index.html, en.html, es.html),
    between the markers <!-- blog:latest:start --> and <!-- blog:latest:end -->
  * the blog addresses in sitemap.xml

To publish a new article:
  1. put its three texts in blog/_src/<id>.fr.md, <id>.en.md, <id>.es.md
     (first line "# Title", then the text exactly as written: paragraphs, "### " subtitles, "> " quotes)
  2. add it at the TOP of blog/_src/articles.json (newest first) with its three slugs
     ("date": "YYYY-MM-DD" is optional: when it is there, the date is shown; without it, no date appears)
  3. run:  python3 tools/build_blog.py
The texts are never rewritten: the script only turns them into HTML.
"""
import html, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'blog', '_src')
SITE = 'https://www.katianacordoba.com/'
LANGS = ['fr', 'en', 'es']

T = {
  'fr': dict(html='fr-CA', og='fr_CA', name='Français', short='FR',
             home='', home_label='Accueil', blog_h1='Le <em>blog.</em>', blog_title='Blog',
             blog_desc="Le blog de Katiana Cordoba, accompagnement individuel et soins sonores à Gatineau.",
             more='Lire la suite', all='Tous les articles', also='À lire aussi',
             section='Sur le <em>blog.</em>', tag='Accompagnement individuel et soins sonores',
             skip='Aller au contenu', lang_nav='Langue', back_home='Katiana Cordoba, retour à l’accueil',
             place='En personne à Gatineau', share='share-fr.jpg', book='Réserver une séance',
             months=['janvier','février','mars','avril','mai','juin','juillet','août','septembre','octobre','novembre','décembre']),
  'en': dict(html='en', og='en_CA', name='English', short='EN',
             home='en.html', home_label='Home', blog_h1='The <em>blog.</em>', blog_title='Blog',
             blog_desc="The blog of Katiana Cordoba, individual support and sound healing in Gatineau.",
             more='Read more', all='All articles', also='Also on the blog',
             section='From the <em>blog.</em>', tag='Individual support and sound healing',
             skip='Skip to content', lang_nav='Language', back_home='Katiana Cordoba, back to the home page',
             place='In person in Gatineau', share='share-en.jpg', book='Book a session',
             months=['January','February','March','April','May','June','July','August','September','October','November','December']),
  'es': dict(html='es', og='es_CO', name='Español', short='ES',
             home='es.html', home_label='Inicio', blog_h1='El <em>blog.</em>', blog_title='Blog',
             blog_desc="El blog de Katiana Cordoba, acompañamiento individual y sonoterapia en Gatineau.",
             more='Seguir leyendo', all='Todos los artículos', also='También en el blog',
             section='En el <em>blog.</em>', tag='Acompañamiento individual y sonoterapia',
             skip='Ir al contenido', lang_nav='Idioma', back_home='Katiana Cordoba, volver al inicio',
             place='En persona en Gatineau', share='share-es.jpg', book='Agenda una sesión',
             months=['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre']),
}
HOME_FILE = {'fr': 'index.html', 'en': 'en.html', 'es': 'es.html'}


def esc(s):
    return html.escape(s, quote=False)


def typo(s, lang):
    """French only: a space before : ; ! ? » and after « never breaks the line (the words are unchanged)."""
    if lang != 'fr':
        return s
    s = re.sub(r' ([:;!?\u00bb])', '\u00a0\\1', s)
    return s.replace('\u00ab ', '\u00ab\u00a0')


def title_html(s, lang):
    """A title never breaks inside a hyphenated word (soi-même)."""
    return re.sub(r'(\S+-\S+)', r'<span class="nw">\1</span>', esc(typo(s, lang)))


def fmt(s, lang):
    """Escaped text, with **bold** and *italics* kept as written in the doc."""
    s = esc(typo(s, lang))
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    return re.sub(r'\*(.+?)\*', r'<em>\1</em>', s)


def plain(s):
    return s.replace('*', '')


def attr(s):
    return html.escape(s, quote=True)


def date_html(a, lang, cls='date'):
    """The article's date line, or nothing when the article has no date."""
    d = a.get('date')
    if not d:
        return ''
    return f'<p class="{cls}"><time datetime="{d}">{nice_date(d, lang)}</time></p>'


def nice_date(d, lang):
    y, m, day = (int(x) for x in d.split('-'))
    mo = T[lang]['months'][m - 1]
    if lang == 'fr':
        return f"{'1er' if day == 1 else day} {mo} {y}"
    if lang == 'en':
        return f"{mo} {day}, {y}"
    return f"{day} de {mo} de {y}"


# ---------------------------------------------------------------- reading --
def read_article(aid, lang):
    raw = open(os.path.join(SRC, f'{aid}.{lang}.md'), encoding='utf-8').read().strip()
    lines = raw.split('\n')
    if not lines[0].startswith('# '):
        sys.exit(f'{aid}.{lang}.md must start with "# Title"')
    title = lines[0][2:].strip()
    blocks = [b.strip() for b in re.split(r'\n\s*\n', '\n'.join(lines[1:]).strip()) if b.strip()]
    return title, blocks


def body_html(blocks, lang):
    out, first = [], None
    for i, b in enumerate(blocks):
        if b.startswith('### '):
            out.append(f'<h2>{fmt(b[4:].strip(), lang)}</h2>')
        elif all(re.match(r'\d+\. ', l.strip()) for l in b.split('\n')):
            items = ''.join(f'<li>{fmt(re.sub(r"^\d+\. ", "", l.strip()), lang)}</li>' for l in b.split('\n'))
            out.append(f'<ol>{items}</ol>')
        elif b.startswith('>'):
            inner = ' '.join(l.lstrip('>').strip() for l in b.split('\n'))
            out.append(f'<blockquote><p>{fmt(inner, lang)}</p></blockquote>')
        elif i == len(blocks) - 1 and b == 'Katiana':
            out.append(f'<p class="sig">{esc(b)}</p>')
        else:
            txt = ' '.join(l.strip() for l in b.split('\n'))
            out.append(f'<p>{fmt(txt, lang)}</p>')
            if first is None:
                first = plain(txt)
    return '\n'.join(out), first


def clip(s, n=158):
    if len(s) <= n:
        return s
    cut = s[:n].rsplit(' ', 1)[0].rstrip(',;:')
    return cut + '…'


# ---------------------------------------------------------------- paths ----
def blog_path(lang):
    return 'blog/' if lang == 'fr' else f'blog/{lang}/'


def art_path(a, lang):
    return blog_path(lang) + a['slugs'][lang] + '/'


def rel(prefix, path):
    return (prefix + path) or './'


# ---------------------------------------------------------------- pieces ---
MARK = ('<svg class="mk" viewBox="0 0 64 48" aria-hidden="true">'
        '<path class="lv" d="M32 46C20 46 8 41 2 33 14 32 26 36 32 46ZM32 46C44 46 56 41 62 33 50 32 38 36 32 46Z"/>'
        '<path class="pt" d="M32 43C22 38 13 30 9 20 20 22 29 32 32 43Z"/><path class="pt" d="M32 43C42 38 51 30 55 20 44 22 35 32 32 43Z"/>'
        '<path class="pt" d="M32 43C25 35 20 24 20 12 28 18 32 30 32 43Z"/><path class="pt" d="M32 43C39 35 44 24 44 12 36 18 32 30 32 43Z"/>'
        '<path class="pt c" d="M32 3C38 14 38 30 32 42 26 30 26 14 32 3Z"/></svg>')
ARROW = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="1.8" '
         'stroke-linecap="round" stroke-linejoin="round" d="M5 12h14M13 6l6 6-6 6"/></svg>')
BACK = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="1.8" '
        'stroke-linecap="round" stroke-linejoin="round" d="M19 12H5M11 18l-6-6 6-6"/></svg>')
BLOOM = ('<svg class="bloom" viewBox="0 0 30 22" aria-hidden="true"><path fill="#ECC4B8" d="M15 21C9 17 5 11 4 3 11 5 14 12 15 21Z"/>'
         '<path fill="#ECC4B8" d="M15 21C21 17 25 11 26 3 19 5 16 12 15 21Z"/><path fill="#D9A193" d="M15 1C19 7 19 15 15 21 11 15 11 7 15 1Z"/>'
         '<path fill="#EFCB8E" fill-opacity=".7" d="M15 21C13 18 13 15 15 12 17 15 17 18 15 21Z"/></svg>')
ICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 48'%3E%3Cpath fill='%235F6E34' "
        "d='M32 46C20 46 8 41 2 33 14 32 26 36 32 46ZM32 46C44 46 56 41 62 33 50 32 38 36 32 46Z'/%3E%3Cpath fill='%23C26C86' "
        "d='M32 3C38 14 38 30 32 42 26 30 26 14 32 3Z'/%3E%3Cpath fill='%23E3A2B4' d='M32 43C22 38 13 30 9 20 20 22 29 32 32 43ZM32 "
        "43C42 38 51 30 55 20 44 22 35 32 32 43Z'/%3E%3C/svg%3E")


def head(lang, prefix, title, desc, path, alternates, og_type='website', extra=''):
    t = T[lang]
    alts = ''.join(f'<link rel="alternate" hreflang="{T[l]["html"]}" href="{SITE}{p}">\n' for l, p in alternates.items())
    alts += f'<link rel="alternate" hreflang="x-default" href="{SITE}{alternates["fr"]}">\n'
    return f'''<!doctype html>
<html lang="{t['html']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{attr(desc)}">
<meta name="theme-color" content="#FBF6F1">
<link rel="canonical" href="{SITE}{path}">
{alts}<meta property="og:type" content="{og_type}">
<meta property="og:url" content="{SITE}{path}">
<meta property="og:title" content="{attr(title)}">
<meta property="og:description" content="{attr(desc)}">
<meta property="og:image" content="{SITE}assets/{t['share']}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="{t['og']}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{ICON}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500&family=Figtree:wght@400;500;600&display=swap">
<link rel="stylesheet" href="{prefix}blog/blog.css">
{extra}</head>
<body>
<a class="skip" href="#main">{t['skip']}</a>
<div class="glow" aria-hidden="true"></div>
'''


def topbar(lang, prefix, lang_links, on_blog=False):
    t = T[lang]
    langs = ''.join(
        f'<a class="lg" href="{rel(prefix, p)}" hreflang="{T[l]["html"]}" lang="{T[l]["html"]}" aria-label="{T[l]["name"]}"'
        + (' aria-current="true"' if l == lang else '') + f'>{T[l]["short"]}</a>'
        for l, p in lang_links.items())
    return f'''<header class="top">
  <a class="brand" href="{rel(prefix, t['home'])}" aria-label="{attr(t['back_home'])}">{MARK}<span class="bn"><b>Katiana Cordoba</b><small>{t['tag']}</small></span></a>
  <nav class="tnav" aria-label="{t['lang_nav']}"><a class="tb" href="{rel(prefix, blog_path(lang))}"{' aria-current="page"' if on_blog else ''}>{t['blog_title']}</a><span class="lgs">{langs}</span></nav>
</header>
'''


def footer(lang, prefix):
    t = T[lang]
    return f'''<footer class="foot">
  <div class="foot-in">
    <a class="fbrand" href="{rel(prefix, t['home'])}">{MARK}<span>Katiana Cordoba</span></a>
    <p>{t['tag']} · {t['place']}</p>
    <p class="flinks"><a href="{rel(prefix, t['home'])}">{t['home_label']}</a><span aria-hidden="true">·</span><a href="{rel(prefix, blog_path(lang))}">{t['blog_title']}</a><span aria-hidden="true">·</span><a href="{rel(prefix, t['home'])}#contact">Contact</a></p>
  </div>
</footer>
</body>
</html>
'''


def card(a, lang, prefix, heading='h2'):
    t = T[lang]
    href = rel(prefix, art_path(a, lang))
    return f'''<li class="card"><article>
  {date_html(a, lang)}
  <{heading} class="ct"><a href="{href}">{title_html(a['t'][lang], lang)}</a></{heading}>
  <p class="cx">{esc(typo(a['first'][lang], lang))}</p>
  <a class="more" href="{href}" aria-label="{t['more']}{' : ' if lang == 'fr' else ': '}{attr(a['t'][lang])}">{t['more']} {ARROW}</a>
</article></li>'''


# ---------------------------------------------------------------- pages ----
def article_page(a, lang, arts):
    t = T[lang]
    path = art_path(a, lang)
    prefix = '../' * path.count('/')
    alternates = {l: art_path(a, l) for l in LANGS}
    desc = clip(a['first'][lang])
    ld = {
        "@context": "https://schema.org", "@type": "BlogPosting",
        "headline": a['t'][lang], "inLanguage": t['html'],
        "url": SITE + path, "mainEntityOfPage": SITE + path, "image": SITE + 'assets/' + t['share'],
        "description": desc,
        "author": {"@type": "Person", "name": "Katiana Cordoba", "url": SITE},
        "publisher": {"@type": "Person", "name": "Katiana Cordoba", "url": SITE},
    }
    if a.get('date'):
        ld['datePublished'] = a['date']
    extra = '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + '</script>\n'
    others = [o for o in arts if o['id'] != a['id']][:2]
    also = ''
    if others:
        also = (f'<section class="also" aria-labelledby="also-h"><h2 id="also-h" class="sh">{t["also"]}</h2>'
                f'<ul class="cards">{"".join(card(o, lang, prefix, "h3") for o in others)}</ul></section>\n')
    return (head(lang, prefix, f"{a['t'][lang]} · Katiana Cordoba", desc, path, alternates, 'article', extra)
            + topbar(lang, prefix, alternates)
            + f'''<main id="main" class="page">
<article class="post" lang="{t['html']}">
  <a class="back" href="{rel(prefix, blog_path(lang))}">{BACK} {t['all']}</a>
  <header class="ph">
    {date_html(a, lang)}
    <h1>{title_html(a['t'][lang], lang)}</h1>
    {BLOOM}
  </header>
  <div class="prose">
{a['body'][lang]}
  </div>
</article>
{also}<p class="allrow"><a class="soft" href="{rel(prefix, blog_path(lang))}">{t['all']} {ARROW}</a></p>
</main>
''' + footer(lang, prefix))


def index_page(lang, arts):
    t = T[lang]
    path = blog_path(lang)
    prefix = '../' * path.count('/')
    alternates = {l: blog_path(l) for l in LANGS}
    cards = ''.join(card(a, lang, prefix) for a in arts)
    return (head(lang, prefix, f"{t['blog_title']} · Katiana Cordoba", t['blog_desc'], path, alternates)
            + topbar(lang, prefix, alternates, True)
            + f'''<main id="main" class="page">
  <header class="bh"><h1>{t['blog_h1']}</h1>{BLOOM}</header>
  <ul class="cards">{cards}</ul>
</main>
''' + footer(lang, prefix))


def home_section(lang, a):
    t = T[lang]
    href = art_path(a, lang)
    return f'''<!-- blog:latest:start -->
<section id="blog" class="ex blog9" data-breath data-sc-act="flow" aria-labelledby="blog-h">
  <div class="wrap">
    <h2 id="blog-h" class="d h2" data-sc-in data-tremble>{t['section']}</h2>
    <article class="bl9" data-sc-in>
      {date_html(a, lang, 'bl9-date')}
      <h3 class="d bl9-t"><a href="{href}">{title_html(a['t'][lang], lang)}</a></h3>
      <p class="bl9-x">{esc(typo(a['first'][lang], lang))}</p>
      <p class="bl9-go"><a class="bl9-more" href="{href}">{t['more']} {ARROW}</a><a class="bl9-all" href="{blog_path(lang)}">{t['all']}</a></p>
    </article>
  </div>
</section>
<!-- blog:latest:end -->'''


# ---------------------------------------------------------------- build ----
def write(rel_path, text):
    full = os.path.join(ROOT, rel_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as f:
        f.write(text)


def main():
    meta = json.load(open(os.path.join(SRC, 'articles.json'), encoding='utf-8'))['articles']
    for a in meta:
        a['t'], a['body'], a['first'] = {}, {}, {}
        for l in LANGS:
            title, blocks = read_article(a['id'], l)
            a['t'][l] = title
            a['body'][l], a['first'][l] = body_html(blocks, l)

    for l in LANGS:
        write(blog_path(l) + 'index.html', index_page(l, meta))
        for a in meta:
            write(art_path(a, l) + 'index.html', article_page(a, l, meta))

    # home pages: the latest article, between the markers
    for l in LANGS:
        p = os.path.join(ROOT, HOME_FILE[l])
        s = open(p, encoding='utf-8').read()
        new, n = re.subn(r'<!-- blog:latest:start -->.*?<!-- blog:latest:end -->',
                         lambda m: home_section(l, meta[0]), s, flags=re.S)
        if n != 1:
            sys.exit(f'{HOME_FILE[l]}: blog markers not found exactly once ({n})')
        if new != s:
            open(p, 'w', encoding='utf-8').write(new)

    # sitemap: keep everything that is not the blog, then list the blog pages
    sm_path = os.path.join(ROOT, 'sitemap.xml')
    sm = open(sm_path, encoding='utf-8').read()
    sm = re.sub(r'\s*<!-- blog:start -->.*?<!-- blog:end -->', '', sm, flags=re.S)
    newest = max((a['date'] for a in meta if a.get('date')), default='')
    urls = []

    def url(path, alts, last):
        links = ''.join(f'\n    <xhtml:link rel="alternate" hreflang="{T[k]["html"]}" href="{SITE}{v}"/>' for k, v in alts.items())
        links += f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{SITE}{alts["fr"]}"/>'
        lm = f'\n    <lastmod>{last}</lastmod>' if last else ''
        return f'  <url>\n    <loc>{SITE}{path}</loc>{lm}{links}\n  </url>'
    for l in LANGS:
        urls.append(url(blog_path(l), {k: blog_path(k) for k in LANGS}, newest))
    for a in meta:
        for l in LANGS:
            urls.append(url(art_path(a, l), {k: art_path(a, k) for k in LANGS}, a.get('date')))
    block = '\n  <!-- blog:start -->\n' + '\n'.join(urls) + '\n  <!-- blog:end -->\n'
    sm = sm.replace('</urlset>', block.lstrip('\n') + '</urlset>') if '</urlset>' in sm else sm
    sm = re.sub(r'\n+  <!-- blog:start -->', '\n  <!-- blog:start -->', sm)
    open(sm_path, 'w', encoding='utf-8').write(sm)

    print(f'{len(meta)} articles × {len(LANGS)} languages built. Home shows: {meta[0]["t"]["fr"]}')


if __name__ == '__main__':
    main()
