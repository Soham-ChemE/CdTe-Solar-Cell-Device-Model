# QA for the live page

Run with `python docs/page_qa.py --hero --qa --static` (Chromium) and `--qa --static --engine webkit` (WebKit), Playwright
for Python. The page is served from `docs/` as GitHub Pages serves it. Chromium uses software WebGL with `window.__forceGL`
so the live scenes render (frame timing is therefore not representative); WebKit renders with its own WebGL. Screenshots are
stored as WebP: Chromium in `dark/` and `light/`, WebKit in `webkit/dark/` and `webkit/light/`.

| Engine | Theme | Console errors | Failed requests | Body scenes (1440 px) | Tables | Horizontal overflow (1440 / 375) | Errors at 375 px | Reduced motion: figures shown |
|---|---|---|---|---|---|---|---|---|
| Chromium | dark | 0 | 0 | 8/8 live | all filled | 0 / 0 px | 0 | 8/8 |
| Chromium | light | 0 | 0 | 8/8 live | all filled | 0 / 0 px | 0 | 8/8 |
| WebKit | dark | 0 | 0 | 8/8 live | all filled | 0 / 0 px | 0 | 8/8 |
| WebKit | light | 0 | 0 | 8/8 live | all filled | 0 / 0 px | 0 | 8/8 |

The scenes are built when they come near the viewport, disposed when they are far from it, and rebuilt on return
(`scenesBuilt` in `qa.json`). With a software renderer (Chromium) the hero shows `assets/hero_<theme>.webp` and three.js is
not loaded. Firefox was not run: Playwright's Firefox build exited on launch on this machine.

Fail-safe checks, run in WebKit against the built page:
- A stale `data.js` from the previous release, served under the new page (the Safari report's failure, reproduced): every
  scene that lacked its data showed its static figure, the other scenes kept working, and all four tables stayed filled
  because they are written into the HTML. With the versioned asset URLs this combination can no longer occur.
- One scene broken on purpose: only that scene fell back to its figure; the others rendered and every table was filled.
- `cliff.json` blocked: the valley fell back to F2; every other scene and table was unaffected.

Files per theme: `index-hero-t000/030/100` (hero at the start, mid-morph and the end of the track),
`index-scene1..8-<name>` (every body scene at 1440 px), `index-mobile-375-*`, `index-reduced-motion-*` and
`index-software-gl-hero`.
