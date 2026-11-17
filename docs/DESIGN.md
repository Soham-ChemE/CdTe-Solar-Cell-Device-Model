# Design notes for the live page

The engineering rationale behind `docs/index.html` and `docs/assets/`. The page uses the same design system as Soham
Kavathekar's other project pages (`site.css`, `site.js`, `three-kit.js`, `viz.js`): a pinned hero with one scrubbed GSAP
timeline, Lenis synced to ScrollTrigger, three.js 0.186 with bloom on the hero only, one shared forward renderer
scissor-clipped to every body figure, per-theme palettes and rendering constants (light mode: ACES exposure 0.82, bloom
only on HDR pixels), render-on-demand, and a static path for reduced motion and software or missing WebGL. Pinned CDN
builds: three.js 0.186.1, GSAP 3.15.0, Lenis 1.3.27.

## Data

Every number the page draws comes from `docs/build_assets.py`, which reads the committed CSVs and writes
`assets/data.js` (hero profile, F1 curves, fluctuation gate, ZnO series, design staircase, solver cross-check, ZnSe map)
and `assets/cliff.json` (the identifiability map and fine scan, fetched once and shared by "The cliff, live" and the
valley). Text quotes `README.md` and `docs/CLAIMS.md`; limits and caveats stay in `CLAIMS.md`.

## Hero (`assets/scene.js`)

The 21.4 % cell as a stack of deformable slabs in the true layer order (thicknesses stylised): glass, FTO, ZnO, the
graded As-doped CdSeTe → CdTe absorber and the back contact. Photons enter through the glass and are absorbed mostly near
the front, each creating an electron-hole pair; electrons drift to the ZnO, holes to the back. As the page scrolls, each
slab's top and bottom faces move onto E<sub>c</sub>(x) and E<sub>v</sub>(x), so the stack becomes its own band diagram,
with the band edges as ribbons and fat lines. Then the conduction-band step at the ZnO/CdSeTe interface moves from the
published +0.10 eV spike to the fitted −0.30 eV cliff; the readout shows the nearest simulated offset with its ridge S,
1-sun V<sub>oc</sub> and Δχ² (`ident_profile.csv`), and electrons reaching the interface recombine (a spark along the
buffer-CB → absorber-VB path) with a probability that grows with log S on the ridge. Band shapes away from the interface
(bending, grading, back barrier) are schematic; the step and S are data. The stage mounts when the hero track nears the
viewport and is disposed (with every listener) when it is far away.

## Body scenes (`assets/body.js`), with the static figure each one falls back to

| Placeholder | Scene | Fallback |
|---|---|---|
| `vocT` | 13 measured V<sub>oc</sub>(T) points in three lanes against the best cliff, best spike and published spike; residual stems | F1 |
| `cliff` | the front interface driven by the sliders; spark rate follows the model's V<sub>oc</sub> loss at the chosen point | the 2D map and readouts stay |
| `valley` | Δχ² ribbons per simulated offset, a translucent skin between them for reading, the Δχ² = 6.2 plane, ridge, best fit, published spike, XPS band; camera driven by the sticky steps | F2 |
| `fluct` | Gaussian band-gap domains at the chosen σ and the profile Δχ² against ΔE<sub>c</sub>, with the spike's floor at 447 | F3 |
| `zno` | a Cu-doped and an As-doped ZnO interface with sparks; V<sub>oc</sub> of the Mg series, measured and model | F4 |
| `design` | the design staircase from the calibrated cell to the conservative design, with the penalised-baseline plane | F5 |
| `solvers` | dark J-V, SCAPS points on Sesame ribbons, a sweeping voltage cursor | F6 |
| `znse` | efficiency against the ZnSe offset for eight variants, with the DFT band | F7 |

Scenes are built when they come within one viewport of the screen and their GPU resources are released when they are
more than two and a half viewports away (`viz.js`); the shared renderer caps the pixel ratio at 2 (1.5 on phones) and
renders only when something changed. Narrow placeholders widen the camera's field of view so the designed horizontal
extent stays in frame.

## QA (`docs/page_qa.py`)

Playwright for Python, headless Chromium with software WebGL and `window.__forceGL` (frame timing not representative):
`--hero` renders `assets/hero_dark.webp` and `hero_light.webp` (the no-WebGL hero), `--qa` writes both-theme screenshots at
1440 px and 375 px with console, failed-request and overflow checks to `docs/qa/`, `--static` checks the reduced-motion and
software-renderer paths. `python docs/build_assets.py` then rebuilds the data and the social preview with the hero render.

## Robustness (after the Safari report of 17 November 2026)

The first 3D release left Safari with blank body scenes and empty tables. The cause was a stale cached `assets/data.js`
from the previous page (GitHub Pages serves every file with `max-age=600`) running under the new `page.js`. The new script
threw at the first missing key, so no table was filled and `body.js` stopped registering scenes. Nothing on the page could
then fall back to a figure. Reproduced in Playwright WebKit by serving the old `data.js` under the new page. Since then:

- **No version skew.** Every local asset URL carries `?v=<hash of all assets>`, written by `build_assets.py`, including
  the module imports between `scene.js`, `body.js`, `viz.js` and `three-kit.js`. A browser can no longer combine files
  from two releases.
- **Failure is local.**
  - Every section of `page.js` runs in its own guarded block.
  - Every frame callback is isolated: one that throws is removed, and the others keep running.
  - Each scene's registration, build, update and render is guarded. A scene that fails is disposed and shows its static
    figure (F1–F7) in place.
  - A scene that never registers, or a module that fails to load, is swept to its figure as well.
  - The hero falls back to its rendered image.
- **Tables do not need JavaScript.** `build_assets.py` writes the table rows into `index.html`; `page.js` only refreshes
  them, and drives the voltage sweep.
- **Bloom only with float render targets.** `createStage` skips the post-processing chain when the GPU cannot render to
  half-float targets.
- **Labels.** In-scene labels are drawn bold with a contrasting halo at 3× resolution and are exempt from tone mapping. The
  hero draws them in an overlay pass after bloom. The left wash behind the headline fades out with it.

QA runs in Chromium and WebKit (`page_qa.py --engine webkit`, screenshots in `qa/webkit/`).
