# tools/

Build-time helpers used to restructure the newsletter. They are **not**
shipped to the browser.

| script | role |
|---|---|
| `reorder.py` | Extracts every top-level `<section>` from `index.html`, splits the legacy "triple feature" block, then rewrites the file in the canonical 8-chapter order with the chapter dividers inserted. Section markup is moved **verbatim**. |
| `shots.py`   | Desktop screenshots of the chapter dividers (visual QA). |
| `mobile.py`  | Mobile screenshots + horizontal-overflow audit. |

Run from the project root with a static server on :8080 for the screenshot
scripts:

```bash
python3 -m http.server 8080 &
python3 tools/reorder.py      # rewrites index.html
python3 tools/shots.py        # /tmp/shots/chapitre-*.png
python3 tools/mobile.py
```
