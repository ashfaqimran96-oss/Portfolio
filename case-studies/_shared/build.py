# Generates the case-study pages, "quiet edition": a light page, one dark band for the journey, little text on screen
# and the detail one click away. Order: the name and a live recording, the overview with results, four kinds of
# thinking (a lens the reader can turn on), the problem, the journey, the decisions, the AI workflow, the versions,
# the system, learnings, close.
# Run: python3 -I build.py <out-root>   (writes <out-root>/case-studies/<slug>/index.html)
#
# Writing conventions in the deck:
#   "~text"   a draft written from the evidence; the author must check it (?review marks these)
#   "?text"   a fact only the author can add; renders as an "Add" box
#   **bold**  and *emphasis* inside any string
import sys, os, re, html

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAIL = "ar.ashfaqimran96@gmail.com"

def esc(s): return html.escape(s, quote=True)

def inline(s):
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    return re.sub(r"\*(.+?)\*", r"<em>\1</em>", s)

MARK = re.compile(r"(?:^|(?<=\s))([~?])(?=\S)")

def t(s):
    """One string of copy: plain text, then from a ~ a draft, or from a ? a gap for the author."""
    m = MARK.search(s)
    if not m: return inline(s)
    head, rest = s[:m.start()], s[m.end():]
    if m.group(1) == "?":
        label, _, more = rest.partition("|")
        gap = f'<span class="todo"><b>Add: {inline(label.strip())}</b> {inline(more.strip())}</span>'
        return (inline(head) + gap) if head.strip() else gap
    return inline(head) + f'<span class="draft">{t(rest) if MARK.search(rest) else inline(rest)}</span>'

def p(s, cls=""):
    if s.startswith("?"): return f'<div class="todo-wrap{" " + cls if cls else ""}">{t(s)}</div>'
    return f'<p{f" class=\"{cls}\"" if cls else ""}>{t(s)}</p>'

def plain(s): return re.sub(r"[*~]", "", s.lstrip("?~"))

# ---------- pictures of the product ----------
def media(m, cls=""):
    if not m: return ""
    k = m["kind"]
    cap = f'<figcaption>{t(m["caption"])}</figcaption>' if m.get("caption") else ""
    ar = f' style="--ar: {m["ar"]}"' if m.get("ar") else ""
    fc = f' class="{cls}"' if cls else ""
    if k == "slot":
        return f'<figure{fc}><div class="slot" role="img" aria-label="Placeholder: {esc(m["what"])}"{ar}><b>Screenshot to add</b><span>{esc(m["what"])}</span></div>{cap}</figure>'
    if k == "ui":
        return f'<figure{fc}><div class="ui-shot" data-ui>{m["html"]}</div>{cap}</figure>'
    if k == "img":
        dims = f' width="{m["w"]}" height="{m["h"]}"' if m.get("w") else ""
        return f'<figure{fc}><div class="screen"><img class="zoomable" src="{m["src"]}" alt="{esc(m["alt"])}"{dims} loading="lazy"></div>{cap}</figure>'
    if k == "loop":  # the look at the solution: a real recording, looping
        return (f'<figure{fc}><div class="screen"><video src="{m["src"]}" poster="{m["poster"]}" autoplay muted loop playsinline preload="auto" '
                f'aria-label="{esc(m["alt"])}" width="1600" height="900"></video></div>{cap}</figure>')
    raise ValueError(k)

def shot(m, notes, i, on):
    """One journey screen: plays once when its step is reached, rests on the last frame, where the pins appear."""
    pins = "".join(f'<span class="pin" style="--x:{x}%;--y:{y}%" aria-hidden="true">{n+1}</span>' for n, (_, _, x, y) in enumerate(notes))
    if m["kind"] != "live":  # pages without recordings show their picture in the same frame
        inner = media(m).replace("<figure>", "").replace("</figure>", "")
        return f'<div class="shot{" is-on" if on else ""}" data-shot="{i}">{inner}</div>'
    return (f'<div class="shot shot-live{" is-on" if on else ""}" data-shot="{i}"><video src="{m["src"]}" poster="{m["poster"]}" muted playsinline preload="{"auto" if on else "none"}" '
            f'aria-label="{esc(m["alt"])}" width="1600" height="900"></video><div class="pins">{pins}</div></div>')

# ---------- the lens: four kinds of thinking a reader can turn on ----------
LENSES = [
    ("product", "Product thinking", "What to build, in what order, and what it costs."),
    ("content", "Content thinking", "The words and structure that make a choice feel easy."),
    ("analytical", "Analytical thinking", "Evidence first: numbers, comparisons and gaps."),
    ("ai", "AI fluency", "Designing for AI, and using AI to move faster."),
]
LNAME = {k: n for k, n, _ in LENSES}

def lens_attr(d):
    """data-lens="product content" on anything the deck tags, so the lens can find it."""
    ls = d.get("lens") if isinstance(d, dict) else None
    return f' data-lens="{" ".join(ls)}"' if ls else ""

def lens_notes(d):
    ls = d.get("lens") if isinstance(d, dict) else None
    if not ls: return ""
    return "".join(f'<p class="lens-note" data-for="{k}"><b>{LNAME[k]}</b> {t(v)}</p>' for k, v in ls.items())

def count_lens(c):
    n = {k: 0 for k, _, _ in LENSES}
    def walk(x):
        if isinstance(x, dict):
            for k in (x.get("lens") or {}): n[k] += 1
            for v in x.values(): walk(v)
        elif isinstance(x, (list, tuple)):
            for v in x: walk(v)
    walk(c); return n

# ---------- the sections ----------
def sec_overview(c):
    ov = c.get("overview") or dict(challenge=c["intro"]["challenge"], approach=c["intro"]["summary"], outcome=c["intro"]["outcome"])
    cols = "".join(f'<div class="rise"><h3>{a}</h3>{p(ov[k])}</div>' for k, a in (("challenge", "Challenge"), ("approach", "Approach"), ("outcome", "Outcome")))
    figs = ""
    for v, lab in c["results"]["figures"]:
        if v == "todo": figs += f'<div class="rise"><dt class="dt-todo">Add a figure</dt><dd>{esc(lab)}</dd></div>'
        else: figs += f'<div class="rise"><dt>{esc(v)}</dt><dd>{t(lab)}</dd></div>'
    hook = c["hook"][0]
    q = f'<blockquote class="hook rise"><p>{t(hook)}</p></blockquote>' if not hook.startswith("?") else ""
    return (f'<section class="sec" id="overview" aria-labelledby="overview-h"><div class="wrap">'
            f'<div class="ov-top"><h2 id="overview-h" class="rise">Overview</h2>{q}</div>'
            f'<div class="ov-cols">{cols}</div>{sec_owned(c)}'
            f'<dl class="figures" aria-label="Results">{figs}</dl><p class="source rise">{t(c["results"]["source"])}</p></div></section>')

def sec_owned(c):
    o = c.get("owned")
    if not o: return ""
    items = "".join(f'<li class="rise"><h3>{esc(a)}</h3>{p(b)}</li>' for a, b in o)
    return f'<div class="owned"><h3 class="owned-h rise">What I owned</h3><ul class="owned-list">{items}</ul></div>'

def sec_lessons(c):
    d = c.get("lessons")
    if not d: return ""
    rules = "".join(f'<li class="rise"{lens_attr(r)}><h3>{t(r["title"])}</h3>{p(r["text"])}{lens_notes(r)}</li>' for r in d["rules"])
    fig = media(d["media"], "lessons-fig rise") if d.get("media") else ""
    return (f'<section class="sec" id="lessons" aria-labelledby="lessons-h"><div class="wrap">'
            f'<div class="split-head"><h2 id="lessons-h" class="rise">{t(d["h2"])}</h2>{p(d["lead"], "lead rise")}</div>'
            f'<div class="lessons"><ul class="lesson-rules">{rules}</ul>{fig}</div></div></section>')

def sec_roadmap(c):
    d = c.get("roadmap")
    if not d: return ""
    cols = ""
    for h in d["horizons"]:
        its = "".join(f'<li{lens_attr(it)}><b>{t(it["title"])}</b>{p(it["text"]) if it.get("text") else ""}{lens_notes(it)}</li>' for it in h["items"])
        cols += f'<div class="horizon rise horizon--{h["key"]}"><h3>{esc(h["name"])}</h3><p class="hz-when">{t(h["when"])}</p><ul>{its}</ul></div>'
    how = "".join(f'<li class="rise">{t(x)}</li>' for x in d.get("how", []))
    vis = d.get("vision")
    return (f'<section class="sec" id="roadmap" aria-labelledby="roadmap-h"><div class="wrap">'
            f'<div class="split-head"><h2 id="roadmap-h" class="rise">{t(d["h2"])}</h2>{p(d["lead"], "lead rise")}</div>'
            + (f'<div class="vision rise"{lens_attr(vis)}><p class="vision-k">The vision</p><p class="vision-t">{t(vis["text"])}</p>{lens_notes(vis)}</div>' if vis else "")
            + f'<div class="horizons">{cols}</div>'
            + (f'<div class="ai-rules"><h3 class="rise">{esc(d.get("how_h", "How I decided what comes next"))}</h3><ul>{how}</ul></div>' if how else "")
            + '</div></section>')

def sec_thinking(c):
    n = count_lens(c)
    if not any(n.values()): return ""
    th = c.get("thinking", {})
    cards = "".join(
        f'<li class="rise"><button class="lens-card" type="button" data-lens-set="{k}" aria-pressed="false">'
        f'<span class="lc-name">{nm}</span><span class="lc-line">{t(th.get(k, line))}</span>'
        f'<span class="lc-count">{n[k]} moment{"s" if n[k] != 1 else ""} on this page</span></button></li>'
        for k, nm, line in LENSES if n[k])
    return (f'<section class="sec sec--thinking" id="thinking" aria-labelledby="thinking-h"><div class="wrap">'
            f'<div class="split-head"><h2 id="thinking-h" class="rise">How I thought about it</h2>'
            f'<p class="lead rise">Pick a lens to see where each kind of thinking shaped the product. The page marks every moment, and you can step through them.</p></div>'
            f'<ul class="lenses">{cards}</ul></div></section>')

def sec_problem(d):
    fig = d.get("figure")
    left = (f'<div class="figure rise"><p class="big" aria-hidden="true">{esc(fig[0])}</p>'
            f'<p class="figure-cap"><span class="sr">{esc(fig[0])} </span>{t(fig[1])}</p></div>') if fig else "".join(media(m, "rise") for m in (d.get("evidence") or [])[:1])
    return (f'<section class="sec" id="problem" aria-labelledby="problem-h"><div class="wrap">'
            f'<div class="problem"{lens_attr(d)}><div class="problem-left">{left}</div><div class="problem-right">'
            f'<h2 id="problem-h" class="rise">{t(d["h2"])}</h2><div class="rise">{"".join(p(x) for x in d["paras"])}</div>{lens_notes(d)}</div></div></div></section>')

def sec_journey(d):
    steps, shots, segs = "", "", ""
    for i, s in enumerate(d["steps"]):
        notes = s.get("notes", [])
        nl = "".join(f'<li><b>{t(b)}</b> <span>{t(sp)}</span></li>' for b, sp, _, _ in notes)
        steps += (f'<li class="step{" is-active" if i == 0 else ""}" data-step="{i}"{lens_attr(s)}><h3>{t(s["title"])}</h3>{p(s["thought"], "thought")}'
                  + (f'<ol class="notes">{nl}</ol>' if nl else "") + lens_notes(s) + '</li>')
        shots += shot(s["media"], notes, i, i == 0)
        segs += f'<i{" class=\"on\"" if i == 0 else ""}></i>'
    return (f'<section class="sec sec--night sec--journey" id="journey" aria-labelledby="journey-h"><div class="wrap">'
            f'<div class="split-head"><h2 id="journey-h" class="rise">{t(d["h2"])}</h2>{p(d["lead"], "lead rise")}</div>'
            f'<div class="steps"><figure class="steps-media"><div class="frame">{shots}</div>'
            f'<figcaption><span class="segs" aria-hidden="true">{segs}</span><button class="replay" type="button">Replay</button></figcaption></figure>'
            f'<ol class="steps-list" aria-label="The steps of the journey">{steps}</ol></div></div></section>')

def sec_decisions(d):
    body = ""
    for i, it in enumerate(d["items"]):
        opts = "".join(f'<li class="option{" chosen" if ch else ""}"><span class="opt-tag">{"Chosen" if ch else esc(tag)}</span><b>{t(nm)}</b><span>{t(tr)}</span></li>'
                       for tag, nm, tr, ch in it["options"])
        before, after = it["before"], it.get("after")
        bm = media(before.get("media")) if before.get("media") else ""
        am = media(after, "ds-shot rise") if after else ""
        body += (f'<article class="ds" id="d{i+1}" aria-labelledby="d{i+1}-h"{lens_attr(it)}>'
                 f'<div class="ds-head"><h3 id="d{i+1}-h" class="rise">{t(it.get("h3") or it["title"])}</h3>{p(it["hook"], "ds-hook rise")}</div>'
                 + (f'<ul class="options rise" aria-label="The options">{opts}</ul>' if opts else "")
                 + f'<div class="ds-body"><div class="ds-why rise">{p(it["why"])}{lens_notes(it)}</div>{am}</div>'
                 f'<details class="ds-more"><summary>Before, what I did, and what happened</summary><div class="ds-more-in">'
                 f'<div><h4>Before</h4>{p(before["text"])}{bm}</div>'
                 f'<div><h4>What I did</h4><ul class="actions">{"".join(f"<li>{t(a)}</li>" for a in it["actions"])}</ul></div>'
                 f'<div><h4>What happened</h4>{p(it["result"])}</div></div></details>'
                 f'</article>')
    return (f'<section class="sec" id="decisions" aria-labelledby="decisions-h"><div class="wrap">'
            f'<div class="split-head"><h2 id="decisions-h" class="rise">{t(d["h2"])}</h2>{p(d["lead"], "lead rise")}</div>'
            f'<div class="ds-list">{body}</div></div></section>')

TOOL_ICON = {"Claude": "claude-chat.png", "Claude Code": "claude-code.png", "Claude Cowork": "claude-cowork.png", "Claude Design": "claude-design.png",
             "Higgsfield": "higgsfield.png", "Lovable": "lovable.webp", "Midjourney": "midjourney.webp"}

TOOL_MONO = {"NotebookLM": "NL", "Notion": "N", "Figma": "F", "n8n": "n8", "Zapier": "Z", "ElevenLabs": "11", "After Effects": "Ae", "Replit": "R"}

def tool_mark(name, size=20):
    ic = TOOL_ICON.get(name)
    if ic: return f'<img src="../../assets/tools/{ic}" alt="" width="{size}" height="{size}" loading="lazy">'
    return f'<span class="mono" aria-hidden="true">{esc(TOOL_MONO.get(name, name[:1]))}</span>'

def tool_chip(name):
    mark = tool_mark(name)
    return f'<li class="tool">{mark}<span>{esc(name)}</span></li>'

