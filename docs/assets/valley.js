/* The identifiability valley in 3D: Delta-chi2 over (front offset, log10 S) from the fine scan of each simulated offset
   (window.CDTE.valley, built by docs/build_assets.py from optionA/sesame/kujovic/ident/ident_fine_scan.csv). Height is
   log10(1 + Delta-chi2), so the 95 % region is the floor of the trench. Drag to orbit, hover for values. ES module. */
import { THREE, createStage, makeLabel, redrawLabel } from './three-kit.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
const D = window.CDTE, S = window.SITE;
const canvas = document.getElementById('valleyCanvas');
if (canvas && D) {
  const st = createStage(canvas, { fov: 34, bloom: null, exposure: 1.0, envIntensity: .45 });
  if (!st.failed) build(st);
}
function build(st) {
  const { scene, camera } = st, holder = st.holder;
  const XS = 22, ZS = 1.15, YS = 1.0;                        // eV -> x, log S -> z, log10(1+dchi2) -> y
  const X = d => (d + 0.12) * XS, Z = l => -(l - 3) * ZS, Y = c => Math.log10(1 + Math.max(0, c)) * YS;
  const hemi = new THREE.HemisphereLight(0xffffff, 0x334155, 1.0); scene.add(hemi);
  const dl = new THREE.DirectionalLight(0xffffff, 1.2); dl.position.set(4, 10, 6); scene.add(dl);
  const g = new THREE.Group(); scene.add(g);
  const cmap = (v, dark) => { // v in 0..1 (0 = valley floor): deep blue -> pale
    const a = new THREE.Color(dark ? '#22d3ee' : '#0e7490'), b = new THREE.Color(dark ? '#1e293b' : '#cbd5e1');
    return a.clone().lerp(b, Math.min(1, Math.pow(v, .6)));
  };
  const W = 0.62, ribbons = [];
  D.valley.forEach(col => {
    const pts = col.pts, n = pts.length, pos = new Float32Array(n * 2 * 3), colr = new Float32Array(n * 2 * 3), idx = [];
    pts.forEach((p, i) => { const x = X(col.dEc), z = Z(p[0]), y = Y(p[1]); pos.set([x - W / 2, y, z, x + W / 2, y, z], i * 6); if (i < n - 1) { const a = 2 * i; idx.push(a, a + 1, a + 2, a + 1, a + 3, a + 2); } });
    const geo = new THREE.BufferGeometry(); geo.setAttribute('position', new THREE.BufferAttribute(pos, 3)); geo.setAttribute('color', new THREE.BufferAttribute(colr, 3)); geo.setIndex(idx); geo.computeVertexNormals();
    const m = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: .55, metalness: .05, side: THREE.DoubleSide }));
    m.userData = { col }; g.add(m); ribbons.push(m);
  });
  const paint = dark => ribbons.forEach(m => { const c = m.geometry.attributes.color, pts = m.userData.col.pts; pts.forEach((p, i) => { const v = Math.log10(1 + p[1]) / 3, k = cmap(v, dark); c.setXYZ(2 * i, k.r, k.g, k.b); c.setXYZ(2 * i + 1, k.r, k.g, k.b); }); c.needsUpdate = true; });
  // ridge (best S for each offset) and best fit
  const ridgePts = D.profile.slice().sort((a, b) => a.dEc - b.dEc).map(p => { const col = D.valley.find(v => Math.abs(v.dEc - p.dEc) < 1e-6); let best = col.pts[0]; col.pts.forEach(q => { if (q[1] < best[1]) best = q; }); return new THREE.Vector3(X(p.dEc), Y(best[1]) + .06, Z(best[0])); });
  const ridge = new THREE.Line(new THREE.BufferGeometry().setFromPoints(ridgePts), new THREE.LineBasicMaterial({ color: 0xec4899 })); g.add(ridge);
  const bestCol = D.valley.find(v => Math.abs(v.dEc - D.best.dEc) < 1e-6); let bp = bestCol.pts[0]; bestCol.pts.forEach(q => { if (q[1] < bp[1]) bp = q; });
  const star = new THREE.Mesh(new THREE.SphereGeometry(.2, 24, 16), new THREE.MeshStandardMaterial({ color: 0xf97316, emissive: 0xf97316, emissiveIntensity: .5 })); star.position.set(X(D.best.dEc), Y(bp[1]) + .2, Z(bp[0])); g.add(star);
  // XPS band on the floor, axes and labels
  const xps = new THREE.Mesh(new THREE.PlaneGeometry(X(D.xps[1]) - X(D.xps[0]), .5), new THREE.MeshBasicMaterial({ color: 0x10b981, transparent: true, opacity: .55, side: THREE.DoubleSide }));
  xps.rotation.x = -Math.PI / 2; xps.position.set((X(D.xps[0]) + X(D.xps[1])) / 2, -.02, Z(-0.6)); g.add(xps);
  const labels = [];
  const L = (txt, x, y, z, o = {}) => { const s = makeLabel(txt, { px: 24, scale: .32, bg: false, color: o.color || 'muted', ...o }); s.position.set(x, y, z); g.add(s); labels.push(s); return s; };
  [-0.3, -0.2, -0.1, 0, 0.1].forEach(d => L((d > 0 ? '+' : d < 0 ? '−' : '') + Math.abs(d).toFixed(1), X(d), -.05, Z(-1.1)));
  L('front offset ΔEc (eV)', X(-0.12), -.05, Z(-1.9), { color: 'ink' });
  [0, 2, 4, 6].forEach(l => L(String(l), X(-0.38), -.05, Z(l)));
  L('log₁₀ S (cm/s)', X(-0.46), -.05, Z(3.0), { color: 'ink' });
  L('XPS cliffs', (X(D.xps[0]) + X(D.xps[1])) / 2, .3, Z(-0.6), { color: 'green' });
  L('best fit', X(D.best.dEc), Y(bp[1]) + .75, Z(bp[0]), { color: 'hot' });
  const axisMat = new THREE.LineBasicMaterial({ color: 0x64748b, transparent: true, opacity: .6 });
  g.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(X(-0.36), 0, Z(-0.5)), new THREE.Vector3(X(0.12), 0, Z(-0.5))]), axisMat));
  g.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(X(-0.36), 0, Z(-0.5)), new THREE.Vector3(X(-0.36), 0, Z(6.2))]), axisMat));
  g.position.set(-X(-0.12), -1.2, 0);
  st.onTheme = dark => { paint(dark); labels.forEach(s => redrawLabel(s, dark)); hemi.intensity = 1.0 * st.lights; dl.intensity = 1.2 * st.lights; st.dirty = true; };
  st.onTheme(S.isDark());
  camera.position.set(-3.2, 9.0, 15.5);
  const ctr = new OrbitControls(camera, canvas); ctr.target.set(0, -.3, -.4); ctr.enableDamping = true; ctr.enableZoom = false; ctr.enablePan = false; ctr.minPolarAngle = .35; ctr.maxPolarAngle = 1.45; ctr.update();
  ctr.addEventListener('change', () => st.dirty = true);
  // hover readout
  const tip = document.getElementById('valleyTip'), ray = new THREE.Raycaster(), mv = new THREE.Vector2();
  canvas.addEventListener('pointermove', ev => {
    const r = canvas.getBoundingClientRect(); mv.set((ev.clientX - r.left) / r.width * 2 - 1, -(ev.clientY - r.top) / r.height * 2 + 1); ray.setFromCamera(mv, camera);
    const hit = ray.intersectObjects(ribbons, false)[0]; if (!hit || !tip) { if (tip) tip.hidden = true; return; }
    const col = hit.object.userData.col, zl = 3 - g.worldToLocal(hit.point.clone()).z / ZS; let q = col.pts[0]; col.pts.forEach(p => { if (Math.abs(p[0] - zl) < Math.abs(q[0] - zl)) q = p; });
    tip.hidden = false; tip.style.left = (ev.clientX + 14) + 'px'; tip.style.top = (ev.clientY + 14) + 'px';
    tip.innerHTML = `<b>ΔE<sub>c</sub> ${col.dEc > 0 ? '+' : col.dEc < 0 ? '−' : ''}${Math.abs(col.dEc).toFixed(2)} eV</b>S = 10<sup>${q[0].toFixed(2)}</sup> cm/s · Δχ² ${q[1] < 10 ? q[1].toFixed(1) : q[1].toFixed(0)}`;
  });
  canvas.addEventListener('pointerleave', () => { if (tip) tip.hidden = true; });
  let spin = !S.reduced;
  canvas.addEventListener('pointerdown', () => { spin = false; });
  st.loop((t, dt) => { if (spin) { g.rotation.y = Math.sin(t * .25) * .18; return true; } return ctr.update(); });
}
