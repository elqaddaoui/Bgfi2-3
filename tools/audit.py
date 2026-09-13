#!/usr/bin/env python3
"""Structural integrity audit for index.html.

Checks, at both viewport widths:
  · every in-page anchor (`href="#…"`) resolves to an existing element
  · no duplicate `id` attributes
  · no broken <img> (loaded but naturalWidth === 0)
  · no console errors / page errors
  · no horizontal document overflow
  · counter targets (`data-target`) all animate to their final value
"""
import sys
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8080/index.html"
VIEWPORTS = [("desktop", 1440, 900), ("mobile", 390, 844)]


def audit(pg, label, problems):
    # --- anchors ---------------------------------------------------
    for bad in pg.evaluate(
        """() => [...document.querySelectorAll('a[href^="#"]')]
             .map(a => a.getAttribute('href'))
             .filter(h => h && h.length > 1 && !document.querySelector(h))"""):
        problems.append(f"[{label}] dead anchor -> {bad}")

    # --- duplicate ids ---------------------------------------------
    for dup in pg.evaluate(
        """() => { const seen = {}, out = [];
             document.querySelectorAll('[id]').forEach(e => {
               seen[e.id] = (seen[e.id] || 0) + 1; });
             for (const k in seen) if (seen[k] > 1) out.push(`${k} x${seen[k]}`);
             return out; }"""):
        problems.append(f"[{label}] duplicate id -> {dup}")

    # --- broken images ---------------------------------------------
    for b in pg.evaluate(
        """() => [...document.images]
             .filter(i => i.complete && i.naturalWidth === 0)
             .map(i => i.getAttribute('src'))"""):
        problems.append(f"[{label}] broken image -> {b}")

    # --- horizontal overflow ---------------------------------------
    ow = pg.evaluate("() => ({sw: document.documentElement.scrollWidth,"
                     " cw: document.documentElement.clientWidth})")
    if ow["sw"] > ow["cw"] + 1:
        problems.append(f"[{label}] horizontal overflow {ow}")

    # --- counters reach their target -------------------------------
    for c in pg.evaluate(
        """() => [...document.querySelectorAll('[data-target]')].map(e => ({
             target: e.dataset.target,
             shown: e.textContent.trim(),
             seen: e.getBoundingClientRect().top < innerHeight * 3 }))"""):
        if not c["seen"]:
            continue
        want = c["target"].replace(".", ",")
        if want not in c["shown"]:
            problems.append(f"[{label}] counter '{c['target']}' shows "
                            f"'{c['shown']}' (not settled)")


def main():
    problems = []
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
        for label, w, h in VIEWPORTS:
            pg = b.new_page(viewport={"width": w, "height": h})
            logs = []
            pg.on("console", lambda m: logs.append(f"{m.type}: {m.text}"))
            pg.on("pageerror", lambda e: logs.append(f"pageerror: {e}"))
            pg.goto(BASE, wait_until="load", timeout=60000)
            pg.wait_for_timeout(1200)
            # walk the whole document so lazy images + counters fire
            pg.evaluate(
                """async () => {
                    const step = innerHeight * 0.9;
                    for (let y = 0; y < document.body.scrollHeight; y += step) {
                        scrollTo(0, y);
                        await new Promise(r => setTimeout(r, 90));
                    }
                    scrollTo(0, 0);
                }""")
            pg.wait_for_timeout(2500)
            audit(pg, label, problems)
            for m in logs:
                low = m.lower()
                if "error" in low or "failed to load" in low:
                    problems.append(f"[{label}] console -> {m}")
            pg.close()
        b.close()

    print("=== STRUCTURAL AUDIT ===")
    if problems:
        for pr in problems:
            print("  !", pr)
        sys.exit(1)
    print("  PASS — anchors, ids, images, counters, overflow, console all clean")


if __name__ == "__main__":
    main()
