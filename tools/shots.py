#!/usr/bin/env python3
"""Screenshot each chapitre divider using viewport clips (animation-safe)."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path("/tmp/shots")
OUT.mkdir(exist_ok=True)
URL = "http://localhost:8080/index.html"
ids = sys.argv[1:] or [f"chapitre-{i}" for i in range(1, 9)]

FREEZE = "*,*::before,*::after{animation:none !important;transition:none !important}"

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1440, "height": 1000})
    pg.goto(URL, wait_until="load")
    pg.wait_for_timeout(2500)
    pg.add_style_tag(content=FREEZE)
    pg.evaluate(
        "document.querySelectorAll('.reveal-up,.reveal-left,.reveal-right,.reveal')"
        ".forEach(e=>e.classList.add('in-view'))"
    )
    pg.wait_for_timeout(800)

    for i in ids:
        box = pg.evaluate(
            """(id)=>{const e=document.getElementById(id);if(!e)return null;
               const r=e.getBoundingClientRect();
               return {y:r.top+window.scrollY,h:r.height};}""",
            i,
        )
        if not box:
            print("missing", i)
            continue
        pg.evaluate("y=>window.scrollTo(0,y)", box["y"])
        pg.wait_for_timeout(400)
        h = min(int(box["h"]), 1000)
        pg.screenshot(path=str(OUT / f"{i}.png"), clip={"x": 0, "y": 0, "width": 1440, "height": h})
        print("shot", i, int(box["h"]))
    b.close()
