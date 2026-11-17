/* Page logic that does not need WebGL: the hero readout, the controls and readouts of the interactive sections, the tables,
   and the static path (figures F1-F7 for reduced motion and software or missing WebGL). The 3D scenes (scene.js, body.js) read
   the shared state in window.PAGE every frame. Classic script; runs after site.js. Data: window.CDTE (assets/data.js) and
   assets/cliff.json (fetched once, shared). */
(function () {
  const D = window.CDTE, S = window.SITE || { reduced: true, onFrame() {}, isDark: () => false, steps() {} };
  const $ = id => document.getElementById(id);
  const clamp = (v, a, b) => Math.min(b, Math.max(a, v)), sstep = (a, b, x) => { const t = clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };
  const SUP = { '-': '⁻', '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹' };
  const sup = s => String(s).split('').map(c => SUP[c] || c).join('');
  const minus = s => String(s).replace(/-/g, '−');
  const fx = (v, d) => minus((+v).toFixed(d));
  const sgn = (v, d = 2) => (v > 0 ? '+' : '') + fx(v, d);
  const fmtS = ls => { const S0 = Math.pow(10, ls); if (ls >= 2.5) { const e = Math.floor(ls), m = S0 / Math.pow(10, e); return m.toFixed(1) + ' × 10' + sup(e) + ' cm/s'; } return (S0 < 10 ? S0.toFixed(1) : Math.round(S0).toString()) + ' cm/s'; };
  const fmtX = v => v == null ? '—' : v < 10 ? fx(v, 1) : Math.round(v).toLocaleString('en-US');
  const P = window.PAGE = { v: 0, cliff: null, vt: 'cliff', sigma: 60, valley: 'map', sweep: { i: 6, paused: false }, bump() { this.v++; } };

  /* ---------- hero timeline (shared with scene.js) */
  const prof = D.profile;                                   // descending dEc: +0.10 ... -0.34
  const sweep = prof.filter(p => p.dEc >= -0.30 - 1e-9);    // the sweep ends at the best fit
  P.heroState = T => {
    const m = sstep(.08, .36, T), u = sstep(.42, .88, T), dEc = .10 + (-.30 - .10) * u;
    let near = sweep[0]; for (const p of sweep) if (Math.abs(p.dEc - dEc) < Math.abs(near.dEc - dEc)) near = p;
    return { T, m, u, dEc, near, ro: sstep(.30, .42, T), call: sstep(.9, .97, T), phase: T < .2 ? 0 : T < .42 ? 1 : 2 };
  };
  const TAG = { '0.1': 'the published model’s spike', '0.06': 'the best spike', '-0.02': 'nearly flat', '-0.1': 'a shallow cliff', '-0.14': 'a shallow cliff', '-0.18': 'a shallow cliff', '-0.22': 'the MOCVD XPS value', '-0.26': 'the shallowest cliff the data allow', '-0.3': 'best fit: a passivated cliff', '-0.34': 'a deeper cliff' };
  // profile mini-plot
  const px = d => 12 + (d + .34) / .44 * 216, py = x => 62 - (Math.log10(Math.max(x, .1)) + 1) / 4 * 56;
  const svg = $('roProfile');
  if (svg) {
    const asc = [...prof].sort((a, b) => a.dEc - b.dEc);
    svg.innerHTML = `<line class="lim" x1="8" x2="232" y1="${py(6.2).toFixed(1)}" y2="${py(6.2).toFixed(1)}"/><polyline class="pl" points="${asc.map(p => px(p.dEc).toFixed(1) + ',' + py(p.dchi2).toFixed(1)).join(' ')}"/>` +
      asc.map(p => `<circle class="pt" r="2" cx="${px(p.dEc).toFixed(1)}" cy="${py(p.dchi2).toFixed(1)}"/>`).join('') + `<circle id="roCur" class="cur" r="5"/>`;
  }
  const ro = { box: $('heroReadout'), dec: $('roDec'), tag: $('roTag'), s: $('roS'), v: $('roV'), x: $('roX'), cur: $('roCur') };
  const phases = [...document.querySelectorAll('.phases li')], call = $('cliffCall'), copy = document.querySelector('.hero .copy');
  let lastNear = null, lastT = -1;
  function heroDOM(T) {
    if (Math.abs(T - lastT) < 1e-4) return; lastT = T; const h = P.heroState(T);
    if (ro.box && !document.querySelector('.hero.no-webgl')) ro.box.style.opacity = h.ro.toFixed(3);
    phases.forEach((li, i) => li.classList.toggle('on', i === h.phase));
    if (call) { call.style.opacity = h.call.toFixed(3); call.style.transform = `translate(0,${(10 - 10 * h.call).toFixed(1)}px)`; }
    if (h.near !== lastNear && ro.dec) {
      const p = h.near; lastNear = p;
      ro.dec.textContent = sgn(p.dEc) + ' eV'; ro.tag.textContent = TAG[String(p.dEc)] || '';
      ro.s.textContent = fmtS(p.logS); ro.v.textContent = Math.round(p.voc) + ' mV'; ro.x.textContent = fmtX(p.dchi2);
      ro.box.classList.toggle('good', p.dchi2 <= 6.2);
      if (ro.cur) { ro.cur.setAttribute('cx', px(p.dEc).toFixed(1)); ro.cur.setAttribute('cy', py(p.dchi2).toFixed(1)); }
    }
  }
  heroDOM(S.reduced ? 1 : 0);
  S.onFrame(() => heroDOM(S.hero ? S.hero.t : 1));
  if (S.reduced && copy) copy.style.opacity = 1;
  if (S.reduced && call) call.hidden = true;   // the final keyframe is shown at once; the headline already says it

  /* ---------- static path: figures F1-F7 for reduced motion and software or missing WebGL */
  const heroFb = document.querySelector('.hero .fallback');
  const heroImg = () => { if (heroFb && document.querySelector('.hero.no-webgl')) heroFb.src = 'assets/hero_' + (S.isDark() ? 'dark' : 'light') + '.webp'; };
  const staticFigs = () => document.querySelectorAll('.viz img.fallback[data-src]').forEach(i => { if (!i.getAttribute('src')) i.src = i.dataset.src; });
  if (S.reduced) { document.documentElement.classList.add('viz-static'); staticFigs(); }
  heroImg(); document.addEventListener('themechange', heroImg);
  // if three.js never arrives (blocked CDN, module error), show the hero render after a grace period
  if (!S.softGL) setTimeout(() => { if (!window.__heroReady) { const h = document.querySelector('.hero'); if (h) { h.classList.add('no-webgl'); heroImg(); if (ro.box) ro.box.style.opacity = 1; } } }, 8000);
  if (!S.reduced) setTimeout(() => { if (!window.__viz || !window.__viz.S) { document.documentElement.classList.add('viz-static'); staticFigs(); } }, 9000);

  /* ---------- reveals by IntersectionObserver as well (instant jumps, restored scroll positions) */
  if ('IntersectionObserver' in window) { const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } })); document.querySelectorAll('.reveal').forEach(el => io.observe(el)); }

  /* ---------- 01 Voc(T) model toggle */
  const VT = { cliff: 'best cliff, S = ', spike: 'best spike, S = ', published: 'published spike, S on the ridge = ' };
  function setVT(k) {
    P.vt = k; P.bump(); const m = D.vocT.models.find(x => x.key === k);
    document.querySelectorAll('[data-vt]').forEach(b => { const on = b.dataset.vt === k; b.classList.toggle('on', on); b.setAttribute('aria-pressed', on); });
    $('vtDec').textContent = sgn(m.dEc) + ' eV'; $('vtName').textContent = VT[k] + fmtS(m.logS); $('vtX').textContent = fmtX(m.dchi2); $('vtLight').textContent = m.X.toFixed(2) + ' sun';
  }
  document.querySelectorAll('[data-vt]').forEach(b => b.addEventListener('click', () => setVT(b.dataset.vt))); setVT('cliff');

  /* ---------- 02 the cliff, live */
  const dS = $('dEcSlider'), sS = $('sSlider');
  P.cliffData = fetch('assets/cliff.json').then(r => r.json()).then(j => { P.cliffJSON = j; return j; }).catch(() => null);
  const lerpRow = (rows, ls, cols) => { let k = 1; while (k < rows.length - 1 && rows[k][0] < ls) k++; const a = rows[k - 1], b = rows[k], t = clamp((ls - a[0]) / ((b[0] - a[0]) || 1), 0, 1); return cols.map(c => a[c] == null || b[c] == null ? null : a[c] + (b[c] - a[c]) * t); };
  function evalCliff(J, i, ls) {
    const o = J.offsets[i], fine = o.fine, mp = o.map, lo = fine[0][0], hi = fine[fine.length - 1][0];
    const onGrid = mp.find(r => Math.abs(r[0] - ls) < .013);
    if (Math.abs(ls - o.ridge) < .006 && o.ridge_sim) { const [voc, ff, dx] = o.ridge_sim; return { status: 'in', voc, ff, dchi2: dx, ridge: true, o }; }   // simulated directly on the ridge
    if (ls >= lo - 1e-9 && ls <= hi + 1e-9) { const [voc, ff, dx] = lerpRow(fine, ls, [1, 2, 3]); return { status: 'in', voc, ff, dchi2: Math.max(0, dx), grid: onGrid, o }; }
    if (ls <= mp[mp.length - 1][0] + 1e-9) { const [voc, ff] = lerpRow(mp, ls, [1, 2]); return { status: 'partial', voc, ff, dchi2: null, grid: onGrid, o }; }
    return { status: 'out', voc: null, ff: null, dchi2: null, o };
  }
  const verdict = x => x == null ? '' : x <= 2.3 ? 'inside the 68 % region' : x <= 6.2 ? 'inside the 95 % region' : 'excluded at 95 %';
  function updCliff(src) {
    const J = P.cliffJSON; if (!J || !dS) return;
    const i = +dS.value, ls = +sS.value, o = J.offsets[i], r = evalCliff(J, i, ls);
    P.cliff = { i, dEc: o.dEc, logS: ls, ridge: o.ridge, voc: r.voc, ff: r.ff, dchi2: r.dchi2, status: r.status }; P.bump();
    $('dEcOut').textContent = sgn(o.dEc) + ' eV'; dS.setAttribute('aria-valuetext', sgn(o.dEc) + ' eV, ' + (o.dEc < 0 ? 'cliff' : 'spike'));
    $('sOut').innerHTML = '10<sup>' + ls.toFixed(2) + '</sup> ≈ ' + fmtS(ls); sS.setAttribute('aria-valuetext', 'log S ' + ls.toFixed(2) + ', ' + fmtS(ls));
    $('lvV').textContent = r.voc == null ? '—' : r.voc.toFixed(1) + ' mV'; $('lvF').textContent = r.ff == null ? '—' : r.ff.toFixed(1) + ' %';
    $('lvX').textContent = r.dchi2 == null ? '—' : fmtX(r.dchi2);
    $('lvXv').textContent = r.status === 'in' ? verdict(r.dchi2) : r.status === 'partial' ? 'not evaluated here' : 'no simulation here';
    const st = $('lvStatus'); st.className = 'status' + (r.status === 'in' ? '' : r.status === 'partial' ? ' partial' : ' out');
    st.querySelector('span').textContent = r.status === 'in' ? 'Inside the data' : r.status === 'partial' ? 'V_oc and FF only' : 'Outside the data';
    const where = `ΔE<sub>c</sub> ${sgn(o.dEc)} eV, log₁₀ S ${ls.toFixed(2)}`;
    $('lvCite').innerHTML = r.ridge ? `ident_profile.csv · ${where} · the best S for this offset, simulated directly` : r.status === 'in' ? `ident_fine_scan.csv · ${where} · ${r.grid ? 'a simulated point (ident_map.csv)' : 'PCHIP in log S between simulated points'}` :
      r.status === 'partial' ? `ident_map.csv · ${where} · 1-sun V<sub>oc</sub> below 700 mV, so the temperature series and χ² were not run; V<sub>oc</sub> and FF linear between simulated points` :
        `outside the data · ${where} · this offset was simulated up to log₁₀ S ${o.map[o.map.length - 1][0].toFixed(1)}`;
    document.querySelectorAll('.presets [data-p]').forEach(b => b.classList.toggle('on', Math.abs(+b.dataset.p - o.dEc) < 1e-6 && Math.abs(ls - o.ridge) < .03));
    drawMap();
  }
  function setCliff(dEc, ls) { const J = P.cliffJSON; if (!J) return; const i = J.offsets.findIndex(o => Math.abs(o.dEc - dEc) < 1e-6); if (i >= 0) dS.value = i; sS.value = (ls ?? J.offsets[+dS.value].ridge).toFixed(2); updCliff(); }
  if (dS) {
    dS.addEventListener('input', () => updCliff()); sS.addEventListener('input', () => updCliff());
    // arrow keys move S in 0.05-decade steps, Page Up/Down in half decades (the slider itself has 0.01 resolution for the presets)
    sS.addEventListener('keydown', e => { const st = { ArrowRight: .05, ArrowUp: .05, ArrowLeft: -.05, ArrowDown: -.05, PageUp: .5, PageDown: -.5 }[e.key]; if (st == null) return; e.preventDefault(); sS.value = clamp(+sS.value + st, 0, 6).toFixed(2); updCliff(); });
    document.querySelectorAll('.presets [data-p]').forEach(b => b.addEventListener('click', () => setCliff(+b.dataset.p)));
    const rb = document.querySelector('.presets [data-ridge]'); if (rb) rb.addEventListener('click', () => { const J = P.cliffJSON; if (J) { sS.value = J.offsets[+dS.value].ridge.toFixed(2); updCliff(); } });
    P.cliffData.then(J => { if (J) setCliff(-0.30, J.offsets.find(o => Math.abs(o.dEc + .3) < 1e-6).ridge); });
  }
  // the (dEc, log S) map
  const cv = $('cliffMap'), MX = { l: 30, r: 8, t: 8, b: 22 };
  const mapX = d => MX.l + (d + .37) / .5 * (340 - MX.l - MX.r), mapY = ls => 190 - MX.b - ls / 6.2 * (190 - MX.t - MX.b), CW = .028 / .5 * (340 - MX.l - MX.r);
  function drawMap() {
    const J = P.cliffJSON; if (!cv || !J) return; const dpr = Math.min(2, devicePixelRatio || 1); if (cv.width !== 340 * dpr) { cv.width = 340 * dpr; cv.height = 190 * dpr; }
    const g = cv.getContext('2d'); g.setTransform(dpr, 0, 0, dpr, 0, 0); g.clearRect(0, 0, 340, 190);
    const css = getComputedStyle(document.documentElement), acc = css.getPropertyValue('--c-cyan').trim(), mut = css.getPropertyValue('--muted').trim(), ink = css.getPropertyValue('--ink').trim(), line = css.getPropertyValue('--line').trim(), hot = css.getPropertyValue('--c-hot').trim();
    g.font = '10px -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif'; g.fillStyle = mut; g.strokeStyle = line; g.lineWidth = 1;
    [0, 2, 4, 6].forEach(t => { const y = mapY(t); g.beginPath(); g.moveTo(MX.l, y); g.lineTo(340 - MX.r, y); g.stroke(); g.fillText(t === 0 ? '1' : '10' + sup(t), 4, y + 3); });
    [-0.3, -0.2, -0.1, 0, 0.1].forEach(d => g.fillText(minus(d.toFixed(1)), mapX(d) - 9, 186));
    for (const o of J.offsets) {
      const x = mapX(o.dEc) - CW / 2;
      // V_oc/FF-only stretch: hatched
      const fhi = o.fine[o.fine.length - 1][0], mhi = o.map[o.map.length - 1][0];
      if (mhi > fhi) { g.save(); g.beginPath(); g.rect(x, mapY(mhi), CW, mapY(fhi) - mapY(mhi)); g.clip(); g.strokeStyle = mut; g.globalAlpha = .45; for (let k = -40; k < 200; k += 5) { g.beginPath(); g.moveTo(x - 2, mapY(fhi) - k); g.lineTo(x + CW + 2, mapY(fhi) - k - CW); g.stroke(); } g.restore(); }
      for (let k = 0; k < o.fine.length - 1; k++) {
        const a = o.fine[k], b = o.fine[k + 1], q = clamp(1 - Math.log10(Math.max(a[3], .3) / .3) / 4, 0, 1);
        g.globalAlpha = .08 + .92 * Math.pow(q, 1.6); g.fillStyle = acc; g.fillRect(x, mapY(b[0]), CW, mapY(a[0]) - mapY(b[0]) + .6);
      }
      g.globalAlpha = 1;
    }
    const c = P.cliff; if (c) { const x = mapX(c.dEc), y = mapY(c.logS); g.strokeStyle = c.status === 'out' ? mut : ink; g.lineWidth = 1.2; g.beginPath(); g.moveTo(x, MX.t); g.lineTo(x, 190 - MX.b); g.moveTo(MX.l, y); g.lineTo(340 - MX.r, y); g.stroke(); g.fillStyle = hot; g.beginPath(); g.arc(x, y, 4, 0, 7); g.fill(); }
  }
  if (cv) {
    cv.addEventListener('click', e => { const J = P.cliffJSON; if (!J) return; const rc = cv.getBoundingClientRect(), x = (e.clientX - rc.left) / rc.width * 340, y = (e.clientY - rc.top) / rc.height * 190;
      let best = 0; J.offsets.forEach((o, i) => { if (Math.abs(mapX(o.dEc) - x) < Math.abs(mapX(J.offsets[best].dEc) - x)) best = i; });
      dS.value = best; sS.value = clamp((190 - MX.b - y) / (190 - MX.t - MX.b) * 6.2, 0, 6).toFixed(2); updCliff(); });
    document.addEventListener('themechange', drawMap);
  }

  /* ---------- 03 valley steps */
  const VL = { map: ['The map', 'Δχ² over (ΔE<sub>c</sub>, log S)'], ridge: ['The ridge', '12.9 decades of S per eV'], floor: ['The floor', '95 %: −0.335 to −0.277 eV'], xps: ['The XPS band', '−0.32 eV inside the 68 % region'], spike: ['The published spike', 'Δχ² ≈ 589'] };
  const vlab = $('valLabel');
  if (S.steps) S.steps('#valSteps .step', k => { P.valley = k; P.bump(); if (vlab && VL[k]) vlab.innerHTML = `<b>${VL[k][0]}</b>${VL[k][1]}`; });

  /* ---------- 04 fluctuation gate */
  const F = D.fluct, sg = $('sigSlider');
  function updSig() {
    const s = +sg.value, k = F.sigma.indexOf(s), row = F.dchi2[k]; P.sigma = s; P.bump();
    let bi = 0; row.forEach((v, i) => { if (v < row[bi]) bi = i; }); const si = F.dEc.findIndex(d => Math.abs(d - .06) < 1e-6);
    $('sigOut').textContent = s + ' meV'; sg.setAttribute('aria-valuetext', s + ' meV');
    $('sigRead').innerHTML = `At σ = ${s} meV the best offset is ${sgn(F.dEc[bi])} eV (Δχ² ${fmtX(row[bi])}, S = ${fmtS(F.logS[k][bi])}); the best spike, +0.06 eV, sits at Δχ² ${fmtX(row[si])}, above the floor of ${Math.round(F.spike_min)}.`;
  }
  if (sg) { sg.addEventListener('input', updSig); updSig(); }
  const gt = $('gateTable');
  if (gt) { const mx = 600; gt.innerHTML = [['S free', F.spike.free], ['S ≥ 1 cm/s', F.spike.S1], ['S ≥ 10 cm/s', F.spike.S10]].map(([n, v]) => `<tr><td>${n}</td>${v.map(x => `<td class="num"><span class="bar" style="width:${(x / mx * 90).toFixed(0)}px"></span>${Math.round(x)}</td>`).join('')}</tr>`).join(''); }

  /* ---------- 05 ZnO table, 06 badges, 07 solver tables */
  const zt = $('znoTable');
  if (zt) zt.innerHTML = D.zno.series.map(r => `<tr><td>${r.x.toFixed(2)}</td><td class="num">${sgn(r.dEc)}</td><td class="num">${Math.round(r.voc_best)}</td><td class="num">${r.voc_model.toFixed(1)}</td><td class="num">${r.eta_best.toFixed(1)} / ${r.eta_avg.toFixed(1)}</td></tr>`).join('');
  if ($('bdScaps')) { $('bdScaps').textContent = D.design.scaps.toFixed(2) + ' %'; $('bdSesame').textContent = D.design.cons.toFixed(2) + ' %'; }
  const lt = $('lightTable');
  if (lt) lt.innerHTML = D.solvers.table.map(r => `<tr><td>${r[0]}</td><td>${r[1]}</td>${r.slice(2).map(c => `<td class="num">${minus(c)}</td>`).join('')}</tr>`).join('');
  const SW = D.solvers.dark, VV = SW[0].V, swb = $('swBody'), SWC = ['--c-hot', '--c-cyan', '--c-violet', '--c-green'];
  const fJ = j => j >= 1 ? j.toFixed(2) : j.toExponential(2).replace('e', '×10^').replace(/\^([+-]?)(\d+)/, (m, s, d) => sup((s === '-' ? '-' : '') + +d)).replace('-', '−');
  function updSweep() {
    const V = VV[P.sweep.i]; P.sweep.V = V; P.bump(); if (!swb) return; $('swV').textContent = V.toFixed(2) + ' V';
    swb.innerHTML = SW.map((c, k) => { const j = c.V.indexOf(V); if (j < 0) return ''; return `<tr><td><span class="sw-d" style="background:var(${SWC[k]})"></span>${sgn(c.dEc)}</td><td class="num">${fJ(c.scaps[j])}</td><td class="num">${fJ(c.sesame[j])}</td><td class="num">${(c.sesame[j] / c.scaps[j]).toFixed(3)}</td></tr>`; }).join('');
  }
  updSweep();
  const pb = $('swPause'); let swVisible = false, dir = 1;
  if (pb) pb.addEventListener('click', () => { P.sweep.paused = !P.sweep.paused; pb.setAttribute('aria-pressed', P.sweep.paused); pb.textContent = P.sweep.paused ? 'Resume sweep' : 'Pause sweep'; });
  const swEl = document.querySelector('[data-viz="solvers"]');
  if (swEl && 'IntersectionObserver' in window) new IntersectionObserver(es => es.forEach(e => swVisible = e.isIntersecting)).observe(swEl);
  if (!S.reduced) setInterval(() => { if (!swVisible || P.sweep.paused) return; let i = P.sweep.i + dir; if (i >= VV.length || i < 0) { dir = -dir; i = P.sweep.i + dir; } P.sweep.i = i; updSweep(); }, 850);
  else { P.sweep.paused = true; if (pb) pb.hidden = true; }
})();