def sec_workflow(c):
    w = c.get("workflow")
    if not w:  # pages without their own workflow keep the plain AI-versus-me lists
        d = c["ai"]; li = lambda xs: "".join(f'<li>{t(x)}</li>' for x in xs)
        lead = p(d["lead"], "lead rise") if d.get("lead") else ""
        return (f'<section class="sec sec--soft" id="ai" aria-labelledby="ai-h"><div class="wrap">'
                f'<div class="split-head"><h2 id="ai-h" class="rise">{t(d["h2"])}</h2>{lead}</div>'
                f'<div class="ai"><div class="rise"><h3>What AI executed</h3><ul>{li(d["by_ai"])}</ul></div>'
                f'<div class="rise"><h3>What I decided</h3><ul>{li(d["by_me"])}</ul></div></div></div></section>')
    tabs, panels = "", ""
    for i, s in enumerate(w["stages"]):
        on = i == 0
        icons = "".join(tool_mark(x, 18) for x in s["tools"])
        tabs += (f'<button class="stage" type="button" role="tab" id="st{i}" aria-controls="sp{i}" aria-selected="{str(on).lower()}" tabindex="{0 if on else -1}">'
                 f'<span class="stage-name">{esc(s["name"])}</span><span class="stage-icons" aria-hidden="true">{icons}</span></button>')
        panels += (f'<div class="stage-panel" role="tabpanel" id="sp{i}" aria-labelledby="st{i}"{"" if on else " hidden"}{lens_attr(s)}>'
                   f'<ul class="tools" aria-label="Tools">{"".join(tool_chip(x) for x in s["tools"])}</ul>'
                   f'<div class="sp-cols"><div><h4>What AI did</h4>{p(s["ai"])}</div><div><h4>What I decided</h4>{p(s["me"])}</div></div>'
                   + (f'<p class="sp-link"><a href="{s["link"][1]}">{esc(s["link"][0])} →</a></p>' if s.get("link") else "") + '</div>')
    kit = "".join(f'<div class="kit-group rise"><h3>{esc(g)}</h3><ul class="tools">{"".join(tool_chip(x) for x in xs)}</ul></div>' for g, xs in w["kit"])
    rules = "".join(f'<li class="rise">{t(x)}</li>' for x in w.get("rules", []))
    return (f'<section class="sec sec--soft" id="ai" aria-labelledby="ai-h"><div class="wrap">'
            f'<div class="split-head"><h2 id="ai-h" class="rise">{t(w["h2"])}</h2>{p(w["lead"], "lead rise")}</div>'
            f'<div class="stages rise"><div class="stage-tabs" role="tablist" aria-label="Stages of the work">{tabs}</div>{panels}</div>'
            + (f'<div class="ai-rules"><h3 class="rise">{esc(w.get("rules_h", "Where AI stops"))}</h3><ul>{rules}</ul></div>' if rules else "")
            + f'<div class="kit"><h3 class="kit-h rise">{esc(w.get("kit_h", "The toolkit"))}</h3><div class="kit-grid">{kit}</div></div>'
            + (p(w["speed"], "speed rise") if w.get("speed") else "") + '</div></section>')

def sec_iterations(d):
    rounds = d.get("rounds", [])
    if not rounds:
        body = p(d["todo"]) if d.get("todo") else ""
        lead = p(d["lead"], "lead rise") if d.get("lead") else ""
        return (f'<section class="sec" id="iterations" aria-labelledby="iterations-h"><div class="wrap">'
                f'<div class="split-head"><h2 id="iterations-h" class="rise">{t(d["h2"])}</h2>{lead}</div>{body}</div></section>')
    tabs, panels = "", ""
    for i, r in enumerate(rounds):
        on = i == 0
        tabs += f'<button type="button" role="tab" id="rt{i}" aria-controls="rp{i}" aria-selected="{str(on).lower()}" tabindex="{0 if on else -1}">{esc(r["label"])}<span>{t(r["name"])}</span></button>'
        figs = "".join(f'<figure class="{"kept" if kept else "dropped"}"><img class="zoomable" src="{src}" alt="{esc(plain(nm))}" loading="lazy" width="1366" height="768">'
                       f'<figcaption><b>{t(nm)}</b><span class="verdict">{"Kept" if kept else "Dropped"}</span><span>{t(why)}</span></figcaption></figure>' for src, nm, why, kept in r["items"])
        panels += f'<div class="round" role="tabpanel" id="rp{i}" aria-labelledby="rt{i}"{"" if on else " hidden"}><p class="round-note">{t(r["note"])}</p><div class="round-row">{figs}</div></div>'
    fin = d.get("final")
    finh = (f'<div class="final">{media(fin["media"], "rise")}<div class="rise"><h3>{t(fin["title"])}</h3>{"".join(p(x) for x in fin["text"])}</div></div>') if fin else ""
    return (f'<section class="sec" id="iterations" aria-labelledby="iterations-h"><div class="wrap">'
            f'<div class="split-head"><h2 id="iterations-h" class="rise">{t(d["h2"])}</h2>{p(d["lead"], "lead rise")}</div>'
            f'<div class="rounds rise"{lens_attr(d)}><div class="round-tabs" role="tablist" aria-label="Rounds">{tabs}</div>{panels}{lens_notes(d)}</div>{finh}</div></section>')

def sec_system(d):
    lead = p(d["lead"], "lead rise") if d.get("lead") else ""
    head = f'<div class="split-head"><h2 id="system-h" class="rise">{t(d["h2"])}</h2>{lead}</div>'
    if d.get("todo"):
        return f'<section class="sec" id="system" aria-labelledby="system-h"><div class="wrap">{head}{p(d["todo"])}</div></section>'
    ty, co = d["type"], d["colours"]
    def ink(hx):
        r, g, b = (int(hx[i:i+2], 16) for i in (1, 3, 5))
        return "#000" if (0.299 * r + 0.587 * g + 0.114 * b) > 150 else "#fff"
    band = "".join(f'<li style="--c:{hx};--k:{ink(hx)};--f:{4 if i == 0 else 1}"><b>{esc(n)}</b><span>{hx}</span></li>' for i, (n, hx) in enumerate(co["swatches"]))
    rows = "".join(f'<li><span>{sz}px · {"Medium" if w == 500 else "Regular"}</span><b style="font-size:{min(sz, 40)}px;font-weight:{w}">{esc(s)}</b></li>' for sz, w, s in ty["rows"])
    comps = "".join(f'<figure class="rise"><div class="screen"><img class="zoomable" src="{src}" alt="{esc(c)}" loading="lazy"></div><figcaption>{esc(c)}</figcaption></figure>' for src, c in d["components"]["items"])
    return (f'<section class="sec" id="system" aria-labelledby="system-h"><div class="wrap">{head}'
            f'<ul class="band rise" data-ui aria-label="The colours">{band}</ul>'
            f'<div class="sys-cols"{lens_attr(d)}><div class="rise"><h3>Colour</h3>{p(co["why"])}<h3>Type: {esc(ty["family"])}</h3>{p(ty["why"])}{lens_notes(d)}</div>'
            f'<ol class="specimen rise" data-ui aria-label="Type sizes in the product">{rows}</ol></div>'
            f'<h3 class="parts-h rise">{esc(d["components"]["title"])}</h3>'
            f'<div class="parts">{comps}</div></div></section>')

def sec_reflection(d):
    learn = "".join((f'<li class="rise"><h3>{t(b)}</h3>{p(x)}</li>' if not b.startswith("?") else f'<li class="rise">{t(b)}</li>') for b, x in d["learn"])
    fut = "".join(f'<li class="rise"><h3>{t(b)}</h3>{p(x) if x else ""}</li>' for b, x in d["future"])
    return (f'<section class="sec" id="reflection" aria-labelledby="reflection-h"><div class="wrap">'
            f'<div class="refl"><div><h2 id="reflection-h" class="rise">{t(d["h2"])}</h2><ul class="learn">{learn}</ul></div>'
            f'<div><h2 class="rise">What comes next</h2><ul class="future">{fut}</ul></div></div></div></section>')

NAV = [("overview", "Overview"), ("thinking", "Thinking"), ("journey", "Journey"), ("decisions", "Decisions"), ("roadmap", "Roadmap"), ("ai", "AI workflow")]

def page(c, nxt):
    name, slug = c["name"], c["slug"]
    style = f'--accent: {c["accent"]}; --accent-ink: {c["accent_ink"]}'
    tagline = c.get("tagline") or plain(c["h1"]).split(": ", 1)[-1]
    tagline = tagline[0].upper() + tagline[1:]
    tagline = plain(tagline)
    facts = "".join(f'<div><dt>{esc(x)}</dt><dd>{t(y)}</dd></div>' for x, y in c["facts"])
    mail = f'mailto:{MAIL}?subject=About%20the%20{esc(name).replace(" ", "%20")}%20case%20study'
    has_thinking = any(count_lens(c).values())
    teaser = c["teaser"]
    if teaser.get("kind") == "slot":  # no screen yet: a cover card that states the problem
        own = "".join(f'<li>{esc(plain(a))}</li>' for a, _ in (c.get("owned") or [])[:4])
        hero_media = (f'<figure class="hero-media poster-card"><p class="pc-k">The problem</p><p class="pc-h">{t(c["problem"]["h2"])}</p>'
                      + (f'<ul class="pc-own" aria-label="What I owned">{own}</ul>' if own else "") + '</figure>')
        cap = ""
    else:
        hero_media = media(dict(teaser, caption=""), "hero-media")
        cap = f'<p class="hero-cap">{t(teaser.get("caption", ""))}</p>' if teaser.get("caption") else ""
    letters = "".join(f'<span aria-hidden="true" style="--k:{i}">{esc(ch) if ch != " " else "&nbsp;"}</span>' for i, ch in enumerate(name))
    close_img = c.get("close_img") or f'../../assets/posters/{c["poster"]}.webp'
    dock = ('<div class="dock" role="region" aria-label="Lens" hidden><span class="dock-name"></span><span class="dock-count" aria-live="polite"></span>'
            '<button type="button" class="dock-prev" aria-label="Previous moment">←</button><button type="button" class="dock-next" aria-label="Next moment">→</button>'
            '<button type="button" class="dock-off" aria-label="Turn the lens off">✕</button></div>') if has_thinking else ""
    return f'''<!doctype html>
<html lang="en" style="{style}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(c["title"])}</title>
<meta name="description" content="{esc(c["desc"])}">
<meta property="og:title" content="{esc(plain(c["h1"]))}">
<meta property="og:description" content="{esc(c["desc"])}">
<meta property="og:image" content="../../assets/posters/{c["poster"]}.webp">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
<script>document.documentElement.classList.add('js');try{{localStorage.removeItem('cs-read')}}catch(e){{}}</script>
<link rel="stylesheet" href="../_shared/guide.css">
</head>
<body>
<a class="skip" href="#main">Skip to the case study</a>
<a class="wordmark" href="../../index.html">Ashfaq Imran</a>
<header class="bar">
  <nav aria-label="Sections">
    <a href="../../index.html#story"><svg class="nav-ic" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="8" r="3.5"/><path d="M5 20c.8-3.6 3.6-5.5 7-5.5s6.2 1.9 7 5.5"/></svg><span>Story</span></a>
    <a href="../../index.html#work" class="is-on" aria-current="page"><svg class="nav-ic" viewBox="0 0 24 24" aria-hidden="true"><rect x="3.5" y="7" width="17" height="12.5" rx="2"/><path d="M9 7V5.5A1.5 1.5 0 0 1 10.5 4h3A1.5 1.5 0 0 1 15 5.5V7M3.5 12.5h17"/></svg><span>Work</span></a>
    <a href="../../index.html#road"><svg class="nav-ic" viewBox="0 0 24 24" aria-hidden="true"><circle cx="6" cy="18" r="2"/><circle cx="18" cy="6" r="2"/><path d="M8 18h7a3.5 3.5 0 0 0 0-7H9a3.5 3.5 0 0 1 0-7h7"/></svg><span>Path</span></a>
    <a href="../../index.html#kit"><svg class="nav-ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 9.5h16v9a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 4 18.5z"/><path d="M8.5 9.5V7a1.5 1.5 0 0 1 1.5-1.5h4A1.5 1.5 0 0 1 15.5 7v2.5M4 13.5h16M10.5 13.5v2h3v-2"/></svg><span>Kit</span></a>
  </nav>
  <a class="hello" href="../../index.html#contact" aria-label="Say hello"><span>Say hello</span> <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M3 5h14v10H3z M3 5l7 6 7-6"/></svg></a>
</header>
<main id="main">
<section class="hero" aria-labelledby="hero-h">
  <div class="cover"><div class="wrap cover-in">
    <h1 id="hero-h" class="h1-name" aria-label="{esc(name)}" style="--n:{max(len(name), 7)}">{letters}</h1>
    <div class="cover-row">
      <p class="h1-line">{esc(tagline)}</p>
      <div class="cover-side">
        <p class="dek">{t(c["dek"])}</p>
        <p class="hero-btns"><a class="btn btn--cover" href="#overview">Read the case study</a><a class="btn btn--cover-ghost" href="{mail}">Email me</a></p>
      </div>
    </div>
  </div></div>
  <div class="wrap stage"><div class="stage-in">{hero_media}</div>{cap}</div>
  <div class="wrap"><dl class="hero-facts">{facts}</dl></div>
</section>
{sec_overview(c)}
{sec_thinking(c)}
{sec_problem(c["problem"])}
{sec_journey(c["journey"])}
{sec_decisions(c["decisions"])}
{sec_lessons(c)}
{sec_roadmap(c)}
{sec_workflow(c)}
{sec_iterations(c["iterations"])}
{sec_system(c["system"])}
{sec_reflection(c["reflection"])}
<section class="close" aria-labelledby="close-h"><div class="wrap">
  <div class="close-text">
    <h2 id="close-h" class="rise">{t(c["close"]["h2"])}</h2>
    <p class="rise">{t(c["close"]["text"])}</p>
    <p class="close-btns rise"><a class="btn" href="{mail}">Email Ashfaq</a><a class="btn btn--ghost" href="../{nxt["slug"]}/index.html">Next: {esc(nxt["name"])}</a></p>
  </div>
  {"" if c.get("close_img") == "" else f'<figure class="close-fig rise"><div class="screen"><img src="{close_img}" alt="{esc(c.get("close_alt", "The last screen of the product"))}" loading="lazy" width="1600" height="900"></div></figure>'}
</div></section>
</main>
<footer class="foot"><div class="wrap">
  <p class="foot-name">Ashfaq Imran</p>
  <div class="foot-links"><a href="{mail}">{MAIL}</a><a href="../../index.html#work">All work</a><a href="../../index.html">Home</a><a href="#main">Back to top</a></div>
  <p class="foot-legal">Trained as an architect: a five-year degree and a year in practice, while learning product design. Designing products since 2019, at Rillusion, Sysvine Technologies and now as Head of Product Design at myAIcademy. {t(c.get("credit", ""))}</p>
</div></footer>
{dock}
<p class="review-note" role="note">Review mode: <i>highlighted</i> wording was drafted from the project files and needs your check. Boxes marked “Add” need facts only you have.</p>
<script src="../_shared/guide.js" defer></script>
</body>
</html>
'''
# The older copy deck (deck.py) describes each screen with img(), slot(), ui() and row(); these turn them into media for the new template.
def img(device, src, alt, caption, s=None, w=None, h=None):
    return dict(kind="img", frame={"phone": "phone", "web": "web", "wide": "none"}.get(device, "web"), src=src, alt=alt, caption=caption, w=w, h=h)
def slot(device, what, caption, s=None):
    return dict(kind="slot", frame="phone" if device == "phone" else "web", what=what, caption=caption, ar="9 / 16" if device == "phone" else "16 / 10")
