#!/usr/bin/env python3
"""
Reorder the BGFI Lisolo newsletter according to the official 8-chapter plan.

The script is idempotent-ish: it works from the *current* index.html, extracts
every top-level <section> block (with its leading HTML comment banner), then
rewrites index.html in the canonical chapter order, inserting the chapter
dividers (chapitres.html fragments) between them.

No editorial copy is modified: blocks are moved verbatim.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "index.html"

html = SRC.read_text(encoding="utf-8")

# ------------------------------------------------------------------
# 1 · Split the document into: head/pre, [section blocks], tail
# ------------------------------------------------------------------
BLOCK_RE = re.compile(
    r"(?:^<!--(?:.|\n)*?-->\n)?^<section(?:[^>]*)>(?:.|\n)*?^</section>\n",
    re.M,
)

blocks = []
spans = []
for m in BLOCK_RE.finditer(html):
    blocks.append(m.group(0))
    spans.append(m.span())

if not blocks:
    sys.exit("No top-level sections found — aborting.")

pre = html[: spans[0][0]]
tail = html[spans[-1][1] :]

# sanity: nothing but blank lines between consecutive blocks
for (a, b), (c, d) in zip(spans, spans[1:]):
    between = html[b:c]
    if between.strip():
        sys.exit(f"Unexpected content between sections: {between[:200]!r}")


GENERIC = {"story-section", "reveal-up", "container"}


def key_of(block: str) -> str:
    tag = re.search(r"<section\b[^>]*>", block).group(0)
    m = re.search(r'id="([^"]+)"', tag)
    if m:
        return m.group(1)
    cls = re.search(r'class="([^"]+)"', tag)
    if cls:
        classes = [c for c in cls.group(1).split() if c not in GENERIC]
        for c in classes:
            if c.endswith("-section") or c.endswith("-strip"):
                return c
        if classes:
            return classes[0]
    return "unknown"


by_key = {}
for b in blocks:
    k = key_of(b)
    if k in by_key:
        sys.exit(f"Duplicate section key: {k}")
    by_key[k] = b

print("Sections found:", ", ".join(by_key))

# ------------------------------------------------------------------
# 2 · Split the legacy "triple feature" section (Fanzone + 2 trainings)
#     Fanzone  -> Chapitre V  (BGFI s'engage & culture d'entreprise)
#     English + DISC -> Chapitre VII (Formation & développement des talents)
#     Card markup is reused verbatim.
# ------------------------------------------------------------------
triple = by_key.pop("double-story-section", None)
if triple is None:
    sys.exit("Triple feature section not found (already split?).")

cards = re.findall(
    r'      <article class="double-card(?:.|\n)*?      </article>\n', triple
)
if len(cards) != 3:
    sys.exit(f"Expected 3 cards in the triple feature section, found {len(cards)}")

fanzone_card, english_card, disc_card = cards


def restyle(card: str, delay: str) -> str:
    return re.sub(r'style="--rd:[^"]*"', f'style="--rd:{delay}"', card, count=1)


FANZONE_SECTION = """<!-- ============================================================
     CHAPITRE V · Fanzone Coupe d'Afrique — Événement fédérateur
     ============================================================ -->
<section class="story-section double-story-section fanzone-section" id="story-fanzone" aria-labelledby="fanzone-title">
  <div class="container reveal-up">
    <div class="section-eyebrow center">
      <span class="line"></span>
      <span class="eyebrow-text"><span class="bgfi-star bgfi-star--xs"></span> Culture d'entreprise · Juin 2026 <span class="bgfi-star bgfi-star--xs"></span></span>
      <span class="line"></span>
    </div>
    <h2 class="sr-only" id="fanzone-title">Fanzone Coupe d'Afrique</h2>
    <div class="double-grid double-grid--solo">
{FANZONE_CARD}    </div>
  </div>
</section>
""".replace("{FANZONE_CARD}", restyle(fanzone_card, ".05s"))

FORMATIONS_SECTION = """<!-- ============================================================
     CHAPITRE VII · Formations — ARC EN CIEL DISC & Anglais
     ============================================================ -->
<section class="story-section double-story-section formations-section" id="story-formations" aria-labelledby="formations-title">
  <div class="container reveal-up">
    <div class="section-eyebrow center">
      <span class="line"></span>
      <span class="eyebrow-text"><span class="bgfi-star bgfi-star--xs"></span> Deux formations · Avril — Juin 2026 <span class="bgfi-star bgfi-star--xs"></span></span>
      <span class="line"></span>
    </div>
    <h2 class="sr-only" id="formations-title">Formations du semestre</h2>
    <div class="double-grid">
{DISC_CARD}{ENGLISH_CARD}    </div>
  </div>
