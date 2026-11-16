/* Hero: the ZnO/CdSeTe band diagram, scrubbed by scroll from the published +0.10 eV spike to the best-fit -0.30 eV cliff.
   The step moves continuously; the readout and the mini profile report the nearest simulated offset (window.CDTE.profile,
   built by docs/build_assets.py from optionA/sesame/kujovic/ident/). Classic script, loaded after site.js. */
(function () {
  const S = window.SITE, D = window.CDTE; if (!S || !D) return;
  const $ = id => document.getElementById(id);
  const svg = $('band'); if (!svg) return;
  const NS = 'http://www.w3.org/2000/svg';
  const P = D.profile.slice().sort((a, b) => b.dEc - a.dEc);          // +0.10 ... -0.34
  const START = 0.10, END = D.best.dEc;                               // published spike -> best fit
  const EY = 100, Y0 = 200, XI = 160;                                  // px per eV, absorber CB at the interface, interface x
  const zno = $('zCB'), step = $('zStep'), dot = $('zDot'), rec = $('zRec'), lab = $('zLab'), sub = $('zSub');
  const sup = n => String(n).replace(/[-0-9]/g, c => '⁻⁰¹²³⁴⁵⁶⁷⁸⁹'['-0123456789'.indexOf(c)]);
  const fmtS = lg => { const v = Math.pow(10, lg); if (v < 100) return v.toFixed(1) + ' cm/s'; const e = Math.floor(lg), m = v / Math.pow(10, e); return m.toFixed(1) + ' × 10' + sup(e) + ' cm/s'; };
  const fmtE = d => (d > 0 ? '+' : d < 0 ? '−' : '') + Math.abs(d).toFixed(2) + ' eV';
  // mini profile: log10(dchi2) against dEc
  const prof = $('roProfile');
  const px = d => 12 + (d + 0.36) / 0.48 * 216, py = c => 60 - (Math.log10(Math.max(c, 0.1)) + 1) / 4 * 54;
  if (prof) {
    const byE = P.slice().sort((a, b) => a.dEc - b.dEc);
    const line = document.createElementNS(NS, 'polyline'); line.setAttribute('points', byE.map(p => px(p.dEc) + ',' + py(p.dchi2)).join(' ')); line.setAttribute('class', 'pl'); prof.appendChild(line);
    const lim = document.createElementNS(NS, 'line'); lim.setAttribute('x1', 8); lim.setAttribute('x2', 232); lim.setAttribute('y1', py(6.2)); lim.setAttribute('y2', py(6.2)); lim.setAttribute('class', 'lim'); prof.appendChild(lim);
    byE.forEach(p => { const c = document.createElementNS(NS, 'circle'); c.setAttribute('cx', px(p.dEc)); c.setAttribute('cy', py(p.dchi2)); c.setAttribute('r', 3); c.setAttribute('class', 'pt'); prof.appendChild(c); });
    const cur = document.createElementNS(NS, 'circle'); cur.setAttribute('r', 6.5); cur.setAttribute('class', 'cur'); cur.id = 'roCur'; prof.appendChild(cur);
  }
  let last = null, lastSnap = null;
  function draw(t) {
    const u = Math.max(0, Math.min(1, (t - 0.05) / 0.75)), e = u < .5 ? 2 * u * u : 1 - Math.pow(-2 * u + 2, 2) / 2;
    const d = START + (END - START) * e, yi = Y0 - d * EY;
    const snap = P.reduce((a, b) => Math.abs(b.dEc - d) < Math.abs(a.dEc - d) ? b : a);
    const cliff = d < -0.005, col = cliff ? 'var(--c-green)' : 'var(--c-hot)';
    zno.setAttribute('d', `M90,250 L${XI},${yi.toFixed(1)}`);
    step.setAttribute('d', `M${XI},${Y0} L${XI},${yi.toFixed(1)}`); step.style.stroke = col;
    dot.setAttribute('cy', yi.toFixed(1)); dot.style.fill = col;
    rec.setAttribute('d', `M${XI - 3},${(yi + 5).toFixed(1)} C${XI - 34},${(yi + 50).toFixed(1)} ${XI - 34},300 ${XI - 3},337`); rec.style.stroke = col;
    rec.style.strokeWidth = (1.2 + snap.logS * 0.55).toFixed(2); rec.style.opacity = (0.35 + snap.logS * 0.1).toFixed(2);
    lab.setAttribute('y', (yi + (cliff ? 18 : -10)).toFixed(1)); sub.setAttribute('y', (yi + (cliff ? 36 : 8)).toFixed(1));
    lab.textContent = fmtE(d) + (cliff ? ' cliff' : Math.abs(d) < 0.005 ? ' flat' : ' spike'); lab.style.fill = col;
    sub.textContent = Math.abs(d - START) < 0.002 ? 'published model' : Math.abs(d - END) < 0.002 ? 'best fit, passivated' : '';
    if (snap !== lastSnap) {
      lastSnap = snap;
      $('roDec').textContent = fmtE(snap.dEc);
      $('roTag').textContent = snap.dEc === START ? 'the published model’s spike' : snap.dEc === END ? 'best fit: a passivated cliff' : snap.dEc > 0 ? 'spike' : 'cliff';
      $('roS').textContent = fmtS(snap.logS);
      $('roV').textContent = snap.voc.toFixed(0) + ' mV';
      $('roX').textContent = snap.dchi2 < 1 ? snap.dchi2.toFixed(1) : snap.dchi2.toFixed(0);
      const c = $('roCur'); if (c) { c.setAttribute('cx', px(snap.dEc)); c.setAttribute('cy', py(snap.dchi2)); }
      document.querySelector('.readout').classList.toggle('good', snap.dEc === END);
    }
  }
  // on phones the readout sits where the copy is read first: fade it in once the copy has scrolled away
  const ro = document.querySelector('.hero .readout'), narrow = matchMedia('(max-width:760px)');
  const roFade = t => { if (!ro) return; ro.style.opacity = (narrow.matches && !S.reduced) ? Math.max(0, Math.min(1, (t - 0.2) / 0.1)).toFixed(2) : ''; };
  draw(S.reduced ? 1 : S.hero.t); roFade(S.reduced ? 1 : S.hero.t);
  S.onFrame(() => { const t = S.reduced ? 1 : S.hero.t; if (t !== last) { last = t; draw(t); roFade(t); } });
})();