def ui(device, inner, caption, s=None):
    return dict(kind="ui", html=inner, caption=caption)
def row(what, value, off=False, todo=False):
    return dict(what=what, value=value, off=off, todo=todo)

# ---------- the product fragments from the main page ----------
UI = {
 "mf-street": '<div class="ui"><p class="ui-meta">Equity · Large cap</p><p class="ui-title">Bluechip Growth Fund</p><p class="ui-big">₹68.42 <small>+0.84% today</small></p><svg viewBox="0 0 200 60" class="spark"><polyline points="0,50 20,44 40,46 60,36 80,38 100,28 120,30 140,20 160,22 180,12 200,8"/></svg><p class="ui-row"><span>3Y returns</span><b>14.2% p.a.</b></p><span class="ui-btn">Start SIP</span></div>',
 "godofx": '<div class="ui"><p class="ui-title">Markets</p><p class="ui-row"><span>EUR/USD</span><b>1.0842 <i class="up">+0.12%</i></b></p><p class="ui-row"><span>GBP/USD</span><b>1.2716 <i class="up">+0.31%</i></b></p><p class="ui-row"><span>USD/JPY</span><b>149.62 <i class="down">−0.18%</i></b></p><p class="ui-split"><span>Sell 1.2714</span><span>Buy 1.2718</span></p></div>',
 "healthpractice": '<div class="ui"><p class="ui-meta">Today · Tue 14 Oct</p><p class="ui-title">12 appointments</p><p class="ui-row"><span>09:30 Priya R.</span><b class="tag tag--ok">Checked in</b></p><p class="ui-row"><span>10:15 Arun K.</span><b class="tag">Confirmed</b></p><p class="ui-row"><span>11:45 Joseph T.</span><b class="tag tag--wait">Pending</b></p><span class="ui-btn">New appointment</span></div>',
 "tbil": '<div class="ui"><p class="ui-title">What does your plan cover?</p><p class="ui-row"><span>Treatment</span><b>Physiotherapy</b></p><p class="ui-row"><span>Plan</span><b>PPO · 8 visits</b></p><p class="ui-big">80% <small>covered after deductible</small></p></div>',
 "hoffmann-group": '<div class="ui"><p class="ui-meta">Tools › Torque › Wrenches</p><p class="ui-row"><span>Click type 5–25 Nm</span><b>In stock</b></p><p class="ui-row"><span>Digital 40–200 Nm</span><b>2 days</b></p><p class="ui-row"><span>Click type 60–330 Nm</span><b>In stock</b></p><span class="ui-btn ui-btn--ghost">Compare (2)</span></div>',
 "dashboards": '<div class="ui"><p class="ui-meta">Operations · last 14 days</p><p class="ui-big">94.6% <small>on time</small></p><svg viewBox="0 0 200 70" class="bars"><g><rect x="4" y="20" width="10" height="50"/><rect x="18" y="28" width="10" height="42"/><rect x="32" y="24" width="10" height="46"/><rect x="46" y="18" width="10" height="52"/><rect x="60" y="30" width="10" height="40"/><rect x="74" y="44" width="10" height="26" class="hi"/><rect x="88" y="22" width="10" height="48"/><rect x="102" y="20" width="10" height="50"/><rect x="116" y="26" width="10" height="44"/><rect x="130" y="22" width="10" height="48"/><rect x="144" y="16" width="10" height="54"/><rect x="158" y="46" width="10" height="24" class="hi"/><rect x="172" y="24" width="10" height="46"/><rect x="186" y="20" width="10" height="50"/></g></svg><p class="ui-note">On-time rate dips every Monday: weekend backlog.</p></div>',
 "lesson-pipeline": '<div class="ui"><p class="ui-meta">n8n · Lesson pipeline</p><p class="ui-title">Run in progress</p><p class="ui-row"><span>Brief from Notion</span><b class="tag tag--ok">Done</b></p><p class="ui-row"><span>Claude drafts the lesson</span><b class="tag tag--ok">Done</b></p><p class="ui-row"><span>NotebookLM fact-check</span><b class="tag tag--ok">Done</b></p><p class="ui-row"><span>ElevenLabs voice-over</span><b class="tag tag--wait">Running</b></p><span class="ui-btn">Open run</span></div>',
 "this-portfolio": '<div class="ui"><p class="ui-meta">Build log</p><p class="ui-title">How this site was made</p><p class="ui-row"><span>Key visuals and bust</span><b>Higgsfield</b></p><p class="ui-row"><span>Scroll film and code</span><b>Claude Code</b></p><p class="ui-row"><span>Copy</span><b>Claude</b></p><p class="ui-row"><span>Responsive checks</span><b>12 screen sizes</b></p><span class="ui-btn">You\'re looking at it</span></div>',
 "myaicademy": '<div class="ui"><p class="ui-meta">Role</p><p class="ui-title">Choose what you do</p><p class="ui-opt ui-opt--on">Product manager</p><p class="ui-opt">Marketing lead</p><p class="ui-opt">Founder</p><span class="ui-btn">Build my path</span></div>',
}

MY = "../myaicademy/img/"
INK = "#16120b"; PAPER = "#f4f3f1"

