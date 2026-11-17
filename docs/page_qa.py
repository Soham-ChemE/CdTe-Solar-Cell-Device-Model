#!/usr/bin/env python3
"""Renders and QA for the live page (Playwright for Python, headless Chromium).

  python docs/page_qa.py [--hero] [--qa] [--static] [--lighthouse]

  --hero        assets/hero_dark.webp and assets/hero_light.webp: the hero canvas alone at its final keyframe (the cliff), the
                static image shown when WebGL is missing or software-rendered; docs/build_assets.py embeds the dark one in
                the social preview
  --qa          screenshots in both themes at 1440 px (hero at three scroll positions and every body scene) and 375 px (hero and
                three scenes) into qa/<theme>/, plus console errors, failed requests and horizontal overflow, to qa/qa.json
  --static      the reduced-motion path in both themes: every scene must show its static figure (F1-F7), to qa/<theme>/
  --lighthouse  desktop Lighthouse run (needs the lighthouse CLI on PATH), report to qa/lighthouse.report.{html,json}

Serves docs/ on a local port and loads it with software WebGL and window.__forceGL set, so the live scenes render rather
than the static path (frame timing is therefore not representative). Port of page-qa.mjs / page_qa.py in the sibling
project pages."""
from __future__ import annotations

import argparse
import http.server
import json
import shutil
import socketserver
import subprocess
import threading
import time
from functools import partial
from pathlib import Path

ap = argparse.ArgumentParser()
for f in ("--hero", "--qa", "--static", "--lighthouse"):
    ap.add_argument(f, action="store_true")
A = ap.parse_args()
DOCS = Path(__file__).resolve().parent


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def end_headers(self):
        self.send_header("cache-control", "no-cache")
        super().end_headers()


srv = socketserver.TCPServer(("127.0.0.1", 0), partial(Quiet, directory=str(DOCS)))
PORT = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{PORT}/index.html"

from playwright.sync_api import sync_playwright  # noqa: E402

QA = DOCS / "qa"
report = {"pages": {"index.html": {}}}
SCENES = ["vocT", "cliff", "valley", "fluct", "zno", "design", "solvers", "znse"]


def open_page(browser, theme, w, h, reduced=False, force=True):
    ctx = browser.new_context(viewport={"width": w, "height": h}, device_scale_factor=2 if w < 500 else 1,
                              reduced_motion="reduce" if reduced else "no-preference", color_scheme=theme)
    ctx.add_init_script(("window.__forceGL = true; " if force else "") + f"try {{ localStorage.setItem('theme', '{theme}'); }} catch (e) {{}}")
    page = ctx.new_page()
    errors, failed = [], []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("requestfailed", lambda r: failed.append(r.url))
    page.on("response", lambda r: failed.append(f"{r.status} {r.url}") if r.status >= 400 else None)
    page.goto(BASE, wait_until="networkidle")
    page.wait_for_function("() => window.SITE && window.SITE.ready")
    time.sleep(2.0)
    return ctx, page, errors, failed


def hero_to(page, T):
    page.evaluate("""T => { const tr = document.querySelector('.hero-track'); const y = (tr.offsetHeight - innerHeight) * T;
      if (window.SITE.lenis) window.SITE.lenis.scrollTo(y, { immediate: true, force: true }); window.scrollTo(0, y); if (window.ScrollTrigger) ScrollTrigger.update(); }""", T)
    time.sleep(3.0)


def scene_to(page, name):
    page.evaluate("""s => { const el = document.querySelector(s); const r = el.getBoundingClientRect(); const y = r.top + scrollY - (innerHeight - r.height) / 2;
      if (window.SITE.lenis) window.SITE.lenis.scrollTo(y, { immediate: true, force: true }); window.scrollTo(0, y); if (window.ScrollTrigger) ScrollTrigger.update();
      document.querySelectorAll('.reveal').forEach(e => e.classList.add('in')); }""", f'[data-viz="{name}"]')
    time.sleep(1.0)
    page.evaluate("() => window.__viz && window.__viz.force(1)")
    time.sleep(2.6)


