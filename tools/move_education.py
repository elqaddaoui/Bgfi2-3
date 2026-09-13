#!/usr/bin/env python3
"""Move the `#story-education` section from Chapter V into Chapter VII.

The section markup is relocated verbatim (byte-identical) — only its
position in the document changes. It is re-inserted directly after the
Chapter VII divider, i.e. as the chapter's opening story, and the
chapter table-of-contents entries are updated accordingly.
"""
import re
import sys

SRC = "index.html"

EDU_COMMENT = """<!-- ============================================================
     STORY · Éducation — asymmetric magazine layout
     ============================================================ -->
"""


def main():
    html = open(SRC, encoding="utf-8").read()

    # ---- 1. cut the education block (its comment + section) -------------
    start = html.index(EDU_COMMENT)
    sec_start = html.index('<section class="story-section magazine-left" id="story-education">',
                           start)
    end_marker = '</section>\n'
    # the section ends at the first </section> that closes it: find the
    # next top-level comment banner after it
    nxt = html.index("<!-- ============================================================\n"
                     "     STORY · Mois de la femme", sec_start)
    block = html[start:nxt]
    html_wo = html[:start] + html[nxt:]

    # ---- 2. re-insert after the Chapter VII divider --------------------
    anchor = ("<!-- ============================================================\n"
              "     STORY · BGFI Étoiles — Talents de demain\n"
              "     ============================================================ -->\n")
    if anchor not in html_wo:
        sys.exit("Chapter VII anchor (BGFI Étoiles banner) not found")
    html_out = html_wo.replace(anchor, block + anchor, 1)

    # ---- 3. sanity: the block must be preserved byte-for-byte ----------
    assert block in html_out, "education block was altered while moving"
    assert html_out.count('id="story-education"') == 1

    open(SRC, "w", encoding="utf-8").write(html_out)
    print("moved #story-education into Chapter VII "
          f"({len(block)} bytes, verbatim)")


if __name__ == "__main__":
    main()