PAGES = [
 # ---------------------------------------------------------------- myAIcademy
 dict(slug="myaicademy", name="myAIcademy", accent="#f0581c", accent_ink=INK, poster="p5",
  poster_alt="Key visual: a smartphone built from orange sticky notes, showing a lesson",
  title="myAIcademy, a case study by Ashfaq Imran",
  desc="How Ashfaq Imran designed myAIcademy: an AI-fluency app for 20,000 leaders that starts from your role and ends in work done.",
  hero=dict(sentence="An AI-fluency app for 20,000 leaders: pick your role, learn in minutes, finish with your own work done.",
   facts=[("Live on", "iOS, Android and web"), ("Product Hunt", "#2 Product of the Day, September 2026"), ("My role", "Head of Product Design, 2025 to now")]),
  problem=dict(h2="Courses teach tools. Jobs need outcomes.",
   beats=[("Users", "Leaders finished AI courses and still could not use AI on Monday's work."),
          ("Business", "One generic course for 24 different roles meant low completion and weak renewals."),
          ("Why it mattered", "A path built for your role can end in your own work, done.")],
   ref=lambda s: img("wide", MY+"slide-problem.webp", "The problem slide from the myAIcademy pitch deck", "The problem, as the founder pitched it", s, 2000, 1124)),
  process=dict(h2="Role first, then everything else", lead="What we learned, what we tried, and the direction we kept.",
   slip=[("Researched", [row("Founder's classrooms", "10,000+ professionals"), row("Roles that kept coming up", "24 roles"), row("Interviews with leaders", "add the number", todo=True)]),
         ("Explored", [row("One course for everyone", "dropped", off=True), row("A library of prompts", "dropped", off=True), row("Role-first paths with an assistant", "kept")])],
   end=("Role-first paths, refreshed every 72 hours", "the direction"),
   ref=lambda s: img("wide", MY+"slide-question.webp", "The pitch slide asking which role the learner is in", "The question the whole product is built around", s, 2000, 1124)),
  solution=dict(h2="Every screen answers the problem", items=[
   dict(name="Pick a role first", line="Twenty-four roles, so the first screen is already about your job. Answers: one course for everyone.",
        ref=lambda s: img("phone", MY+"phone-role.webp", "The role picker in the myAIcademy app", "Onboarding: the role picker", s, 900, 1407)),
   dict(name="A welcome in your words", line="The path greets you with your role and your first outcome. Answers: courses that never mention your work.",
        ref=lambda s: img("phone", MY+"phone-welcome.webp", "The welcome screen in the myAIcademy app", "Onboarding: the welcome", s, 900, 1456)),
   dict(name="Lessons in minutes", line="Short lessons with a checkpoint and a skill passport. Answers: low completion.",
        ref=lambda s: img("phone", MY+"phone-lesson.webp", "A lesson screen in the myAIcademy app", "A lesson, with its checkpoint", s, 900, 1407)),
   dict(name="Aimy, inside ChatGPT", line="The assistant follows you into the tool you already use. Answers: learning that stays in the classroom.",
        ref=lambda s: img("wide", MY+"aimy-panel.webp", "Aimy, the myAIcademy assistant, open as a panel", "Aimy, the assistant", s, 1400, 824)),
   dict(name="Paths that refresh", line="When a tool changes, the path changes within 72 hours. Answers: lessons that go stale.",
        ref=lambda s: slot("web", "A learning path showing its last refresh date", "The path view", s)),
  ]),
  results=dict(h2="What it adds up to", figures=[("20,000+", "leaders on the platform, as the site states it"), ("#2", "Product of the Day on Product Hunt, September 2026"), ("72h", "to refresh a path after a major tool change"), ("4.3", "rating on Trustpilot"), ("todo", "completion rate, renewals, or enterprise seats")],
   owned="Product design end to end: onboarding, lessons, the role system, Aimy and the brand.",
   source="Public sources, October 2026: myaicademy.com (20k+ leaders, Trustpilot 4.3, refreshed every 72 hours), Product Hunt launch page (#2 Product of the Day), App Store and Google Play listings.")),

 # ---------------------------------------------------------------- MF Street
 dict(slug="mf-street", name="MF Street", accent="#f6c514", accent_ink=INK, poster="p0",
  poster_alt="Key visual: a staircase of bar-chart columns built from yellow sticky notes",
  title="MF Street, a case study by Ashfaq Imran",
  desc="How Ashfaq Imran designed MF Street at Rillusion: a mutual-fund investing app on web and mobile where a first SIP takes one screen.",
  hero=dict(sentence="A mutual-fund app where a first-time investor starts a monthly SIP in one screen.",
   facts=[("Studio", "Rillusion"), ("Platforms", "Web and mobile"), ("Scope", "Fund discovery, fund detail, SIP flow")]),
  problem=dict(h2="Too many funds, too many numbers.",
   beats=[("Users", "A first-time investor met 2,000 funds, forty ratios and no idea where to begin."),
          ("Business", "Every investor who left without a SIP was a customer the app had already paid to acquire."),
          ("Why it mattered", "A SIP is a monthly habit. Win the first one and the account stays.")],
   ref=lambda s: slot("phone", "The fund list before the redesign", "Before: the fund list", s)),
  process=dict(h2="One number, one action", lead="What we learned, what we tried, and the direction we kept.",
   slip=[("Researched", [row("First-time investors interviewed", "add the number", todo=True), row("Competitor apps compared", "add the number", todo=True)]),
         ("Explored", [row("A full data sheet per fund", "dropped", off=True), row("A guided quiz first", "dropped", off=True), row("One number, a chart, one button", "kept")])],
   end=("Lead with returns, end with Start SIP", "the direction"),
   ref=lambda s: slot("web", "Early sketches or wireframes of the fund card", "During: wireframes", s)),
  solution=dict(h2="Every screen answers the problem", items=[
   dict(name="One fund, one number", line="Today's price, the three-year return, and the one thing to do. Answers: forty ratios.",
        ref=lambda s: ui("phone", UI["mf-street"], "The fund card, as built", s)),
   dict(name="Start a SIP in one screen", line="Amount, date, confirm. Answers: investors who leave before the first SIP.",
        ref=lambda s: slot("phone", "The SIP flow: amount, date, confirm", "The SIP flow", s)),
   dict(name="Discover by goal", line="Funds grouped by what they are for, not by their category code. Answers: 2,000 funds and no way in.",
        ref=lambda s: slot("phone", "The discover screen with goal groups", "Discover", s)),
   dict(name="The same app on the web", line="One design system, so the desktop view is the phone view with more room. Answers: two products to maintain.",
        ref=lambda s: slot("web", "The web portfolio view", "Web: portfolio", s)),
  ]),
  results=dict(h2="What it adds up to", figures=[("1", "screen from fund to first SIP"), ("2", "platforms, web and mobile, from one design system"), ("todo", "SIPs started, time to first SIP, or monthly active investors")],
   owned="The product design at Rillusion: fund discovery, the fund card and the SIP flow, on web and mobile.",
   source="No public figures were found for MF Street in October 2026; the two figures above describe the design itself.")),

 # ---------------------------------------------------------------- GodoFX
 dict(slug="godofx", name="GodoFX", accent="#f0581c", accent_ink=INK, poster="p1",
  poster_alt="Key visual: green and red candlestick-chart candles built from sticky notes",
  title="GodoFX, a case study by Ashfaq Imran",
  desc="How Ashfaq Imran designed the GodoFX forex trading site at Rillusion: live prices and trust on one screen for a broker launched in June 2021.",
  hero=dict(sentence="A forex broker's site where live prices and the reasons to trust it share one screen.",
   facts=[("Studio", "Rillusion"), ("Launched", "June 2021, managed from Dubai"), ("Platforms", "MT4, ZuluTrade and RoboX")]),
  problem=dict(h2="Prices on one page, trust on another.",
   beats=[("Users", "A new trader wanted to see the spread and the licence in the same glance, and could not."),
          ("Business", "Three platforms and a long sign-up meant most visitors never opened an account."),
          ("Why it mattered", "For a broker, the first screen is the first trade.")],
   ref=lambda s: slot("web", "The broker's homepage before the redesign", "Before: the homepage", s)),
  process=dict(h2="Show the price and the licence together", lead="What we learned, what we tried, and the direction we kept.",
   slip=[("Researched", [row("Broker sites compared", "add the number", todo=True), row("Sign-up steps mapped", "add the number", todo=True)]),
         ("Explored", [row("A marketing page with a login", "dropped", off=True), row("Platform choice before anything", "dropped", off=True), row("Live markets and trust on one screen", "kept")])],
   end=("Live prices, licence and one button", "the direction"),
   ref=lambda s: slot("web", "Wireframes of the homepage with the live ticker", "During: wireframes", s)),
  solution=dict(h2="Every screen answers the problem", items=[
   dict(name="Live markets on the first screen", line="Three pairs, their change, buy and sell. Answers: prices hidden behind a login.",
        ref=lambda s: ui("web", UI["godofx"], "The markets panel, as built", s)),
   dict(name="The licence next to the price", line="Regulator, licence number and the managing office, in the same view. Answers: trust on another page.",
        ref=lambda s: slot("web", "The trust strip with regulator and licence", "The trust strip", s)),
   dict(name="Open an account in three steps", line="Details, verification, deposit. Answers: the long sign-up.",
        ref=lambda s: slot("phone", "The account opening flow", "Account opening", s)),
   dict(name="Choose a platform after funding", line="MT4, ZuluTrade or RoboX, explained once the account exists. Answers: three platforms before the first screen.",
        ref=lambda s: slot("web", "The platform chooser", "Platform chooser", s)),
  ]),
  results=dict(h2="What it adds up to", figures=[("2021", "the site went live in June, from Dubai, licensed in Mauritius"), ("3", "trading platforms behind one sign-up"), ("2024", "the broker rebranded to GODO Capital Markets"), ("todo", "accounts opened, sign-up completion, or deposits in the first month")],
   owned="The site's product design at Rillusion: the homepage, the markets panel, trust and the account flow.",
   source="Public sources, October 2026: GodoFX launch coverage (June 2021, Dubai management, Mauritius FSC licence, MT4, ZuluTrade, RoboX) and the March 2024 rebrand to GODO Capital Markets.")),

 # ---------------------------------------------------------------- HealthPractice
 dict(slug="healthpractice", name="HealthPractice", accent="#d7172f", accent_ink="#ffffff", poster="p2", display="clamp(52px, 7vw, 112px)", display_m="clamp(44px, 12.4vw, 100px)",
  poster_alt="Key visual: a stethoscope built from red and cream sticky notes",
  title="HealthPractice, a case study by Ashfaq Imran",
  desc="How Ashfaq Imran designed HealthPractice from zero at Sysvine: a clinic platform now used by 13,400+ practitioners in 84+ countries.",
  hero=dict(sentence="From zero to a clinic platform used by 13,400 practitioners, on web, iOS and Android.",
   facts=[("Company", "Sysvine Technologies"), ("Scope", "Design system, architecture, flows"), ("Reach", "84+ countries, 41+ specialties")]),
  problem=dict(h2="A clinic runs on a diary and a phone.",
   beats=[("Users", "Doctors booked by phone, kept notes on paper and chased payments by hand."),
          ("Business", "Every practice wanted its own fields, so every build was bespoke and slow."),
          ("Why it mattered", "One core with modules per specialty could serve thousands of practices at once.")],
   ref=lambda s: slot("web", "The paper diary or spreadsheet a practice used before", "Before: the diary", s)),
  process=dict(h2="A core, then a module per specialty", lead="What we learned, what we tried, and the direction we kept.",
   slip=[("Researched", [row("Practices visited", "add the number", todo=True), row("Specialties mapped", "41+")]),
         ("Explored", [row("One product per specialty", "dropped", off=True), row("A generic records system", "dropped", off=True), row("A core with specialty modules", "kept")])],
   end=("One core, modules per specialty", "the direction"),
   ref=lambda s: slot("web", "The module model: a whiteboard, flow or early wireframe", "During: the module model", s)),
  solution=dict(h2="Every screen answers the problem", items=[
   dict(name="Today's appointments first", line="The screen a doctor opens at eight shows the day, not a menu. Answers: the phone and the diary.",
        ref=lambda s: ui("web", UI["healthpractice"], "The day view, as built", s)),
   dict(name="One record per patient", line="Notes, prescriptions and bills on one timeline. Answers: paper notes.",
        ref=lambda s: slot("web", "A patient record with its timeline", "The patient record", s)),
   dict(name="A module per specialty", line="A dentist and a physiotherapist see different fields on the same core. Answers: every build bespoke.",
        ref=lambda s: slot("web", "Specialty settings or a specialty-specific form", "Specialty modules", s)),
   dict(name="The same system in a pocket", line="iOS and Android apps for the day's list and the next patient. Answers: a desk-bound system.",
        ref=lambda s: slot("phone", "The mobile app: today's appointments", "Mobile: today", s)),
  ]),
  results=dict(h2="What it adds up to", figures=[("13,400+", "practitioners use the platform"), ("8,500+", "practices"), ("84+", "countries, across 41+ specialties"), ("3", "platforms: web, iOS and Android, plus the Google Workspace Marketplace")],
   owned="Product design from zero at Sysvine: the design system, the information architecture and the core flows.",
   source="Public source, October 2026: healthpractice.care (13,400+ practitioners, 8,500+ practices, 84+ countries, 41+ specialties, web, iOS, Android, Google Workspace Marketplace). Figures are the vendor's own.")),

 # ---------------------------------------------------------------- TBIL
 dict(slug="tbil", name="TBIL", accent="#120d05", accent_ink=PAPER, poster="p3",
  poster_alt="Key visual: a glowing umbrella built from yellow sticky notes on black",
  title="TBIL, a case study by Ashfaq Imran",
  desc="How Ashfaq Imran designed TBIL at Sysvine: a US insurance coverage finder that tells a patient what their plan covers before the treatment.",
  hero=dict(sentence="A coverage finder that tells a US patient what their plan pays, before the treatment happens.",
   facts=[("Company", "Sysvine Technologies"), ("Client", "A US insurance client, under NDA"), ("Scope", "Coverage check, plan compare, claim")]),
  problem=dict(h2="The bill arrives after the treatment.",
   beats=[("Users", "Patients found out what their plan covered when the invoice came."),
          ("Business", "Every surprise bill became a support call and a disputed claim."),
          ("Why it mattered", "Answer the coverage question first and the claim is already half done.")],
   ref=lambda s: slot("web", "A plan document or explanation of benefits as patients saw it", "Before: the plan document", s)),
  process=dict(h2="Ask the treatment, not the plan", lead="What we learned, what we tried, and the direction we kept.",
   slip=[("Researched", [row("Patients and agents interviewed", "add the number", todo=True), row("Plan types mapped", "add the number", todo=True)]),
         ("Explored", [row("A searchable plan document", "dropped", off=True), row("A chatbot over the policy", "dropped", off=True), row("Start from the treatment, answer in a percentage", "kept")])],
   end=("Treatment in, coverage out", "the direction"),
   ref=lambda s: slot("web", "Early flow of the treatment-first question", "During: the flow", s)),
  solution=dict(h2="Every screen answers the problem", items=[
   dict(name="Treatment in, coverage out", line="Name the treatment, see the percentage covered after the deductible. Answers: the bill that arrives after.",
        ref=lambda s: ui("phone", UI["tbil"], "The coverage check, as built", s)),
   dict(name="Compare two plans on one treatment", line="The same question asked of both plans, side by side. Answers: choosing a plan blind.",
        ref=lambda s: slot("web", "The plan compare view", "Plan compare", s)),
   dict(name="A claim that is already filled", line="The coverage check becomes the claim, with the numbers carried over. Answers: disputed claims.",
        ref=lambda s: slot("phone", "The claim screen", "The claim", s)),
  ]),
  results=dict(h2="What it adds up to", figures=[("1", "question, the treatment, instead of a plan document"), ("todo", "coverage checks run, support calls down, or claims disputed less")],
   owned="The product design at Sysvine: the coverage flow, plan compare and the claim, under NDA.",
   source="The client is under NDA; no public figures were sought.")),

 # ---------------------------------------------------------------- Hoffmann Group
 dict(slug="hoffmann-group", name="Hoffmann Group", accent="#f6c514", accent_ink=INK, poster="p4", display="clamp(52px, 7vw, 112px)", display_m="clamp(44px, 12.4vw, 100px)",
  poster_alt="Key visual: a torque wrench built from yellow sticky notes",
  title="Hoffmann Group, a case study by Ashfaq Imran",
  desc="How Ashfaq Imran designed for the Hoffmann Group catalogue at Sysvine: 500,000 industrial tools, dense German enterprise data made precise.",
  hero=dict(sentence="An industrial catalogue of 500,000 tools where a buyer finds the right one in three taps.",
   facts=[("Company", "Sysvine Technologies"), ("Client", "Hoffmann Group, Munich"), ("Catalogue", "500,000+ products, 500+ brands")]),
  problem=dict(h2="Half a million tools, one search box.",
   beats=[("Users", "A buyer with the part number wanted it in seconds; one without wanted to be guided."),
          ("Business", "Each failed search became an order placed by phone, or placed elsewhere."),
          ("Why it mattered", "In a catalogue this size, search is the shop.")],
   ref=lambda s: slot("web", "The catalogue search before the redesign", "Before: search", s)),
  process=dict(h2="Part numbers first, guidance for the rest", lead="What we learned, what we tried, and the direction we kept.",
   slip=[("Researched", [row("Search logs reviewed", "add the period", todo=True), row("Buyers interviewed", "add the number", todo=True)]),
         ("Explored", [row("More filters on the side", "dropped", off=True), row("Categories before search", "dropped", off=True), row("Search that knows part numbers and guides the rest", "kept")])],
   end=("One search, two kinds of buyer", "the direction"),
   ref=lambda s: slot("web", "Wireframes of the search results", "During: wireframes", s)),
  solution=dict(h2="Every screen answers the problem", items=[
   dict(name="A list that reads like a spec sheet", line="Range, stock and delivery in one line per tool. Answers: dense data, made precise.",
        ref=lambda s: ui("web", UI["hoffmann-group"], "The results list, as built", s)),
   dict(name="Compare without leaving", line="Two tools side by side on the same page. Answers: the buyer who is not sure.",
        ref=lambda s: slot("web", "The compare view", "Compare", s)),
   dict(name="Reorder from history", line="Last month's order, one tap to repeat. Answers: orders placed by phone.",
        ref=lambda s: slot("phone", "Order history on mobile", "Reorder", s)),
  ]),
  results=dict(h2="What it adds up to", figures=[("500,000+", "products in the catalogue, from 500+ brands"), ("32", "countries served by the shop, in 18+ languages"), ("todo", "search success rate, orders per session, or support calls down")],
   owned="The product design at Sysvine: search, results, compare and reorder for the catalogue.",
   source="Public sources, October 2026: hoffmann-group.com (500,000+ products, 500+ brands, 135,000+ customers, 50+ countries); the shop's own figures of 32 countries and 18+ languages. Sysvine's involvement is not public.")),

 # ---------------------------------------------------------------- Dashboards
 dict(slug="dashboards", name="Dashboards", accent="#d7172f", accent_ink="#ffffff", poster="p6",
  poster_alt="Key visual: a performance gauge built from red and cream sticky notes",
  title="Dashboards, a case study by Ashfaq Imran",
  desc="How Ashfaq Imran designed myAIcademy's operations and learning-analytics dashboards: one number, one chart, one sentence, prototyped in code on live data.",
  hero=dict(sentence="Dashboards that end in one sentence: what moved, why, and what to do on Monday.",
   facts=[("Company", "myAIcademy"), ("Built with", "Claude Code, on live data"), ("Views", "Operations, learning analytics, admin")]),
  problem=dict(h2="Six tabs to answer one question.",
   beats=[("Users", "Ops opened a spreadsheet, two panels and a chat thread to learn whether last week went well."),
          ("Business", "Enterprise buyers ask for a live progress dashboard on the first call. The answer was a spreadsheet."),
          ("Why it mattered", "A dashboard that points at one action is opened every morning.")],
   ref=lambda s: slot("web", "The spreadsheet or admin panel used before", "Before: the spreadsheet", s)),
  process=dict(h2="The Monday question", lead="What we learned, what we tried, and the direction we kept.",
   slip=[("Researched", [row("Questions ops asked each week", "3"), row("Weeks of questions logged", "add the number", todo=True)]),
         ("Explored", [row("A BI tool with every metric", "dropped", off=True), row("A static Figma dashboard", "dropped", off=True), row("A coded prototype on live data", "kept")])],
   end=("One number, a chart, a sentence", "the direction"),
   ref=lambda s: slot("web", "The first coded prototype running on live data", "During: first prototype", s)),
  solution=dict(h2="Every screen answers the problem", items=[
   dict(name="One number, then the chart", line="On-time rate, fourteen days, and the sentence that explains the dip. Answers: are we on time, where did it slip.",
        ref=lambda s: ui("web", UI["dashboards"], "The operations view, as built", s)),
   dict(name="Highlight the exception", line="The two low bars in red; everything else grey. Answers: six tabs of everything.",
        ref=lambda s: slot("web", "The learner progress view", "Learner progress", s)),
   dict(name="The admin view buyers see", line="The product's own components, so the demo is the thing shipped. Answers: the deal waiting on a spreadsheet.",
        ref=lambda s: slot("web", "The admin report", "Admin report", s)),
  ]),
  results=dict(h2="What it adds up to", figures=[("1", "pattern found on live data before the first review: the Monday dip"), ("3", "views: operations, learning analytics, admin"), ("todo", "report time down, dashboard opens per week, or demos that used the admin view")],
   owned="The dashboards end to end at myAIcademy: the questions, the views, the chart grammar and the coded prototypes.",
   source="Public source, October 2026: myaicademy.com lists live progress dashboards for admins in the enterprise offer.")),

 # ---------------------------------------------------------------- Lesson pipeline
 dict(slug="lesson-pipeline", name="Lesson pipeline", accent="#120d05", accent_ink=PAPER, poster="p7", display="clamp(52px, 7vw, 112px)", display_m="clamp(44px, 12.4vw, 100px)",
  poster_alt="Key visual: workflow nodes built from yellow sticky notes, joined by amber cables",
  title="Lesson pipeline, a case study by Ashfaq Imran",
  desc="How Ashfaq Imran designed myAIcademy's lesson pipeline: from a Notion brief to a published, voiced lesson in one automated run.",
  hero=dict(sentence="From a Notion brief to a published, voiced lesson in one run, with one human gate.",
   facts=[("Company", "myAIcademy"), ("Stack", "n8n, Claude, NotebookLM, ElevenLabs"), ("Keeps", "paths refreshed within 72 hours")]),
  problem=dict(h2="The lessons fell behind the tools.",
   beats=[("Users", "Learners followed a lesson recorded against last month's screens, and the button was not there."),
          ("Business", "Forty tools, each changing monthly, made the content team the bottleneck."),
          ("Why it mattered", "The 72-hour refresh is the product's edge. It had to be a process, not a sprint.")],
   ref=lambda s: slot("web", "A lesson showing an outdated interface", "Before: a stale lesson", s)),
  process=dict(h2="Automate the waiting, keep the judgement", lead="What we learned, what we tried, and the direction we kept.",
   slip=[("Researched", [row("A lesson followed from brief to publish", "1"), row("Hours per step by hand", "add the hours", todo=True)]),
         ("Explored", [row("Hire more writers", "dropped", off=True), row("A template with AI drafting", "dropped", off=True), row("A full pipeline with one human gate", "kept")])],
   end=("Every wait becomes a node; one gate stays human", "the direction"),
   ref=lambda s: slot("wide", "The n8n workflow canvas", "During: the canvas", s)),
  solution=dict(h2="Every step answers the problem", items=[
   dict(name="The run you can watch", line="Each step with its status, and a button to open the output. Answers: trusting an automation you cannot see.",
        ref=lambda s: ui("web", UI["lesson-pipeline"], "The run view, as built", s)),
   dict(name="Draft, then fact-check", line="Claude writes, NotebookLM checks against the tool's own docs. Answers: lessons that describe buttons that moved.",
        ref=lambda s: slot("web", "The fact-check step showing a disagreement", "The fact-check", s)),
   dict(name="A human before the voice", line="One approval, placed before ElevenLabs, so nothing is voiced twice. Answers: the cost of a wrong lesson.",
        ref=lambda s: slot("web", "The review gate", "The review gate", s)),
   dict(name="The lesson, published", line="Text, voice and checkpoints in the app, hands off. Answers: the content team as the bottleneck.",
        ref=lambda s: slot("phone", "A published lesson in the app", "The output", s)),
  ]),
  results=dict(h2="What it adds up to", figures=[("72h", "the refresh promise the product makes, kept by this pipeline"), ("40+", "tools covered without a content sprint"), ("1", "human gate, placed where judgement is needed"), ("todo", "lessons per week, hours per lesson before and after, or voice cost saved")],
   owned="The pipeline as a product at myAIcademy: the workflow, the human gate and the run interface.",
   source="Public sources, October 2026: myaicademy.com (refreshed every 72 hours, 40+ tools) and the Product Hunt launch post.")),

 # ---------------------------------------------------------------- This portfolio
 dict(slug="this-portfolio", name="This portfolio", accent="#2a63ee", accent_ink="#ffffff", poster="p8", display="clamp(52px, 7vw, 112px)", display_m="clamp(44px, 12.4vw, 100px)",
  poster_alt="Key visual: a laptop built from blue and white sticky notes on royal blue",
  title="This portfolio, a case study by Ashfaq Imran",
  desc="How Ashfaq Imran designed, rendered, wrote and coded this portfolio with AI: Higgsfield for the visuals, Claude for the copy, Claude Code for the build.",
  hero=dict(sentence="One designer, three AI tools, a portfolio that is its own proof.",
   facts=[("Made with", "Higgsfield, Claude, Claude Code"), ("Stack", "HTML, CSS, JavaScript, GSAP"), ("Checked on", "12 screen sizes")]),
  problem=dict(h2="A hundred portfolios of screenshots.",
   beats=[("Readers", "A grid of shots answers “can you make it pretty” and nothing else."),
          ("Me", "Every conversation started by explaining the AI workflow in words."),
          ("Why it mattered", "If the site is built the way I claim to work, the site is the case study.")],
   ref=lambda s: slot("web", "A typical portfolio grid, or this site's first draft", "Before: a grid", s)),
  process=dict(h2="Build it the way I say I work", lead="What I learned, what I tried, and the direction I kept.",
   slip=[("Researched", [row("What gets read, in what order", "outcome first"), row("Case-study shape", "five parts")]),
         ("Explored", [row("A portfolio template", "dropped", off=True), row("A no-code builder", "dropped", off=True), row("Hand-written code, with Claude Code", "kept")])],
   end=("Render, write and build with AI, in code", "the direction"),
   ref=lambda s: slot("wide", "A Higgsfield render session or a Claude Code transcript", "During: the tools", s)),
  solution=dict(h2="Every choice answers the problem", items=[
   dict(name="One scroll film, not a grid", line="The bust, the career cards, the crowd, then the work. Answers: a hundred grids.",
        ref=lambda s: slot("wide", "The scroll film on the home page", "The scroll film", s)),
   dict(name="A sticky-note world", line="Every key visual in the same material, so nine products read as one body of work. Answers: showing the AI workflow, not describing it.",
        ref=lambda s: img("wide", "../../assets/posters/p5.webp", "A key visual rendered in Higgsfield: a phone built from sticky notes", "A key visual, rendered in Higgsfield", s, 2400, 2979)),
   dict(name="Nine case studies, one shape", line="Hook, problem, process, solution, results. Learn it once, read nine. Answers: how do you think.",
        ref=lambda s: ui("web", UI["this-portfolio"], "The build log, as built", s)),
   dict(name="Twelve screen sizes", line="Phones, short laptops and wide screens each get their own layout. Answers: a recruiter on a phone.",
        ref=lambda s: slot("phone", "The home page on a phone", "Mobile", s)),
  ]),
  results=dict(h2="What it adds up to", figures=[("9", "projects, each a case study in the same five parts"), ("12", "screen sizes checked"), ("1", "designer, with Higgsfield, Claude and Claude Code"), ("todo", "visits, replies, or interviews that started from the site")],
   owned="All of it: the concept, the visuals, the copy, the code and the case studies.",
   source="The site is live and open source on GitHub.")),
]
# ---------------------------------------------------------------- myAIcademy, in full
# Evidence: the Figma file (UI_UX -myAIcademy.fig), the 4K screen recordings of the web onboarding,
# the badge-redesign folder (nine directions and the production spec), the founder's pitch deck.
F, I = "film/", "img/"
def live(name, alt, caption=""):
    return dict(kind="live", src=F + f"clip-{name}.mp4", poster=F + f"end-{name}.jpg", alt=alt, caption=caption)
