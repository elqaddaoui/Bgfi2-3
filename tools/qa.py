#!/usr/bin/env python3
"""Visual QA helper for the BGFI Lisolo newsletter.

Captures each requested selector at one viewport width and reports
horizontal overflow, broken images, clipped text and console errors.

Because the document is extremely tall, sections are captured as
viewport-sized chunks and stitched with PIL (keeps memory low in the
sandbox instead of using Playwright's full_page mode).

Usage:
    python3 tools/qa.py OUTDIR VIEWPORT sel1 sel2 ...
        VIEWPORT = desktop | mobile
"""
import sys
import os
from PIL import Image
from playwright.sync_api import sync_playwright

BASE = os.environ.get("QA_BASE", "http://localhost:8080/index.html")
VIEWPORTS = {"desktop": (1440, 900), "mobile": (390, 844)}
MAX_H = 5000

KILL_MOTION = """
  *, *::before, *::after {
    animation: none !important;
    transition: none !important;
    scroll-behavior: auto !important;
  }
"""

FORCE_REVEAL = """() => {
  document.querySelectorAll('[class*="reveal"]').forEach(el => {
    el.classList.add('in-view');
    // the IO may not have fired yet for off-screen nodes; the transition is
    // killed by KILL_MOTION so force the end-state inline as well
    el.style.opacity = '1';
    el.style.transform = 'none';
  });
}"""


def abs_box(page, sel):
    return page.evaluate(
        """(sel) => { const el = document.querySelector(sel); if (!el) return null;
             const r = el.getBoundingClientRect();
             return {x: r.x + scrollX, y: r.y + scrollY, w: r.width, h: r.height}; }""",
        sel)


def capture(page, sel, path, vw, vh):
    """Scroll-and-stitch capture of one element."""
    b = abs_box(page, sel)
    if not b or b["w"] < 2 or b["h"] < 2:
        raise RuntimeError(f"empty box for {sel}")
    x, y = max(b["x"], 0), max(b["y"], 0)
    w, h = int(min(b["w"], vw)), int(min(b["h"], MAX_H))
    tiles, off = [], 0
    while off < h:
        page.evaluate("(t) => window.scrollTo(0, t)", y + off)
        page.wait_for_timeout(260)
        page.evaluate(FORCE_REVEAL)
        page.wait_for_timeout(140)
        top = page.evaluate("() => window.scrollY")
        # element y relative to the current viewport
        rel = (y + off) - top
        tile_h = int(min(vh - max(rel, 0), h - off))
        if tile_h <= 0:
            break
        tmp = f"{path}.part{len(tiles)}.png"
        page.screenshot(path=tmp, clip={"x": x, "y": max(rel, 0),
                                        "width": w, "height": tile_h},
                        animations="disabled", timeout=30000)
        tiles.append((tmp, tile_h))
        off += tile_h
    total = sum(t[1] for t in tiles)
    out = Image.new("RGB", (w, total), "white")
    cy = 0
    for tmp, th in tiles:
        im = Image.open(tmp)
        out.paste(im, (0, cy))
        im.close()
        cy += th
        os.remove(tmp)
    out.save(path)
    out.close()


def main():
    outdir, vp = sys.argv[1], sys.argv[2]
    selectors = sys.argv[3:]
    vw, vh = VIEWPORTS[vp]
    os.makedirs(outdir, exist_ok=True)
    problems = []

    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox", "--disable-gpu",
                                          "--disable-dev-shm-usage"])
        page = browser.new_page(viewport={"width": vw, "height": vh},
                                device_scale_factor=1, reduced_motion="reduce")
        msgs = []
        page.on("console", lambda m: msgs.append(f"{m.type}: {m.text}"))
        page.on("pageerror", lambda e: msgs.append(f"pageerror: {e}"))
        page.goto(BASE, wait_until="load", timeout=60000)
        page.add_style_tag(content=KILL_MOTION)
        page.wait_for_timeout(700)

        ow = page.evaluate("() => ({sw: document.documentElement.scrollWidth,"
                           " cw: document.documentElement.clientWidth})")
        if ow["sw"] > ow["cw"] + 1:
            problems.append(f"[{vp}] page overflows horizontally {ow}")
            for o in page.evaluate(
                """(cw) => [...document.querySelectorAll('body *')]
                     .map(el => [el, el.getBoundingClientRect()])
                     .filter(([el, r]) => r.right > cw + 2 && r.width > 1 && r.height > 1
                             && getComputedStyle(el).position !== 'fixed')
                     .slice(0, 10)
                     .map(([el, r]) => `${el.tagName}.${(el.className||'').toString().trim().split(/\\s+/).slice(0,2).join('.')} right=${Math.round(r.right)}`)""",
                ow["cw"]):
                problems.append(f"    [{vp}] offender {o}")

        for sel in selectors:
            name = (sel.replace("#", "").replace(" > ", "-").replace(" ", "_")
                       .replace(".", "_").replace(":", "")[:60])
            if not page.query_selector(sel):
                problems.append(f"[{vp}] selector NOT FOUND: {sel}")
                continue
            try:
                capture(page, sel, os.path.join(outdir, f"{name}__{vp}.png"), vw, vh)
            except Exception as e:
                problems.append(f"[{vp}] capture failed {sel}: {e}")

            for c in page.evaluate(
                """(sel) => {
                    const root = document.querySelector(sel);
                    if (!root) return [];
                    const out = [];
                    root.querySelectorAll('*').forEach(el => {
                        const cs = getComputedStyle(el);
                        if (cs.overflow === 'visible' || cs.overflowX === 'auto') return;
                        if (el.children.length) return;
                        if (!el.textContent.trim()) return;
                        if (el.scrollWidth > el.clientWidth + 2 || el.scrollHeight > el.clientHeight + 2)
                            out.push(`${el.tagName}.${(el.className||'').toString().trim().split(/\\s+/)[0]} clipped ` +
                                     `(${el.scrollWidth}x${el.scrollHeight} in ${el.clientWidth}x${el.clientHeight}) ` +
                                     `"${el.textContent.trim().slice(0,36)}"`);
                    });
                    return out.slice(0, 6);
                }""", sel):
                problems.append(f"[{vp}] {sel} -> {c}")

        broken = page.evaluate(
            """() => [...document.images].filter(i => i.complete && i.naturalWidth === 0)
                   .map(i => i.getAttribute('src'))""")
        for b in broken:
            problems.append(f"[{vp}] broken image: {b}")

        for m in msgs:
            low = m.lower()
            if "error" in low or "failed to load" in low:
                problems.append(f"[{vp}] console {m}")
        page.close()
        browser.close()

    print(f"=== QA REPORT ({vp}) ===")
    if problems:
        for pr in problems:
            print("  !", pr)
    else:
        print("  no issues detected")
    print(f"screenshots -> {outdir}")


if __name__ == "__main__":
    main()