</section>
""".replace("{DISC_CARD}", restyle(disc_card, ".05s")).replace(
    "{ENGLISH_CARD}", restyle(english_card, ".15s")
)

by_key["story-fanzone"] = FANZONE_SECTION
by_key["story-formations"] = FORMATIONS_SECTION

# ------------------------------------------------------------------
# 3 · Chapter dividers
# ------------------------------------------------------------------
def divider(num, roman, slug, variant, eyebrow, title_html, standfirst, items, dateline):
    lis = "\n".join(
        '        <li class="cd-item"><a href="{href}">'
        '<span class="cd-item-star bgfi-star bgfi-star--xs" aria-hidden="true"></span>'
        '<span class="cd-item-text">{label}</span>'
        '<span class="cd-item-date">{date}</span></a></li>'.format(**it)
        for it in items
    )
    return f"""<!-- ============================================================
     CHAPITRE {roman} · {eyebrow}
     ============================================================ -->
<section class="chapitre-divider chapitre-divider--{variant}" id="chapitre-{num}" aria-labelledby="chapitre-{num}-title">
  <div class="cd-canvas" aria-hidden="true">
    <span class="cd-wash"></span>
    <span class="cd-mesh"></span>
    <span class="cd-grain"></span>
    <span class="cd-figure"></span>
    <span class="cd-numeral-ghost">{roman}</span>
    <span class="cd-spark cd-spark--a"></span>
    <span class="cd-spark cd-spark--b"></span>
    <span class="cd-spark cd-spark--c"></span>
  </div>

  <div class="container cd-inner">
    <p class="cd-kicker reveal-up">
      <span class="bgfi-star bgfi-star--xs" aria-hidden="true"></span>
      <span class="cd-kicker-text">Chapitre {roman}</span>
      <span class="cd-kicker-rule" aria-hidden="true"></span>
      <span class="cd-kicker-count">{num} / 8</span>
    </p>

    <div class="cd-head">
      <span class="cd-numeral reveal-up" aria-hidden="true">{roman}</span>
      <div class="cd-headings">
        <h2 class="cd-title reveal-up" id="chapitre-{num}-title" style="--rd:.06s">{title_html}</h2>
        <p class="cd-standfirst reveal-up" style="--rd:.12s">{standfirst}</p>
      </div>
    </div>

    <div class="cd-rule reveal-up" style="--rd:.16s" aria-hidden="true">
      <span class="cd-rule-line"></span>
      <span class="bgfi-star bgfi-star--sm"></span>
      <span class="cd-rule-line"></span>
    </div>

    <div class="cd-foot reveal-up" style="--rd:.2s">
      <ul class="cd-list" aria-label="Au sommaire de ce chapitre">
{lis}
      </ul>
      <p class="cd-dateline"><span class="bgfi-star bgfi-star--xs" aria-hidden="true"></span> {dateline}</p>
    </div>
  </div>
