#!/usr/bin/env python3
"""Mobile screenshots of chapter dividers + overflow audit."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path("/tmp/shots")
OUT.mkdir(exist_ok=True)
URL = "http://localhost:8080/index.html"
ids = sys.argv[1:] or ["chapitre-3", "chapitre-8"]
FREEZE = "*,*::before,*::after{animation:none !important;transition:none !important}"

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 390, "height": 844})
    pg.goto(URL, wait_until="load")
    pg.wait_for_timeout(2500)
    pg.add_style_tag(content=FREEZE)
    pg.evaluate(
        "document.querySelectorAll('.reveal-up,.reveal-left,.reveal-right,.reveal')"
        ".forEach(e=>e.classList.add('in-view'))"
    )
    pg.wait_for_timeout(700)

    ow = pg.evaluate("document.documentElement.scrollWidth")
    print("scrollWidth:", ow, "(viewport 390)")
    wide = pg.evaluate(
        """()=>{const out=[];document.querySelectorAll('.chapitre-divider *').forEach(e=>{
             const r=e.getBoundingClientRect();
             if(r.width>392 && r.width<9000) out.push(e.className+' '+Math.round(r.width));});
           return out.slice(0,12);}"""
    )
    print("overflowing nodes in dividers:", wide or "none")

    for i in ids:
        box = pg.evaluate(
            """(id)=>{const e=document.getElementById(id);if(!e)return null;
               const r=e.getBoundingClientRect();return {y:r.top+window.scrollY,h:r.height};}""",
            i,
        )
        if not box:
            print("missing", i)
            continue
        pg.evaluate("y=>window.scrollTo(0,y)", box["y"])
        pg.wait_for_timeout(400)
        h = min(int(box["h"]), 1400)
        pg.screenshot(path=str(OUT / f"m-{i}.png"), clip={"x": 0, "y": 0, "width": 390, "height": h})
        print("shot", i, int(box["h"]))
    b.close()