def still(name, alt, caption=""):
    return dict(kind="img", src=F + f"end-{name}.jpg", alt=alt, caption=caption, w=1600, h=900)

MYAICADEMY = dict(
 slug="myaicademy", name="myAIcademy", accent="#3370ff", accent_ink="#ffffff", hi="#3370ff", poster="p5",
 title="myAIcademy: an AI course that starts with your job | Ashfaq Imran",
 desc="How Ashfaq Imran designed myAIcademy's onboarding, learning path and Aimy, so 26 roles each get a plan about their own work before they make an account.",
 kicker=["Case study", "myAIcademy", "Head of Product Design, 2025 to now"],
 h1="myAIcademy: an AI course that starts with *your job*, not the tool",
 split=("my", "AIcademy"), tagline="An AI course that starts with your job, not the tool.", brief_h2="The question behind it",
 close_img=F + "end-dashboard.jpg", close_alt="Meera's own path, waiting after sign-up",
 dek="How I designed onboarding, the learning path and Aimy so that 26 different roles each get a plan about their own work before they've even made an account.",
 facts=[("My role", "Head of Product Design"), ("Timeline", "2025 to now"), ("Platforms", "Web, iOS and Android"), ("Launch", "#2 Product of the Day, Product Hunt, September 2026")],
 teaser=dict(kind="loop", src=F + "clip-dashboard.mp4", poster=F + "end-dashboard.jpg", alt="A screen recording of a learner's path in the myAIcademy web app",
             caption="Where onboarding ends: the learner's own path, with the tools for their role. A real recording of the web app."),
 hook=["“How does my team use this in its actual work?”",
       "That was the question asked in every room the founder taught. ~Companies had bought the licences and their people had done the courses, and on Monday nothing about the work had changed."],
 intro=dict(
  summary="myAIcademy is an AI-fluency app for working professionals, on web, iOS and Android. I lead product design and own it end to end: onboarding, the learning path, lessons, Aimy the learning agent, and the brand.",
  challenge="Make a course that 26 different roles each recognise as being about their own job, and keep it current when the tools change every week.",
  outcome="It launched on Product Hunt in September 2026 and finished #2 Product of the Day. The site reports more than 20,000 leaders on the platform."),
 problem=dict(
  h2="Licences bought. Work unchanged.",
  figure=("80%", "of organisations that bought AI for everyone still report **no material earnings impact**. McKinsey, 2025, as quoted in the founder's pitch."),
  paras=[
         "The training that came with the licences teaches the tool: what ChatGPT can do, how to write a prompt. ~It doesn't teach a finance lead to close the month faster, or a designer to brief Midjourney for a real campaign.",
         "~So people finish the course, go back to their desk and work the old way. For myAIcademy that means a learner who doesn't come back, and a company that doesn't renew."],
  context=[("Product", "myAIcademy, an AI-fluency app for working professionals"),
           ("Duration", "2025 to now, still running"),
           ("Scope", "A real, shipped product: onboarding, the learning path, lessons, Aimy, the brand"),
           ("My role", "Head of Product Design, owning the product design end to end"),
           ("Constraints", "AI tools change every week, so a path must refresh within 72 hours of a major change. Learners give it 10 to 60 minutes a day."),
           ("Team", "?Who you worked with | the founder, engineers, the content team, and how many")],
  evidence=[dict(kind="img", frame="paper", src=I + "slide-problem.webp", alt="Pitch slide: organisations bought AI for everyone, and more than 80% still see no earnings impact", w=2000, h=1124,
                 caption="The founder's pitch: more than 80% of organisations see no earnings impact from AI."),
            dict(kind="img", frame="paper", src=I + "slide-question.webp", alt="Pitch slide: “How does my team use this in its actual work?”, the question asked in every room the founder taught", w=2000, h=1124,
                 caption="The question the whole product is built around.")]),
 journey=dict(
  h2="Meera's first five minutes",
  note="a real recording of the web app",
  lead="~Meera is a creative professional who has tried AI tools but never used them on real work. The screen holds still while her answers pass beside it; each recording of the live onboarding plays once, then the numbers mark what I designed and why.",
  steps=[
   dict(title="She chooses how to start", thought="~Meera knows her job well and AI barely. A quiz would feel like an exam, so she picks *Tell me your role*.",
        media=live("begin", "The onboarding screen asking how you would like to begin, with two choice cards"),
        notes=[("Two ways in", "Tell me your role, or answer a few questions. The first screen asks how, not who.", 38, 56),
               ("A line of reassurance", "*Two ways in. Both end with a plan made for you.*", 50, 42),
               ("One place for Continue", "~The button sits in the same spot on every step, so the thumb learns where it is.", 50, 85)]),
   dict(title="She finds herself in the list", thought="Twenty-six roles, all one tap away, with a search field above them. ~Meera taps *Creative Professional* without scrolling.",
        media=live("role", "The role screen with 26 roles shown as chips"),
        notes=[("The steps left", "Four segments at the top count down the questions.", 50, 12),
               ("Search above the list", "For anyone whose title isn't a chip.", 50, 38),
               ("Every role is a chip", "No dropdown to open: 26 roles, from Teacher to Forward Deployed Engineer.", 62, 60),
               ("Just Exploring", "~A way in for someone who isn't working yet, or would rather not say.", 41, 77)]),
   dict(title="She marks now and goal on each skill", thought="~She has tried Midjourney but never written copy with AI. She drags *Now* and *Goal* separately on each skill.",
        media=live("skills", "The skill map with a Now and a Goal handle on four skills"),
        notes=[("Skills for her role", "Generative Visuals, AI Copywriting, Creative Ideation and AI Design Tools.", 23, 32),
               ("Now", "Where she is today, on a five-step scale.", 35, 38),
               ("Goal", "Where she wants to get to. The blue gap is what the path will teach.", 80, 38)]),
   dict(title="She says how much time she has", thought="~One step earlier she said afternoons suit her. Now she picks sixty minutes a day; the card calls it *Committed*, not *Hard*.",
        media=live("pace", "The learning pace screen with four cards from 10 to 60 minutes a day"),
        notes=[("Her answer, echoed", "The field above repeats her choice, and takes a typed answer too.", 50, 49),
               ("Four paces, named kindly", "*Casual Pace*, *Steady Learner*, *Balanced*, *Committed*.", 32, 62),
               ("The same choice card", "Illustration top right, title, one line, blue when picked.", 68, 62)]),
   dict(title="She sees how it fits into a month", thought="~This is when the plan stops being abstract: three stages over 30 days, each named after her kind of work.",
        media=live("journey", "The 30-day journey screen with three stages along a curved path"),
        notes=[("Days 1 to 7", "*AI Creative Kickstart*: quick visuals and text for projects.", 26, 44),
               ("Days 8 to 15", "*Integrated Creative Workflow*.", 49, 31),
               ("Days 16 to 30", "*End-to-End AI Creativity*.", 64, 12),
               ("Why it's worth it", "*Small steps that fit around the work you already do.*", 50, 80)]),
   dict(title="Only now does she make an account", thought="~She has seen her path, her tools and her month. An email address now feels like a fair trade.",
        media=live("signup", "The account screen: Individual or Partner, three fields, Google and Apple sign-in"),
        notes=[("Last step, said plainly", "*Last step! Set up your account and your learning begins.*", 50, 29),
               ("Individual or Partner", "Teams and partners sign up on the same screen.", 50, 39),
               ("Google or Apple", "One tap for anyone who would rather not type.", 50, 84)]),
   dict(title="Her path is waiting", thought="~The first thing she sees is her own path: a section on her tools, lessons named after outcomes, and a streak to keep.",
        media=live("dashboard", "The learner's path in the web app, with tool progress and numbered lessons"),
        notes=[("Path, Discover, Live, Signal", "Four places in one bar.", 27, 13),
               ("Coins and a streak", "Rewards sit top right, in amber, away from anything you have to do.", 79, 13),
               ("Tools with progress", "Each tool in the section shows how far she has got.", 49, 38),
               ("Lessons named after outcomes", "*Turn market research into cited answers with NotebookLM.*", 30, 51)]),
  ]),
 decisions=dict(
  h2="Four decisions",
  lead="Each started as a choice between options that all looked reasonable. Here is what I weighed and what it cost.",
  items=[
   dict(short="Two ways to begin", h3="Ask how to begin, not who you are",
        title="Why the first question is *how* you'd like to begin, not *who* you are",
        hook="~Some people arrive knowing their job and nothing about AI. Others can't name the skills they want. One onboarding couldn't serve both.",
        before=dict(text="?What onboarding looked like before | the first version of this flow, or the pattern you started from, such as one long questionnaire",
                    media=dict(kind="slot", what="The earlier onboarding, before the two ways in")),
        options=[("Option A", "One questionnaire for everyone", "~Thorough, but slow for someone who already knows their role, and every extra question loses people.", False),
                 ("Option B", "Role only", "~Fast, but a role says little about what you already know or want to reach.", False),
                 ("Chosen", "Two ways in, both ending with a plan", "*Tell me your role* reads the job and maps the skills; *Answer a few questions* walks through it step by step.", True)],
        why="~I let people choose their own speed into the product. The cost was designing and maintaining two routes, and the risk was people worrying they had picked the wrong one. That's what the line under the question is for: *Two ways in. Both end with a plan made for you.*",
        actions=["Two large choice cards, each with its own illustration, so the choice reads at a glance",
                 "One line of reassurance under the question, so neither route feels like the wrong one",
                 "~The role route goes straight to the role list; the question route adds goal, skill map, time and pace"],
        after=still("begin", "The final onboarding screen with the two ways in", "As shipped."),
        result="?What happened | onboarding completion by route, or what people said in testing. If you have no number, describe what you observed."),
   dict(short="Now and goal, per skill", h3="Two points on every skill, not one level",
        title="Why the skill map asks for two points on every skill, not one level overall",
        hook="~“Beginner” is true of most people for some AI skills and false for others. One level would have sent a designer who already uses Midjourney back to lesson one.",
        before=dict(text="~The usual pattern is a single question: are you a beginner, intermediate or advanced? It is quick, and it is wrong for anyone whose skills are uneven."),
        options=[("Option A", "One overall level", "~Quick to answer, but it flattens uneven skills into one number.", False),
                 ("Option B", "Current level per skill", "~Accurate today, but it says nothing about how far the learner wants to go.", False),
                 ("Chosen", "Now and goal on every skill", "Two handles per slider: where you are and where you want to be. The gap becomes the path.", True)],
        why="~The gap between the two handles is what the path is built from, so the plan skips what you already know and stops where you want to stop. The trade-off is effort: four sliders ask more of you than one tap, so the list is cut to the four skills that matter for the role picked one step earlier.",
        actions=["Four skills, chosen from the role picked on the step before",
                 "A five-step scale on each: Beginner, Novice, Intermediate, Advanced, Expert",
                 "Two labelled handles, *Now* and *Goal*, with the gap filled in brand blue"],
        after=still("skills", "The skill map as shipped, with Now and Goal handles", "As shipped."),
        result="?What happened | did people understand the two handles first time? Note anything from testing or support."),
   dict(short="Sign-up comes last", h3="The account comes last",
        title="Why the account form is the last step of onboarding, not the first",
        hook="~Asking for an email before showing anything asks for trust the product hasn't earned yet.",
        before=dict(text="?The order before | if sign-up used to come first, show that version and where people dropped off",
                    media=dict(kind="slot", what="The earlier order, with sign-up first")),
        options=[("Option A", "Sign up first", "~The usual pattern, and answers are saved straight away, but people leave before they see what they'd get.", False),
                 ("Option B", "No account, browse freely", "~No friction, but the plan can't be saved or followed up.", False),
                 ("Chosen", "Plan first, then the account", "The questions, then *Your path is ready!*, the tools and the 30-day journey. Only then *You're almost there*.", True)],
        why="~By the time the form appears, the learner has already seen their own path, so the form reads as the way to keep it. Its headline says what it unlocks: *Last step! Set up your account and your learning begins.*",
        actions=["*Your path is ready!* and *Discover what you'll learn* come before any form",
                 "The 30-day journey shows Days 1 to 7, 8 to 15 and 16 to 30, named for the learner's role",
                 "The form itself: Individual or Partner, three fields, Google and Apple sign-in"],
        after=still("signup", "The account screen as shipped", "As shipped: the last step, not the first."),
        result="?What happened | sign-up rate after the change, or what you saw in testing"),
   dict(short="Aimy works inside the tool", h3="Aimy works inside the real tool",
        title="Why Aimy guides you inside the tool you're using, instead of answering beside the lesson",
        hook="The positioning slide says it plainly: others teach the tool; myAIcademy proves the work got done. ~A chat window beside a lesson is still a classroom.",
        before=dict(text="Course platforms like Coursera and Udemy teach broadly. Vendor academies teach one tool. WalkMe and Whatfix guide clicks without teaching anything.",
                    media=dict(kind="img", frame="paper", src=I + "slide-position.webp", alt="Pitch slide comparing course platforms, vendor academies, digital adoption tools and myAIcademy", w=2000, h=1124)),
        options=[("Option A", "A chatbot inside the lessons", "~Familiar, but the learner still has to carry the answer across to the real tool.", False),
                 ("Option B", "Click-by-click overlays", "~Gets the task done, but nobody learns why, so they need the overlay next time too.", False),
                 ("Chosen", "An agent that works inside the real tool", "Tell Aimy your goal; she turns it into a workflow and guides you inside the tool, with the exact prompts, actions and settings.", True)],
        why="~Aimy keeps both outcomes in view: the task gets finished, and each step says why, so next time you need her less. *Let Aimy finish the rest* is there for the day when shipping matters more than learning.",
        actions=["Steps counted as *Step 2 of 6*, with a progress line, in a panel docked beside the tool",
                 "A *Copy* button on the exact text to paste, so nothing gets retyped",
                 "A *Learn* switch and *Change goal*, so the learner decides how much teaching they want",
                 "*Let Aimy finish the rest*, for when the task matters more than the lesson"],
        after=dict(kind="img", frame="none", src=I + "aimy-panel.webp", alt="Aimy open as a panel beside a tool, on step 2 of 6", w=1400, h=824, caption="As shipped: Aimy, step 2 of 6, inside the tool."),
        result="Aimy got its own slide in the Product Hunt launch. ?Usage | how many learners open Aimy, or what they said about it"),
  ]),
 iterations=dict(
  h2="Nine badges, one shipped",
  lead="The Speed Learner badge appears when someone finishes three lessons inside 24 hours. I built every direction as a live, animated screen and judged them side by side, three rounds in all.",
  rounds=[
   dict(label="Round 1", name="Three different ideas", note="Each one a different reason to care about a badge.",
        items=[(I + "badge-options-0.jpg", "A · Quiet", "Centred and spare, one white call to action, stats in a single line.", True),
               (I + "badge-options-1.jpg", "B · Collectible", "The badge as a card you own, tilting under the cursor. ~Fun once, but it turned a moment into a toy.", False),
               (I + "badge-options-2.jpg", "C · Editorial", "Split layout with a 24-hour timeline. ~The most to read on a screen people want to leave.", False)]),
   dict(label="Round 2", name="Centred, Inter Regular, brand blue", note="Quiet, taken three ways.",
        items=[(I + "badge-centered-0.jpg", "1 · Pure", "Badge, name, one line and a single Continue, like the streak screen.", True),
               (I + "badge-centered-1.jpg", "2 · Stats", "Three quiet numbers and the button pair from the lesson-complete screen. ~Numbers nobody asked for.", False),
               (I + "badge-centered-2.jpg", "3 · Timeline", "One line showing the three lessons across 24 hours. ~Clever, but it needed explaining.", False)]),
   dict(label="Round 3", name="Down to the minimum", note="Pure, against two last challengers.",
        items=[(I + "badge-minimal-0.jpg", "1 · Pure", "Only the badge, the name, one line and one button.", True),
               (I + "badge-minimal-1.jpg", "2 · Side by side", "Badge beside left-aligned text on web, so it reads like a statement. ~It broke on the phone.", False),
               (I + "badge-minimal-2.jpg", "3 · Timeline", "Pure plus a single line of the three lessons. ~Still one idea too many.", False)])],
  final=dict(media=dict(kind="img", frame="plain", src=I + "badge-final.jpg", alt="The shipped Speed Learner badge: Great Job! You earned the badge Epic, progress to the next badge, Continue", w=1366, h=768),
             title="The plainest one, plus a reason to keep going",
             text=["The shipped screen is one centred component for phone and web: the badge, three short lines and a button. Inter Regular only, brand #3370FF, the title at 24px.",
                   "~It kept Pure's restraint and swapped the stats for the one number that matters next: how many lessons until the next badge. It matches the streak and lesson-complete screens, so a reward never feels like a different app."])),
 system=dict(
  h2="One blue, one typeface",
  lead="Counted from the Figma file across the web app and the dark mobile theme, not chosen for this page.",
  type=dict(family="Inter", rows=[(40, 500, "Your path is ready!"), (28, 400, "How this fits into real life"), (24, 400, "Speed Learner"),
                                  (20, 500, "Tell me your role"), (16, 400, "Two ways in. Both end with a plan made for you."),
                                  (14, 400, "Walk through it together, step by step"), (12, 500, "CHOOSE YOUR PATH")],
            why="Inter Regular is used about 11,500 times in the file, Medium 4,900, Light and Semi Bold under 900 each, and the badge spec says *Inter Regular only*. Most text sits at 12 to 16px, ~so legibility at small sizes mattered more than personality."),
  colours=dict(swatches=[("Brand blue", "#3370FF"), ("Deep blue", "#004CFF"), ("Blue 400", "#5B8CFF"), ("Blue 300", "#6E99FF"), ("Blue 100", "#ACC4FF"),
                         ("Black", "#000000"), ("Surface", "#161618"), ("Surface 2", "#1E1E1E"), ("Grey", "#757575"), ("Grey 300", "#ACACAC"),
                         ("Coins", "#FEA02C"), ("Streak", "#FECD3E")],
               why="One blue does every job that matters: the selected card, the slider fill, the main button, the progress bar. Amber and yellow are kept for rewards, coins and streaks, ~so they never compete with an action."),
  radii=dict(values=[4, 8, 10, 16, 999], why="4 and 8 for inputs and small controls, 16 for cards, a full pill for chips and switches. These five cover almost every corner in the file."),
  components=dict(title="The parts, cut from the shipped screens", n=3, items=[
     (F + "part-choice.jpg", "Choice card, selected"), (F + "part-chips.jpg", "Role chips"), (F + "part-slider.jpg", "Two-handle slider"),
     (F + "part-pace.jpg", "The same choice card, four times"), (F + "part-form.jpg", "Segmented control and fields"), (F + "part-journey.jpg", "The 30-day path")],
   why="The same choice card carries four steps (how to begin, why, when and how much): illustration top right, a title, one line, blue when picked. Learn it once and every step after it reads the same.")),
 ai=dict(
  h2="What AI did, what I decided",
  lead="?How AI fitted into this project | the tools you used and for which tasks, in a sentence",
  by_ai=["~Built each badge direction as a live, animated screen, so all nine could be compared in motion",
         "~Made first drafts of tool artwork and lesson images for the course cards",
         "?Anything else AI executed | prompts, copy drafts, research summaries"],
  by_me=["~Which of the nine badge directions shipped, and why the plainest one won",
         "~Two ways into onboarding, and the order of the questions",
         "~Sign-up after the plan, not before",
         "~What Aimy may do on its own: it finishes a task only when the learner asks"]),
 reflection=dict(
  h2="What I'd keep, and what I'd change",
  learn=[("?What surprised you in testing | one moment where people did something you didn't expect, and what you changed", ""),
         ("?A decision you'd make differently | now that it has shipped, and why", ""),
         ("?What this project taught you about designing for AI products | something only this project could have taught you", "")],
  future=[("~A light theme for the mobile app", "~It already exists in the Figma file as a full set of screens; the next step is testing it with learners who study during the working day."),
          ("~Signals inside the path", "~Signals already curates AI news. Linking a launch to the lessons it changes would make the 72-hour refresh visible to the learner."),
          ("~A team view for partners", "~The sign-up screen already offers *Partner*. The next step is a view of which roles in a team are progressing, and which are stuck.")]),
 results=dict(figures=[("20,000+", "leaders on the platform, as myaicademy.com states it"), ("#2", "Product of the Day on Product Hunt, September 2026"),
                       ("72h", "to refresh a path after a major tool change"), ("4.3", "rating on Trustpilot")],
              source="Public sources, October 2026: myaicademy.com, the Product Hunt launch page, the App Store and Google Play listings, Trustpilot. Screens: recordings of the live web app and the project's Figma file."),
 close=dict(h2="Want the longer version?", text="With the Figma file open, I'm happy to walk through the decisions, the versions that didn't make it, and what I'd do next."),
 credit="Screens on this page are recordings of the live myAIcademy web app.",
)

