# QA for the live page

Run with `docs/page_qa.py --hero --qa --static` (Playwright for Python, headless Chromium). The page is served from
`docs/` as GitHub Pages serves it and loaded with software WebGL and `window.__forceGL`, so the live scenes render (frame
timing is therefore not representative). Screenshots are stored as WebP.

| Theme | Console errors (1440) | Failed requests (1440) | Horizontal overflow (1440) | Console errors (375) | Failed requests (375) | Horizontal overflow (375) | Transfer (bytes) |
|---|---|---|---|---|---|---|---|
| dark | 0 | 0 | 0 px | 0 | 0 | 0 px | 614,643 |
| light | 0 | 0 | 0 px | 0 | 0 | 0 px | 614,643 |

Every scene was built lazily and, where the run scrolled far past it, disposed and rebuilt (`scenesBuilt` in `qa.json`).
Static path: with reduced motion every body scene shows its figure (F1-F7); with a software renderer the hero shows
`assets/hero_<theme>.webp` and three.js is not loaded. Both were checked in both themes with no console errors.

Files in `dark/` and `light/`: `index-hero-t000/030/100` (hero at the start, mid-morph and the end of the track),
`index-scene1..8-<name>` (every body scene at 1440 px), `index-mobile-375-*` (375 px hero and three scenes),
`index-reduced-motion-*` and `index-software-gl-hero`.