</section>
"""


D = {}

D[1] = divider(
    1, "I", "edito", "parchment",
    "Édito du Directeur Général",
    "Édito du <em>Directeur Général</em>",
    "Le mot d’ouverture du numéro&nbsp;: une étape importante dans notre histoire commune.",
    [dict(href="#edito", label="Édito du Directeur Général", date="Juin 2026")],
    "Ouverture du numéro · BGFI Lisolo N°01",
)

D[2] = divider(
    2, "II", "indicateurs", "data",
    "Indicateurs clés — Juin 2026",
    "Indicateurs clés<br/><em>Juin 2026</em>",
    "La performance en chiffres, et l’empreinte humaine qui la porte.",
    [
        dict(href="#indicateurs", label="Nos indicateurs · la performance en chiffres", date="Fin 2025"),
        dict(href="#impact", label="Notre empreinte en RDC", date="Semestre 1 · 2026"),
    ],
    "Le socle chiffré du semestre",
)

D[3] = divider(
    3, "III", "vie-sociale", "editorial",
    "Vie sociale et institutionnelle",
    "Vie sociale <em>et institutionnelle</em>",
    "Six mois de rendez-vous, de missions et de présences qui ont fait vivre la banque — de Kinshasa au Cap, de Brazzaville à Lubumbashi.",
    [
        dict(href="#story-social", label="Échange de vœux — Nous‑Mêmes", date="03 Janvier 2026"),
        dict(href="#retraite-strategique", label="Retraite stratégique à Brazzaville", date="Janvier 2026"),
        dict(href="#indaba-2026", label="Participation à INDABA", date="9 au 12 Février 2026"),
        dict(href="#story-abidjan", label="Séminaire Capital Humain et Communication 2026", date="Du 03 au 06 mars 2026"),
        dict(href="#story-perf", label="Réunion du personnel · performance &amp; ambitions", date="20 mars 2026"),
        dict(href="#story-banques", label="Mission auprès de nos banques correspondantes", date="22 mars au 4 avril 2026"),
        dict(href="#story-kbm", label="Participation au KBM", date="Du 20 au 22 mai 2026"),
        dict(href="#story-tour-variation-1", label="BGFI Tour", date="6 juin 2026"),
        dict(href="#story-mining", label="DRC Mining", date="Du 11 au 13 Juin 2026"),
    ],
    "Neuf temps forts · Janvier — Juin 2026",
)

D[4] = divider(
    4, "IV", "innovation", "circuit",
    "Innovation projets structurants",
    "Innovation<br/><em>projets structurants</em>",
    "Les chantiers qui transforment la banque&nbsp;: le digital, le réseau, et l’argent réinventé.",
    [
        dict(href="#story-digital", label="Projet de transformation digitale — kick off", date="Avril 2026"),
        dict(href="#story-muanda", label="Ouverture agence BGFIBank Muanda", date="28 avril 2026"),
        dict(href="#story-rakka", label="RakkaCash évolue", date="Mai 2026"),
    ],
    "Trois projets structurants · Avril — Mai 2026",
)

D[5] = divider(
    5, "V", "engagement", "bloom",
    "BGFI s'engage et culture d'entreprise",
    "BGFI s’engage <em>et culture d’entreprise</em>",
    "L’éducation, la santé, l’égalité, la fête&nbsp;: ce que nous défendons, et ce qui nous rassemble.",
    [
        dict(href="#story-education", label="Partenariat avec SBS dans l’éducation", date="Février 2026"),
        dict(href="#story-femme", label="Gender Equality · mois de la femme", date="Mars 2026"),
        dict(href="#story-mai", label="Fête du Travail", date="1<sup>er</sup> mai 2026"),
        dict(href="#story-ebola", label="Minute SST", date="20 mai 2026"),
        dict(href="#story-fanzone", label="Fanzone Coupe d’Afrique", date="Dès le 11 Juin 2026"),
    ],
    "Cinq engagements · Février — Juin 2026",
)

D[6] = divider(
    6, "VI", "valeurs", "beam",
    "Valeurs &amp; témoignages",
    "Valeurs <em>&amp; témoignages</em>",
    "Nos valeurs ne se décrètent pas&nbsp;: elles s’incarnent. Deux collaborateurs prennent la parole.",
    [
        dict(href="#temoignages", label="Cynthia Amani · valeur Intégrité", date="Témoignage"),
        dict(href="#temoignages", label="Olivier Mak Makaba · valeur Travail", date="Témoignage"),
    ],
    "Deux voix · Semestre 1 · 2026",
)

D[7] = divider(
    7, "VII", "formation", "ascend",
    "Formation — Développement des talents",
    "Formation<br/><em>développement des talents</em>",
    "Attirer, former, intégrer&nbsp;: le semestre où la montée en compétences devient un programme.",
    [
        dict(href="#story-etoiles", label="Programme BGFI ÉTOILE", date="Février 2026"),
        dict(href="#story-formations", label="Formation ARC EN CIEL DISC des chefs de départements", date="Du 23 avril au 8 mai 2026"),
        dict(href="#story-formations", label="Formation Anglais — Lancement", date="5 juin 2026"),
    ],
    "Trois programmes · Février — Juin 2026",
)

D[8] = divider(
    8, "VIII", "famille", "celebration",
    "Naissances et mariages",
    "Naissances <em>et mariages</em>",
    "La famille BGFI s’agrandit et se célèbre. Onze naissances, dont des triplés, et cinq unions.",
    [
        dict(href="#famille-variation-b", label="Naissances : 11 dont des triplés", date="11"),
        dict(href="#famille-variation-b", label="Mariages : 5", date="05"),
    ],
    "Les célébrations du semestre",
)

# ------------------------------------------------------------------
# 4 · The canonical order
# ------------------------------------------------------------------
ORDER = [
    "hero",
    "masthead-strip",
    "chapitres",            # sommaire (hidden by CSS, kept as-is)

    ("chapitre", 1),
    "edito",

    ("chapitre", 2),
    "indicateurs",
    "impact",

    ("chapitre", 3),
    "story-social",
    "retraite-strategique",
    "indaba-2026",
    "story-abidjan",
    "story-perf",
    "story-banques",
    "story-kbm",
    "story-tour-variation-1",
    "story-tour",             # hidden legacy variant, kept next to its sibling
    "story-tour-variation-2", # hidden
    "story-tour-variation-3", # hidden
    "story-mining",

    ("chapitre", 4),
    "story-digital",
    "story-muanda",
    "story-rakka",

    ("chapitre", 5),
    "story-education",
    "story-femme",
    "story-mai",
    "story-ebola",
    "story-fanzone",

    ("chapitre", 6),
    "temoignages",

    ("chapitre", 7),
    "story-etoiles",
    "story-formations",

    ("chapitre", 8),
    "famille-variation-b",
    "famille",                # hidden legacy variant
    "famille-variation-a",    # hidden

    "agenda",
    "abonnement",
    "finale",
]

missing = [k for k in ORDER if isinstance(k, str) and k not in by_key]
if missing:
    sys.exit(f"Missing sections in source: {missing}")

leftover = [k for k in by_key if k not in [k for k in ORDER if isinstance(k, str)]]
if leftover:
    sys.exit(f"Sections not placed in the new order: {leftover}")

out = [pre.rstrip("\n") + "\n\n"]
for key in ORDER:
    if isinstance(key, tuple):
        out.append(D[key[1]])
    else:
        out.append(by_key[key])
    out.append("\n")

new_html = "".join(out) + tail.lstrip("\n")
SRC.write_text(new_html, encoding="utf-8")
print("index.html rewritten:", len(new_html), "bytes")