# ---------------------------------------------------------------- quiet edition: overview, the thinking lens, the AI workflow
M = MYAICADEMY
M["dek"] = "I led product design end to end: onboarding, the learning path, lessons and Aimy, the learning agent. Twenty-six roles each get a plan about their own work before they make an account."
M["overview"] = dict(
    challenge="Make one AI course that 26 different roles each recognise as being about their own job, and keep it current when tools change every week.",
    approach="Ask about the work, not the tool. The learner's role and skill gaps build the plan, and the account comes last.",
    outcome="Launched September 2026, #2 Product of the Day on Product Hunt, with more than 20,000 leaders on the platform.")
M["thinking"] = dict(
    product="~Ordering onboarding so value comes before commitment, and choosing what Aimy may do alone.",
    content="~Every label and line written so a choice feels safe: *Two ways in. Both end with a plan made for you.*",
    analytical="~A market number to frame the problem, skill gaps instead of levels, nine badge directions judged side by side.",
    ai="~An AI agent designed into the product, and AI tools across research, content, prototyping and automation.")

M["problem"]["lens"] = {
    "analytical": "~Framed with a market number, not an opinion: 80% of organisations see no earnings impact.",
    "product": "~Stated as a business risk, a learner who doesn't return and a company that doesn't renew, not as a missing feature."}
J = M["journey"]["steps"]
J[0]["lens"] = {"product": "~Two routes, so someone who knows their job and someone who knows their gaps both get a fast start.",
                "content": "~One line of reassurance removes the fear of picking the wrong route."}
J[1]["lens"] = {"content": "~Twenty-six roles written the way people describe themselves, not as a taxonomy."}
J[2]["lens"] = {"analytical": "~Two points per skill turn a vague level into a measurable gap, and the gap becomes the plan."}
J[3]["lens"] = {"content": "~Paces named kindly: *Committed*, not *Hard*."}
J[5]["lens"] = {"product": "~Sign-up placed after the value is shown, so the form reads as the way to keep the plan."}
J[6]["lens"] = {"content": "~Lessons named after outcomes, such as *Turn market research into cited answers with NotebookLM*.",
                "ai": "~The path is assembled from the learner's own role, skills and pace."}
D = M["decisions"]["items"]
D[0]["lens"] = {"product": "~Paid for a faster start with a second route to design and maintain.",
                "content": "~The reassurance line does the work a tooltip would otherwise do."}
D[1]["lens"] = {"analytical": "~Replaced one self-reported level with a gap per skill that the path can measure.",
                "product": "~Cut the list to four skills per role, so accuracy didn't cost completion."}
D[2]["lens"] = {"product": "~Moved the ask for trust to the point where the product has earned it."}
D[3]["lens"] = {"ai": "~Designed an agent that works inside the real tool, and decided where its autonomy stops.",
                "product": "~Positioned against course platforms, vendor academies and click-guides at once."}
M["iterations"]["lens"] = {"analytical": "~Nine directions in three rounds, compared side by side in motion rather than as static mock-ups.",
                           "ai": "~Each direction was built as a live, animated screen with AI, so all nine could be judged as they would really feel."}
M["system"]["lens"] = {"analytical": "~The system was counted from the Figma file rather than assumed: Inter Regular appears about 11,500 times."}

M["workflow"] = dict(
    h2="AI across the whole process",
    lead="~Every stage of the project had an AI tool in it. What changed was the speed of trying things; the decisions stayed mine.",
    stages=[
        dict(name="Research", tools=["NotebookLM", "Claude"],
             ai="~Turned the founder's pitch, competitor courses and market reports into one brief I could question.",
             me="~Chose the one question the product answers: *How does my team use this in its actual work?*",
             lens={"ai": "~Research synthesis with NotebookLM and Claude."}),
        dict(name="Content", tools=["Claude", "Notion"],
             ai="~Drafted the role list, skill names and onboarding microcopy in bulk, so there was always something to react to.",
             me="~Edited every line for tone and cut what didn't help a choice: *Committed*, not *Hard*."),
        dict(name="Visuals", tools=["Midjourney", "Higgsfield", "Figma"],
             ai="Made first drafts of tool artwork and lesson images for the course cards.",
             me="~Kept one blue and one typeface, so generated art never set the style."),
        dict(name="Prototype", tools=["Claude Code", "Claude Design", "Lovable"],
             ai="Built each badge direction as a live, animated screen, so all nine could be compared in motion.",
             me="~Picked the plainest of nine, then cut it further."),
        dict(name="Automation", tools=["n8n", "Zapier", "Claude Code"],
             ai="~A lesson pipeline: a brief goes in, and a voiced lesson is live within 72 hours of a major tool change.",
             me="~Decided what the pipeline may publish on its own, and what a person checks first.",
             link=("The lesson pipeline case study", "../lesson-pipeline/index.html")),
        dict(name="Voice and video", tools=["ElevenLabs", "Higgsfield", "After Effects"],
             ai="~Voice-overs for lessons and short scenes for launch films.",
             me="?What you decided here | which voice, what the films had to show, what you cut"),
    ],
    rules_h="Where AI stops",
    rules=["~AI drafts and builds options; I choose which one ships.",
           "~Aimy finishes a task on its own only when the learner asks it to.",
           "~Nothing generated goes live without a person reading it first."],
    kit_h="The toolkit",
    kit=[("Language and research", ["Claude", "NotebookLM", "Notion"]),
         ("Images and video", ["Midjourney", "Higgsfield", "ElevenLabs", "After Effects"]),
         ("Design and build", ["Figma", "Claude Design", "Claude Code", "Lovable", "Replit"]),
         ("Automation", ["n8n", "Zapier", "Claude Cowork"])],
    speed="?How much faster AI made it | one honest comparison, such as nine badge directions in a day rather than a week")