with sync_playwright() as pw:
    browser = pw.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    if A.hero:
        for theme in ("dark", "light"):
            ctx, page, errors, _ = open_page(browser, theme, 1600, 900)
            page.evaluate("""() => { if (window.SITE.heroTimeline) window.SITE.heroTimeline.scrollTrigger.kill(); window.SITE.hero.t = 1;
              document.querySelectorAll('nav, .hero .copy, .hero .readout, .hero .shade, .phases, .hlegend, .cliffcall, .scrollhint, .stats').forEach(e => e.style.visibility = 'hidden'); }""")
            time.sleep(9.0)
            page.query_selector("#heroCanvas").screenshot(path=str(DOCS / "assets" / f"hero_{theme}.png"), timeout=180000)
            print("hero", theme, "errors:", errors)
            ctx.close()
        for theme in ("dark", "light"):  # WebP keeps the bloom gradients without banding at a small size
            try:
                from PIL import Image
                p = DOCS / "assets" / f"hero_{theme}.png"
                Image.open(p).convert("RGB").resize((1280, 720), Image.LANCZOS).save(p.with_suffix(".webp"), quality=80, method=6)
                p.unlink()
            except Exception as e:  # noqa: BLE001
                print("quantise skipped:", e)
    if A.qa:
        for theme in ("dark", "light"):
            qd = QA / theme
            qd.mkdir(parents=True, exist_ok=True)
            ctx, page, errors, failed = open_page(browser, theme, 1440, 900)
            for T in (0, .3, 1):
                hero_to(page, T)
                page.screenshot(path=str(qd / f"index-hero-t{int(T * 100):03d}.png"), timeout=180000)
            for k, name in enumerate(SCENES, 1):
                scene_to(page, name)
                page.screenshot(path=str(qd / f"index-scene{k}-{name}.png"), timeout=180000)
            over = page.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth")
            built = page.evaluate("() => window.__viz ? window.__viz.views.map(v => v.name + ':' + (v.builds || 0)) : []")
            nbytes = page.evaluate("() => performance.getEntriesByType('resource').reduce((a, r) => a + (r.transferSize || r.encodedBodySize || 0), 0) + (performance.getEntriesByType('navigation')[0]?.transferSize || 0)")
            ctx.close()
            mctx, mpage, merr, mfail = open_page(browser, theme, 375, 812)
            for T in (0, 1):
                hero_to(mpage, T)
                mpage.screenshot(path=str(qd / f"index-mobile-375-hero-t{int(T * 100):03d}.png"), timeout=180000)
            for name in ("cliff", "fluct", "design"):
                scene_to(mpage, name)
                mpage.screenshot(path=str(qd / f"index-mobile-375-{name}.png"), timeout=180000)
            mover = mpage.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth")
            mctx.close()
            report["pages"]["index.html"][theme] = {"errors": errors, "failed": failed, "overflowPx1440": over, "scenesBuilt": built,
                                                    "transferBytes": nbytes, "mobileErrors": merr, "mobileFailed": mfail, "overflowPx375": mover}
            print("qa", theme, json.dumps(report["pages"]["index.html"][theme]))
    if A.static:
        for theme in ("dark", "light"):
            qd = QA / theme
            qd.mkdir(parents=True, exist_ok=True)
            ctx, page, errors, failed = open_page(browser, theme, 1440, 900, reduced=True)
            page.screenshot(path=str(qd / "index-reduced-motion-hero.png"), timeout=180000)
            imgs = page.evaluate("() => [...document.querySelectorAll('.viz img.fallback')].map(i => ({ src: (i.getAttribute('src') || '').split('/').pop(), visible: getComputedStyle(i).opacity }))")
            page.evaluate("() => document.querySelector('[data-viz=\"design\"]').scrollIntoView({ block: 'center' })")
            time.sleep(1.5)
            page.screenshot(path=str(qd / "index-reduced-motion-design.png"), timeout=180000)
            ctx.close()
            sctx, spage, serr, sfail = open_page(browser, theme, 1440, 900, force=False)  # software GL without the QA override: static path
            soft = spage.evaluate("() => ({ softGL: window.SITE.softGL, hero: document.querySelector('.hero').className, img: document.querySelector('.hero .fallback').getAttribute('src') })")
            spage.screenshot(path=str(qd / "index-software-gl-hero.png"), timeout=180000)
            sctx.close()
            report["pages"]["index.html"].setdefault(theme, {}).update({"reducedMotionFigures": imgs, "reducedErrors": errors, "reducedFailed": failed,
                                                                        "softwareGL": soft, "softErrors": serr, "softFailed": sfail})
            print("static", theme, json.dumps(imgs), json.dumps(soft), serr, sfail)
    if A.lighthouse:
        lh = shutil.which("lighthouse")
        if not lh:
            print("lighthouse CLI not on PATH; skipped")
        else:
            out = QA / "lighthouse"
            subprocess.run([lh, BASE, "--preset=desktop", "--output=html", "--output=json", f"--output-path={out}", "--quiet",
                            "--chrome-flags=--headless=new --disable-gpu"], check=False)
    browser.close()

if A.qa or A.static:
    QA.mkdir(exist_ok=True)
    try:  # store the screenshots as WebP
        from PIL import Image
        for p in QA.glob("*/*.png"):
            Image.open(p).convert("RGB").save(p.with_suffix(".webp"), quality=78, method=6)
            p.unlink()
    except Exception as e:  # noqa: BLE001
        print("webp conversion skipped:", e)
    (QA / "qa.json").write_text(json.dumps(report, indent=1, ensure_ascii=False))
    print("wrote", QA / "qa.json")
srv.shutdown()