# ---------------------------------------------------------------- the whole role: product owner, roadmap, lesson content
M["kicker"] = ["Case study", "myAIcademy", "Head of Product Design and Product Owner, 2025 to now"]
M["facts"] = [("My role", "Head of Product Design and Product Owner"), ("Timeline", "2025 to now"), ("Platforms", "Web, iOS and Android"), ("Launch", "#2 Product of the Day, Product Hunt, September 2026")]
M["dek"] = "As Head of Product Design and the product owner, I led myAIcademy end to end: the vision and roadmap, every feature shipped and planned, the standard for lesson content, and the design of onboarding, the learning path and Aimy."
M["desc"] = "How Ashfaq Imran, Head of Product Design and product owner, led myAIcademy end to end: vision and roadmap, features, lesson content, onboarding, the learning path and Aimy."
M["intro"]["summary"] = "myAIcademy is an AI-fluency app for working professionals, on web, iOS and Android. As Head of Product Design and product owner I own it end to end: the vision, the quarterly and yearly roadmap, existing and future features, lesson content, and the design of every screen."
M["overview"]["approach"] = "I set the product direction and owned it through to the screens: the roadmap, the features, the lesson standard and the design. The learner's role and skill gaps build the plan, and the account comes last."
M["owned"] = [
    ("Vision and roadmap", "Where the product goes, quarter by quarter and year by year."),
    ("Features", "What exists, what changes, and what comes next, with the trade-offs."),
    ("Lesson content", "What a lesson is: its outcome, its length, its tool, its level."),
    ("Design", "Onboarding, the learning path, Aimy, rewards and the brand, on web and mobile."),
    ("Launch", "The Product Hunt launch in September 2026, #2 Product of the Day."),
]
M["thinking"]["product"] = "~As product owner: the roadmap, the order of features, what onboarding asks first, and what Aimy may do alone."
M["thinking"]["content"] = "~The standard every lesson follows, and every label written so a choice feels safe: *Two ways in. Both end with a plan made for you.*"

M["lessons"] = dict(
    h2="What a lesson should be",
    lead="I owned the lesson content as well as the screens it sits in. Every lesson follows the same standard.",
    rules=[
        dict(title="Named after an outcome, not a feature", text="*Turn market research into cited answers with NotebookLM*, not *Introduction to NotebookLM*.",
             lens={"content": "~A title that names the result tells a learner why to start it."}),
        dict(title="Done in the real tool", text="The learner works in the tool itself, with Aimy beside it giving the exact prompts, actions and settings.",
             lens={"product": "~Learning and doing happen in one place, so the lesson leaves real work behind."}),
        dict(title="Sized for a working day", text="Paces from 10 to 60 minutes a day, so a lesson fits around the work people already do."),
        dict(title="Organised in sections and levels", text="The path is built from sections and three levels, Beginner, Intermediate and Advanced. ~The level comes from the learner's own skill gaps.",
             lens={"analytical": "~Levels come from the gap between *Now* and *Goal* on each skill, not from a single self-rating."}),
        dict(title="Current within 72 hours", text="When a major tool changes, the affected lessons are refreshed within 72 hours.",
             lens={"ai": "~Kept current by an AI lesson pipeline, with a person checking before anything goes live."}),
    ],
    media=dict(kind="img", src=F + "end-dashboard.jpg", alt="A learner's path: sections, levels and lessons named after outcomes, with tool progress", w=1600, h=900,
               caption="A learner's path as shipped: sections, three levels, lessons named after outcomes."))

M["roadmap"] = dict(
    h2="The roadmap",
    lead="As product owner I set where myAIcademy goes next, and in what order. The roadmap runs in quarters for what's next and in years for where it's heading.",
    vision=dict(text="?The product vision | one or two sentences on where myAIcademy is heading in the next two to three years",
                lens={"product": "~One direction that every quarter's plan has to serve."}),
    horizons=[
        dict(key="shipped", name="Shipped", when="2025 to September 2026", items=[
            dict(title="Onboarding with two ways in", text="Role or questions, a skill map, pace, then the account."),
            dict(title="A personal 30-day path", text="Built from the learner's role, skill gaps and time."),
            dict(title="Aimy, the learning agent", text="Guides the learner inside the real tool.",
                 lens={"product": "~The feature that sets the product apart from course platforms and click-guides."}),
            dict(title="Rewards", text="Coins, streaks and badges, kept away from actions."),
            dict(title="Discover, Live and Signal", text="~Browsing, live sessions and AI news beside the path."),
            dict(title="Web, iOS and Android, and the launch", text="#2 Product of the Day on Product Hunt."),
        ]),
        dict(key="next", name="Next", when="?Which quarters | for example Q1 to Q2 2027", items=[
            dict(title="~A team view for partners", text="~Which roles in a team are progressing, and which are stuck. Partners can already sign up.",
                 lens={"product": "~Turns the Partner sign-up that already exists into a reason for companies to renew."}),
            dict(title="~Signals inside the path", text="~Linking a tool launch to the lessons it changes, so the 72-hour refresh is visible."),
            dict(title="~A light theme for the mobile app", text="~Already designed in Figma; next is testing it with daytime learners."),
        ]),
        dict(key="later", name="Later", when="?Which years | for example 2027 to 2028", items=[
            dict(title="?Bigger bets | the features or markets that serve the vision over the next years"),
        ]),
    ],
    how_h="How I decided what comes next",
    how=["~Every item has to answer the founder's question: does it change how a team uses AI in its actual work?",
         "~Retention and renewal come before new audiences: a learner who returns, and a company that renews.",
         "?What else shaped priorities | data, partner requests, cost to build"])

# ---------------------------------------------------------------- the author's account (2026-11-01): everything they did at myAIcademy
M["owned"] = [
    ("Vision and roadmap", "Where the product goes, quarter by quarter and year by year."),
    ("Product design", "The web app, the mobile app and the website, end to end."),
    ("Lesson content", "What a lesson is, plus writing and narrating the content."),
    ("Automation", "The lesson pipeline, email automations and more, built with AI."),
    ("Brand and media", "Graphics, social media posts and video editing."),
]
M["dek"] = "As Head of Product Design and the product owner, I led myAIcademy end to end: the vision and roadmap, the web and mobile apps and the website, the lesson content and its narration, the automations behind it, and the brand's graphics and video."
W = {s["name"]: s for s in M["workflow"]["stages"]}
W["Content"]["me"] = "I wrote and narrated lesson content myself. ~AI drafted, and I edited every line for tone: *Committed*, not *Hard*."
W["Visuals"]["ai"] = "Illustrations for every lesson, plus first drafts of tool artwork for the course cards."
W["Visuals"]["me"] = "The graphics for social media posts, and one blue and one typeface so generated art never set the style."
W["Automation"]["ai"] = "The lesson pipeline runs scans and says which lesson to build, and whether it belongs in a weekly course, the featured course or a persona-based course. Then it gathers the screenshots and illustrations and adds the voice."
W["Automation"]["me"] = "I worked out the logic behind the automations: for lessons, for emails and for much more. ~And what the pipeline may publish on its own, and what a person checks first."
W["Voice and video"]["ai"] = "Lesson voice-overs put together with ElevenLabs."
W["Voice and video"]["me"] = "Content narration, and video editing for lessons and social media."
M["workflow"]["lead"] = "This was very much AI-based work. AI ran across every stage, from research to the voice of each lesson; what changed was the speed of trying things, and the decisions stayed mine."
M["lessons"]["lead"] = "I owned the lesson content as well as the screens it sits in: the standard, the writing and the narration. Every lesson follows the same rules."
M["lessons"]["rules"][4]["lens"] = {"ai": "Kept current by the lesson pipeline I built: scans pick the lesson, then screenshots, illustrations and an ElevenLabs voice are added."}
# ---------------------------------------------------------------- the other eight, from the older copy deck
# These pages have no project files yet, so the structure is complete but the thinking is the author's to add:
# what the old deck inferred is marked as a draft (~) and every gap is an "Add" box (?).
H1 = {
 "mf-street": "MF Street: a first SIP in *one screen*, for investors facing 2,000 funds",
 "godofx": "GodoFX: live prices and the licence *on one screen*, for traders deciding whether to trust a broker",
 "healthpractice": "HealthPractice: a clinic platform designed *from zero*, now used by 13,400+ practitioners",
 "tbil": "TBIL: answering “what does my plan cover?” *before the treatment*, not after the bill",
 "hoffmann-group": "Hoffmann Group: finding one tool *among half a million*, with or without a part number",
 "dashboards": "myAIcademy dashboards: from six tabs to *one sentence* about what to do on Monday",
 "lesson-pipeline": "The lesson pipeline: keeping 40 AI tools' lessons *current within 72 hours*",
 "this-portfolio": "This portfolio: a designer's site *built the way he says he works*",
}
HOOK = {
 "mf-street": "Fund in, SIP started. One screen, no spreadsheet.",
 "godofx": "The spread, the licence and the open-account button, in the same glance.",
 "healthpractice": "Built from zero into the platform a clinic opens every morning.",
 "tbil": "The coverage question answered before the treatment, not after the bill.",
 "hoffmann-group": "Half a million tools, found in three taps, with or without a part number.",
 "dashboards": "What moved, why, and what to do on Monday. In one sentence.",
 "lesson-pipeline": "A brief goes in on Monday. A voiced lesson is live within 72 hours.",
 "this-portfolio": "Built the way I claim to work, so the site is the case study.",
}
HI = {"tbil": "#b88f00", "lesson-pipeline": "#b88f00", "mf-street": "#c99b00", "hoffmann-group": "#c99b00"}
TODO_TURN = "?The options you weighed | two or three real alternatives, what each would have cost, and why this one won"

def convert(p):
    slug = p["slug"]; figs = p["results"]["figures"]
    first = next((f for f in figs if f[0] != "todo"), None)
    items = p["solution"]["items"]
    explored = [r for t, rs in p["process"]["slip"] if t == "Explored" for r in rs]
    def m(ref): return ref(None)
    # decision 1 comes from the directions the old deck says were explored; the rest from the solution items
    d1 = dict(short=p["process"]["end"][0],
              title="~Why " + p["process"]["end"][0][0].lower() + p["process"]["end"][0][1:],
              hook="~" + p["problem"]["beats"][0][1],
              before=dict(text="?The design before | what the product, or the pattern you started from, looked like", media=m(p["problem"]["ref"])),
              options=[("Chosen" if not r["off"] else f"Option {chr(65 + i)}", "~" + r["what"], "?Its trade-off | what it would have cost" if r["off"] else "?Why it won | the evidence that tipped it", not r["off"]) for i, r in enumerate(explored)],
              why="?The turning point | what you were stuck between, and what made you choose",
              actions=["~" + it["name"] for it in items[:3]],
              after=m(items[0]["ref"]),
              result="?What happened | what changed for users or the business, a number or a specific observation")
    rest = []
    for it in items[1:3]:
        line, _, ans = it["line"].partition("Answers:")
        rest.append(dict(short=it["name"], title="~" + it["name"], hook="~" + line.strip(),
                         before=dict(text="~Before: " + ans.strip().rstrip(".") + "." if ans else "?The design before | the version this replaced"),
                         options=[], why=TODO_TURN, actions=["?The design moves | what you did right after deciding"],
                         after=m(it["ref"]), result="?What happened | feedback, testing or a number"))
    ctx = [(a, b) for a, b in p["hero"]["facts"]] + [("My role", p["results"]["owned"]), ("Duration", "?How long it ran | and how big the team was"), ("Constraints", "?Key constraints | time, access to users, legacy systems, regulation")]
    return dict(
     slug=slug, name=p["name"], accent=p["accent"], accent_ink=p["accent_ink"], hi=HI.get(slug, p["accent"]), poster=p["poster"],
     title=p["title"], desc=p["desc"],
     kicker=["Case study", p["name"], p["hero"]["facts"][0][1]],
     h1=H1[slug], dek=p["hero"]["sentence"],
     facts=[p["hero"]["facts"][0], p["hero"]["facts"][1], p["hero"]["facts"][2], ("Outcome", f"{first[0]} {first[1]}" if first else "?Outcome | one line")],
     teaser=dict(m(items[0]["ref"]), caption=items[0]["ref"](None).get("caption", "")),
     hook=[HOOK[slug], "?A moment that starts the story | a real user quote, a support ticket, or the moment you saw what was broken. Two or three sentences, with a person in them."],
     intro=dict(summary=p["hero"]["sentence"] + " " + p["results"]["owned"],
                challenge="~" + p["problem"]["h2"] + " " + p["problem"]["beats"][2][1],
                outcome=f"{first[0]}: {first[1]}." if first else "?The outcome | one line"),
     problem=dict(h2=p["problem"]["h2"], paras=["~" + b for _, b in p["problem"]["beats"]], context=ctx,
                  evidence=[m(p["process"]["ref"])]),
     journey=dict(h2="~Walking through " + p["name"], note="",
                  lead="?One person, one scenario | who is using it, when, and what they are trying to get done",
                  steps=[dict(title="~" + it["name"], thought="?What they think and feel here | their intent at this screen, not the tap they make", media=m(it["ref"]), notes=[]) for it in items]),
     decisions=dict(h2="~The decisions behind it", lead="?Three to five decisions | each with the options you weighed and why you chose", items=[d1] + rest),
     iterations=dict(h2="~The versions that didn't make it", lead="?Versions you threw away | two or three earlier versions of one screen, each with why it failed", rounds=[]),
     system=dict(h2="~The system under the screens", lead="", todo="?The UI system | type, colour, components and spacing, with one reason for each"),
     ai=dict(h2="What AI did, and what I decided", lead="?How AI fitted in | or say plainly that it didn't",
             by_ai=["?What AI executed | drafts, images, code, research"], by_me=["?What you decided | the calls only you made"]),
     reflection=dict(h2="What I'd keep, and what I'd change",
                     learn=[("?What surprised you | one moment from the project", ""), ("?A decision you'd make differently | and why", ""), ("?What it taught you | something only this project could", "")],
                     future=[("?Where it goes next | tied to something you saw users do", "")]),
     results=dict(figures=figs[:4], source=p["results"]["source"]),
     close=dict(h2="Want the longer version?", text="I'm happy to walk through the decisions behind it."),
     credit="")
# ---------------------------------------------------------------- the author's own account (2026-11-01), applied over every page
# Facts in the author's words are plain text; my framing of them is a draft (~); what only the author knows is a gap (?).
def gap_shot(what): return dict(kind="slot", what=what, caption="")

def decision(short, h3, hook, options, why, actions, result="?What happened | a number, or what you saw users do", before="?The design before | what it looked like, or the pattern you started from", after=None):
    return dict(short=short, h3=h3, title=h3, hook=hook, before=dict(text=before, media=None), options=options, why=why, actions=actions,
                after=after or gap_shot("The screen as shipped"), result=result)

def steps(person_lead, items):
    return dict(h2="~Walking through it", note="", lead=person_lead,
                steps=[dict(title=a, thought=b, media=gap_shot(a), notes=[]) for a, b in items])

GAPOPTS = [("Option A", "?A route you considered | and what it would have cost", "", False), ("Option B", "?Another route | and its trade-off", "", False)]

STORY = {}

STORY["mf-street"] = dict(
    tagline="Trading, stocks and mutual funds in one app, each clearly its own.",
    h1="MF Street: trading, stocks and mutual funds, *each clearly its own*",
    dek="At Rillusion, working with my mentor, I designed MF Street: one app where people trade intraday, invest in stocks and invest in mutual funds. The problem was that every kind of investment looked the same.",
    facts=[("Studio", "Rillusion, with my mentor"), ("My role", "UI/UX designer"), ("Platforms", "Web and mobile"), ("Scope", "Intraday trading, stocks and mutual funds")],
    overview=dict(challenge="MF Street offered intraday trading, stocks and mutual funds in one place, with no clear line between them.",
                  approach="~Give each kind of investing its own space, language and pace, so a same-day trade never looks like a monthly SIP.",
                  outcome="?The outcome | what changed for investors or the business once the types were told apart"),
    problem_h2="Every investment looked the same.",
    problem=["MF Street let people trade intraday, buy stocks and invest in mutual funds from one app. The types sat side by side, with nothing to tell them apart.",
             "~For an investor that is a real risk: a same-day trade and a long-term SIP carry very different stakes, and one screen for both invites the wrong choice."],
    owned=[("Investment types", "~A clear distinction between intraday, stocks and mutual funds."), ("UX and UI", "The flows and screens on web and mobile.")],
    first_decision=decision("Each type its own space", "~Why every kind of investing got its own space",
        "~Intraday, stocks and mutual funds were shown the same way, so nothing told an investor which kind of decision they were making.",
        GAPOPTS + [("Chosen", "~A clear distinction between the investment types", "?Why it won | what made this the right call", True)],
        "?The turning point | how you decided the way each type should differ: navigation, colour, language, the order of steps",
        ["?What you designed | for example separate entry points, a different look for each type, different confirmation steps"]),
)

STORY["godofx"] = dict(
    tagline="A forex trading product and the site that sells it.",
    h1="GodoFX: the trading product *and the site that sells it*",
    dek="At Rillusion I designed both halves of GodoFX: the marketing site that shows traders the broker has real trading software, and the product they trade forex in.",
    facts=[("Studio", "Rillusion, with my mentor"), ("My role", "UI/UX designer"), ("Scope", "Marketing site and the trading product"), ("Platforms", "MT4, ZuluTrade and RoboX")],
    overview=dict(challenge="GodoFX needed a marketing site that proves it has a real trading product, and the product behind it.",
                  approach="~Design the site and the product as one: the site shows the product traders will actually use.",
                  outcome="The site went live in June 2021. ?What happened next | sign-ups, deposits, or what the broker said"),
    problem_h2="A broker has to prove its software.",
    problem=["GodoFX sells forex trading. Its marketing site had to show traders that there is a real product behind it, where they buy and sell.",
             "I designed the website and the product itself, so what the site promises is what the trader finds after signing up."],
    owned=[("Marketing site", "The site that presents the product to traders."), ("Trading product", "The product traders use to buy and sell.")],
)

STORY["healthpractice"] = dict(
    tagline="Patient care and doctor care, managed from A to Z.",
    h1="HealthPractice: patient care and doctor care, *from A to Z*",
    dek="HealthPractice is Sysvine's own product for managing a practice from A to Z, for patients and for doctors. It was the main product I worked on at Sysvine, and I was its designer.",
    facts=[("Company", "Sysvine Technologies, internal product"), ("My role", "The product's designer"), ("Scope", "Patient care and doctor care, A to Z"), ("Reach", "84+ countries, 41+ specialties")],
    overview=dict(challenge="Manage everything a practice does, for the patient and for the doctor, in one product.",
                  approach="~One core for the whole practice, with each part of patient and doctor care designed as part of the same system.",
                  outcome="More than 13,400 practitioners in 8,500+ practices use it, as its site states."),
    owned=[("Patient care", "The patient's side, from booking to records."), ("Doctor care", "The doctor's side, from the day's list to notes and billing."), ("Design system", "One system across the product.")],
)

STORY["tbil"] = dict(
    tagline="Which hospital takes which insurance, for which treatment.",
    h1="TBIL: which hospital takes *which insurance, for which treatment*",
    dek="US health insurance is technical: a plan may pay for one treatment and not another, and each hospital accepts only some plans. At Sysvine I designed TBIL, which untangles that, and I owned the UX thinking and the UI.",
    facts=[("Company", "Sysvine Technologies"), ("My role", "UX and UI"), ("Market", "US healthcare insurance"), ("Search by", "Hospital, procedure or insurance")],
    overview=dict(challenge="In the US, insurance is claimed per treatment, and hospitals accept only certain plans. People struggle to pick the right plan for the right procedure at the right hospital.",
                  approach="Separate the three things people start from, hospitals, procedures and insurance plans, and let a search begin from any of them.",
                  outcome="?The outcome | searches run, support calls, or what users said"),
    problem_h2="The right plan, the right hospital, the right treatment.",
    problem=["In India a policy usually covers the overall medical bill. In the US, a particular insurance pays only for particular treatments, and some hospitals take a plan while others don't.",
             "So people find it hard to apply for, or use, the right insurance for the right procedure. TBIL sorts out which hospital offers what, and which insurance is tied to which hospital."],
    owned=[("UX thinking", "How three ways in stay one product."), ("UI", "Every screen of the search and its results.")],
    journey=steps("?One person and their question | for example someone booking a knee operation who needs to know where their plan is accepted",
                  [("Search by hospital", "See every insurance the hospital accepts, and for which procedures."),
                   ("Search by procedure", "See which hospitals perform it, and which insurances they accept for it."),
                   ("Search by insurance", "See every clinic that takes the plan, and which treatments it covers there.")]),
    decisions=[decision("Three ways in", "~Why a search can start from a hospital, a procedure or an insurance plan",
        "People arrive with different starting points: a hospital they trust, a treatment they need, or the plan they already hold.",
        GAPOPTS + [("Chosen", "Three ways in, one set of answers", "Hospital, procedure or insurance, each showing how the other two connect.", True)],
        "~Each starting point is real for someone, so none of them could be secondary. The cost was keeping three entry points consistent, so the answer looks the same whichever way you came in.",
        ["Search by hospital: insurances accepted, by procedure", "Search by procedure: hospitals and the insurances they take for it", "Search by insurance: clinics and treatments available on the plan"])],
)

STORY["hoffmann-group"] = dict(
    tagline="One platform of internal apps, each with its own product owner.",
    h1="Hoffmann Group: one platform, *many internal apps*",
    dek="Hoffmann Group supplies industrial tools. At Sysvine I designed its internal platform: several apps in one, each run by its own product owner, for managing discounts, products and inventory.",
    facts=[("Company", "Sysvine Technologies"), ("Client", "Hoffmann Group, Munich"), ("Scope", "Discounts, product management, inventory"), ("Owners", "A product owner for each app")],
    overview=dict(challenge="Hoffmann needed one platform holding several internal apps, each solving its own problem and each managed by a different product owner.",
                  approach="~One shell and one design language for every app, so each team's tool solves its own problem without feeling like a different product.",
                  outcome="?The outcome | which apps shipped, who uses them, what got faster"),
    problem_h2="Several internal jobs, several owners, one platform.",
    problem=["Hoffmann Group is an industrial tools company. Running it takes several internal products: one for discounts on products, one for managing the products, one for how products are kept in inventory.",
             "Each app had its own product owner and its own problem, and all of them had to live in one platform."],
    owned=[("Discount management", "Applying discounts on products."), ("Product management", "Managing the product range."), ("Inventory", "How products are stocked and tracked.")],
    journey=steps("?Who uses the platform | for example a pricing manager setting a discount, or a warehouse lead checking stock",
                  [("Discount management", "Applying and managing discounts on products."),
                   ("Product management", "Keeping the product range in order."),
                   ("Inventory", "Seeing how products are stocked, and where.")]),
    decisions=[decision("One platform, many owners", "~Why every app shares one shell",
        "Each app had its own product owner and its own problem. Left alone, each would have grown its own way of working.",
        GAPOPTS + [("Chosen", "~One platform and one design language", "~Each app solves its own problem inside a shared frame.", True)],
        "?The turning point | how you agreed one way of working with several product owners",
        ["?What you designed | the shared navigation, components and patterns every app uses"])],
    figures=[("500,000+", "products in Hoffmann Group's range, as its site states"), ("3", "internal apps: discounts, products and inventory"), ("todo", "time saved per task, or teams using the platform")],
)

STORY["dashboards"] = dict(
    facts=[("Company", "myAIcademy"), ("My role", "Head of Product Design and Product Owner"), ("Built with", "Claude Code, on live data"), ("Views", "Operations, learning analytics, admin")],
)

STORY["lesson-pipeline"] = dict(
    tagline="It decides which lesson to build, then builds it.",
    h1="The lesson pipeline: it decides *which lesson to build*, then builds it",
    dek="I built the automation behind myAIcademy's lessons. It runs scans to decide which lesson to build and whether it belongs in a weekly course, the featured course or a persona-based course, then gathers screenshots, makes the illustrations and adds the voice with ElevenLabs.",
    facts=[("Company", "myAIcademy"), ("My role", "Head of Product Design; built the automation"), ("Stack", "n8n, Claude, NotebookLM, ElevenLabs"), ("Decides", "Weekly, featured or persona-based course")],
    overview=dict(challenge="Lessons fall behind tools that change every week, and deciding what to build next took as much work as building it.",
                  approach="An automation that scans, decides which lesson to build and where it belongs, then gathers screenshots, illustrations and voice.",
                  outcome="Paths refresh within 72 hours of a major tool change. ?Lessons per week | or hours per lesson before and after"),
    problem_h2="Deciding what to build was half the work.",
    problem=["Every week new AI tools launch and old ones change. Someone has to decide which lessons to build, where each belongs, and then make it: screenshots, illustrations and narration.",
             "I automated that: the pipeline runs scans, says which lesson to build and whether it is a weekly course, the featured course or a persona-based course, then assembles it."],
    owned=[("The decision", "Scans that say which lesson to build, and where it goes."), ("The assets", "Screenshots and illustrations for each lesson."), ("The voice", "Narration put together with ElevenLabs."), ("Email automations", "Emails that send themselves, alongside the lessons.")],
)

STORY["this-portfolio"] = dict(
    dek="I trained as an architect, five years of study and a year in practice, while teaching myself product design. This portfolio is built the way I now work: designed, written, rendered and coded with AI.",
)

def patch(c):
    s = STORY.get(c["slug"])
    if not s: return c
    for k in ("tagline", "h1", "dek", "facts", "overview", "journey"):
        if k in s: c[k] = s[k]
    if "problem_h2" in s: c["problem"]["h2"] = s["problem_h2"]
    if "problem" in s: c["problem"]["paras"] = s["problem"]
    if "owned" in s: c["owned"] = s["owned"]
    if "decisions" in s: c["decisions"]["items"] = s["decisions"]
    if "first_decision" in s: c["decisions"]["items"][0] = s["first_decision"]
    if "figures" in s: c["results"]["figures"] = s["figures"]
    if "overview" in s: c["intro"]["outcome"] = s["overview"]["outcome"]
    if s.get("journey"): c["teaser"] = dict(kind="slot", what="A recording or screenshot of " + c["name"], caption="")
    return c

# ---------------------------------------------------------------- Lab Fellows, a new page from the author's account
LABFELLOWS = dict(
    slug="lab-fellows", name="Lab Fellows", accent="#0f7b6c", accent_ink="#ffffff", hi="#0f7b6c", poster="p0", close_img="",
    title="Lab Fellows: lab inventory that reorders itself | Ashfaq Imran",
    desc="How Ashfaq Imran designed the UX and UI of Lab Fellows, where AI watches a research lab's stock and asks the right supplier to refill it.",
    h1="Lab Fellows: lab inventory that *reorders itself*", tagline="Lab inventory that reorders itself.",
    dek="Lab Fellows supplies lab equipment and chemicals to research companies. Its product watches the inventory with AI and, when stock runs low, sends a refill request to the supplier of that exact item. At Sysvine I owned the UX thinking and the UI.",
    facts=[("Company", "Sysvine Technologies"), ("My role", "UX and UI"), ("Customers", "Research companies and labs"), ("AI", "Spots low stock and requests refills")],
    teaser=dict(kind="slot", what="A screen of the Lab Fellows inventory", caption=""),
    hook=["Running out of one chemical can stop a lab's work.", "?A moment that starts the story | a lab that ran out, or the first time you saw how stock was tracked"],
    intro=dict(summary="Lab Fellows supplies lab equipment and chemicals to research companies, with a product that manages their inventory.",
               challenge="Keep a research lab stocked without someone counting shelves.", outcome="?The outcome | one line"),
    overview=dict(challenge="Research companies need the right chemicals and equipment in stock, and noticing what is running low is slow manual work.",
                  approach="AI checks the inventory and, wherever stock is low, sends a refill request to the person or company that supplies that item. I designed how people see and trust that.",
                  outcome="?The outcome | refills automated, stock-outs avoided, or what labs said"),
    owned=[("UX thinking", "How people see stock, and trust what the AI does."), ("UI", "The inventory and refill screens.")],
    problem=dict(h2="The shelf runs out before anyone notices.",
                 paras=["Lab Fellows supplies lab equipment and chemicals to research companies, so the problem is inventory: knowing what is there and what is about to run out.",
                        "The product uses AI to check stock and, wherever it is low, to start a refill request to the particular supplier of that chemical or piece of equipment."],
                 context=[("My role", "UX and UI")], evidence=[]),
    journey=steps("?One person and their day | for example a lab manager starting the week",
                  [("Stock at a glance", "~What is in the lab, and what is running low."),
                   ("The AI notices", "~An item drops below its level and is flagged."),
                   ("A refill request goes out", "The request goes to the supplier of that exact item."),
                   ("~The person stays in control", "?What people can check, change or stop | before or after a request goes out")]),
    decisions=dict(h2="~The decisions behind it", lead="?Three to five decisions | each with the options you weighed and why you chose",
                   items=[decision("Automatic refills, visible", "~Why the AI's refill requests are always shown",
                        "~An automation that orders on its own only helps if people trust it.",
                        GAPOPTS + [("Chosen", "~The AI requests refills, and people can see each one", "?Why it won", True)],
                        "?The turning point | how much the AI does on its own, and what a person approves",
                        ["?What you designed | for example the low-stock signal, the request status, the supplier view"])]),
    iterations=dict(h2="~The versions that didn't make it", lead="?Versions you threw away | two or three earlier versions of one screen, each with why it failed", rounds=[]),
    system=dict(h2="~The system under the screens", lead="", todo="?The UI system | type, colour, components and spacing, with one reason for each"),
    ai=dict(h2="What AI did, and what I decided", lead="The product itself runs on AI: it watches stock and requests refills.",
            by_ai=["Checks the inventory and spots low stock", "Sends a refill request to the right supplier"],
            by_me=["How the inventory and its warnings are shown", "?What else you decided | for example what a person must approve"]),
    reflection=dict(h2="What I'd keep, and what I'd change",
                    learn=[("?What surprised you | one moment from the project", ""), ("?What it taught you | about designing around an AI that acts on its own", "")],
                    future=[("?Where it goes next | tied to something you saw users do", "")]),
    results=dict(figures=[("todo", "refill requests sent automatically, or stock-outs avoided")], source="?Sources | the product's site, once you send the link"),
    close=dict(h2="Want the longer version?", text="I'm happy to walk through how the inventory and the AI work together."),
    credit="")

# ---------- write the pages ----------
CONTENT = [MYAICADEMY] + [patch(convert(p)) for p in PAGES if p["slug"] != "myaicademy"]
CONTENT.insert([c["slug"] for c in CONTENT].index("hoffmann-group") + 1, LABFELLOWS)
for i, c in enumerate(CONTENT):
    nxt = CONTENT[(i + 1) % len(CONTENT)]
    d = os.path.join(OUT, "case-studies", c["slug"]); os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "index.html"), "w") as f: f.write(page(c, nxt))
    print("wrote", c["slug"])
