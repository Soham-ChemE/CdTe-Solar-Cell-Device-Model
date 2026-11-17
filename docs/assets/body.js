/* Body scenes of the CdTe page, drawn by the shared renderer in viz.js (one WebGL context, scissor per placeholder, lazy build
   near the viewport, dispose when far away). Every number comes from window.CDTE (assets/data.js) or assets/cliff.json, both
   written by docs/build_assets.py from the committed CSVs; interactive state comes from window.PAGE (assets/page.js).
     vocT    F1  Voc(T): 13 measured points against the best cliff, the best spike and the published spike
     cliff   --  the ZnO/CdSeTe interface driven by the sliders of "The cliff, live"
     valley  F2  Delta chi2 over (dEc, log S), camera driven by the sticky steps
     fluct   F3  Gaussian band-gap domains at the chosen sigma, and the profile against dEc with the spike's floor
     zno     F4  a Cu-doped and an As-doped ZnO interface with recombination sparks; Voc of the Mg series, model vs measured
     design  F5  the design staircase from the calibrated cell to the conservative design
     solvers F6  dark J-V of SCAPS and Sesame for four offsets, with a sweeping voltage cursor
     znse    F7  efficiency against the ZnSe offset for eight front variants, with the DFT band */
import { THREE, redrawLabel } from './three-kit.js';
import Viz from './viz.js';

const D = window.CDTE, P = window.PAGE, S = window.SITE;
const clamp = (v, a, b) => Math.min(b, Math.max(a, v)), lerp = (a, b, t) => a + (b - a) * t;
const ease = t => t < .5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
const sstep = (a, b, x) => { const t = clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };
const mulberry = a => () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
const gauss = r => { let u = 0, w = 0; while (u === 0) u = r(); while (w === 0) w = r(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * w); };
const SUP = { '-': '⁻', '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹' };
const sup = s => String(s).split('').map(c => SUP[c] || c).join('');
const mn = s => String(s).replace(/-/g, '−');
const sgn = (v, d = 2) => (v > 0 ? '+' : '') + mn((+v).toFixed(d));
const lg = x => Math.log10(Math.max(x, .3));
const phone = S.phone;
const Z = new THREE.Matrix4().makeScale(0, 0, 0), M4 = new THREE.Matrix4(), V3 = new THREE.Vector3(), Q4 = new THREE.Quaternion(), SC = new THREE.Vector3();
const lab = (v, text, pos, o = {}) => Viz.label(v, text, pos, { px: 24, scale: .085, bg: false, color: 'muted', ...o });
const sphereG = () => new THREE.SphereGeometry(1, 14, 10);
function inst(v, geo, mat, n, parent) { const im = new THREE.InstancedMesh(geo, mat, n); im.frustumCulled = false; for (let i = 0; i < n; i++) im.setMatrixAt(i, Z); (parent || v.rig).add(im); return im; }
const basic = (key, o = {}) => { const m = new THREE.MeshBasicMaterial({ color: Viz.pal[key] || key, transparent: true, depthWrite: false, ...o }); m.userData.pal = key; return m; };
const yAxisLog = { lo: -.55, hi: 3.8, ticks: [0, 1, 2, 3], fmt: t => ['1', '10', '100', '1000'][t] };

/* ======================================================================== 01 Voc(T) */
Viz.view('[data-viz="vocT"]', v => {
  const VT = D.vocT, keys = ['cliff', 'spike', 'published'], cols = ['green', 'hot', 'rose'];
  const A = Viz.axes(v, { size: [4.6, 2.5, 1.8], x: { lo: 210, hi: 360, ticks: [220, 260, 300, 340], label: 'temperature (K)' }, y: { lo: 740, hi: 940, ticks: [750, 800, 850, 900], label: 'Voc (mV)' }, z: { lo: 0, hi: 3 } });
  const meas = VT.measured, rib = [], stems = [], lanes = [];
  const dotM = Viz.mat('ink', { roughness: .3, emissive: 'ink', emissiveIntensity: .25 });
  const dots = inst(v, sphereG(), dotM, meas.length * 3); v.pickables.push(dots);
  const stemG = new THREE.CylinderGeometry(1, 1, 1, 6); stemG.translate(0, .5, 0);
  VT.models.forEach((m, k) => {
    const z = k + .5, xs = m.curve.map(c => c[0]), ys = m.curve.map(c => c[1]);
    rib.push(Viz.ribbon(v, A, xs, ys, { z, width: .2, color: cols[k], name: ['best cliff', 'best spike', 'published spike'][k] + ` (${sgn(m.dEc)} eV)`, unit: 'mV', skirtOpacity: .12 }));
    const st = inst(v, stemG, Viz.mat(cols[k], { emissive: cols[k], emissiveIntensity: .4 }), meas.length); stems.push(st);
    meas.forEach(([T, Vm], i) => {
      const q = A.map(T, Vm, z); M4.compose(q, Q4, SC.set(.045, .045, .045)); dots.setMatrixAt(k * meas.length + i, M4);
      let j = 1; while (j < xs.length - 1 && xs[j] < T) j++; const Vmod = lerp(ys[j - 1], ys[j], (T - xs[j - 1]) / (xs[j] - xs[j - 1]));
      const a = A.map(T, Math.min(Vm, Vmod), z), b = A.map(T, Math.max(Vm, Vmod), z); st.userData[i] = { T, Vm, Vmod };
      M4.compose(a, Q4, SC.set(.012, Math.max(1e-3, b.y - a.y), .012)); st.setMatrixAt(i, M4);
    });
    st.instanceMatrix.needsUpdate = true;
    lanes.push(lab(v, `${['best cliff', 'best spike', 'published spike'][k]} ${sgn(m.dEc)} eV · Δχ² ${m.dchi2 < 10 ? m.dchi2.toFixed(1) : Math.round(m.dchi2)}`, A.map(362, ys[ys.length - 1] - 6, z).toArray(), { color: cols[k], weight: 700, px: 22 }));
  });
  dots.userData.meas = meas; dots.instanceMatrix.needsUpdate = true;
  lab(v, 'spheres: measured (13 points, 216–355 K)', A.map(285, 935, 0).toArray(), { px: 20 });
  let cur = '', cv = -1;
  v.update = vv => {
    let ch = false; if (Math.abs(vv.p - cv) > 1e-4) { cv = vv.p; rib.forEach(r => r.draw(ease(vv.p))); stems.forEach(s => s.visible = vv.p > .95); ch = true; }
    if (P.vt !== cur) { cur = P.vt; keys.forEach((k, i) => { const on = k === cur, o = on ? 1 : .28; [rib[i].mesh.material].forEach(m => { m.transparent = true; m.opacity = o; m.depthWrite = on; }); if (rib[i].skirt) rib[i].skirt.material.opacity = on ? .16 : .04; stems[i].material.transparent = true; stems[i].material.opacity = on ? 1 : .25; lanes[i].material.opacity = on ? 1 : .45; }); ch = true; }
    return ch;
  };
  v.hover = hit => { if (hit.object === dots) { const k = hit.instanceId % meas.length, [T, Vm] = meas[k]; return `<b>measured</b>${T.toFixed(0)} K · ${Vm.toFixed(1)} mV`; } const ud = hit.object.userData; if (!ud.xs) return null; const i = Viz.ribbonIndex(hit, A); return `<b>${ud.series}</b>${ud.xs[i].toFixed(0)} K · ${ud.ys[i].toFixed(1)} mV`; };
}, { camera: [1.3, 1.25, 7.4], target: [0, -.05, 0], fov: 32, rot: -.12 });

/* ======================================================================== 02 the cliff, live */
Viz.view('[data-viz="cliff"]', v => {
  const K = 2.0, E0 = .35, yE = E => K * (E - E0), ZW = 1.25, X0 = -2.6, XZ = -1.5, X1 = 3.3;
  const u = x => clamp(x / X1, 0, 1);
  const EcA = x => 1.32 - .70 * Math.pow(Math.max(0, 1 - u(x) / .45), 2), EvA = x => EcA(x) - (1.41 + .06 * sstep(.2, 1, u(x)));
  let dEc = -.3; const EcZ = x => lerp(.08, EcA(0) + dEc, clamp((x - XZ) / -XZ, 0, 1));
  const sheet = (x0, x1, nx, key, fn, op = .7) => { const g = new THREE.PlaneGeometry(x1 - x0, 2 * ZW, nx, 1); g.rotateX(-Math.PI / 2); g.translate((x0 + x1) / 2, 0, 0); const m = Viz.mat(key, { side: THREE.DoubleSide, opacity: op, emissive: key, emissiveIntensity: .45, depthWrite: false }); const mesh = new THREE.Mesh(g, m); v.rig.add(mesh); const pos = g.attributes.position; const set = () => { for (let i = 0; i < pos.count; i++) pos.setY(i, fn(pos.getX(i))); pos.needsUpdate = true; g.computeVertexNormals(); }; set(); return { mesh, set }; };
  const sEc = sheet(0, X1, 48, 'warm', x => yE(EcA(x))), sEv = sheet(0, X1, 48, 'warm', x => yE(EvA(x))), sZ = sheet(XZ, 0, 4, 'green', x => yE(EcZ(x)), .85), sF = sheet(X0, XZ, 2, 'blue', () => yE(-.08), .7);
  // region slabs, faint
  const reg = (x0, x1, key, op) => { const m = new THREE.Mesh(new THREE.BoxGeometry(x1 - x0, .04, 2 * ZW), Viz.mat(key, { opacity: op })); m.position.set((x0 + x1) / 2, yE(-1.25), 0); v.rig.add(m); };
  reg(X0, XZ, 'blue', .5); reg(XZ, 0, 'green', .55); reg(0, X1, 'warm', .45);
  const stepM = Viz.mat('green', { emissive: 'green', emissiveIntensity: .9 }); const step = new THREE.Mesh(new THREE.BoxGeometry(.05, 1, 2 * ZW + .02), stepM); v.rig.add(step);
  const ifM = basic('rose', { opacity: .08, side: THREE.DoubleSide, blending: THREE.AdditiveBlending }); const ifP = new THREE.Mesh(new THREE.PlaneGeometry(2 * ZW, 1), ifM); ifP.rotation.y = Math.PI / 2; v.rig.add(ifP);
  // recombination arcs (dashed) at three depths
  const arcPts = (z, n = 20) => { const a = [0, yE(EcZ(0))], b = [0, yE(EvA(0))], c = [-1.0, (a[1] + b[1]) / 2]; return Array.from({ length: n + 1 }, (_, i) => { const s = i / n, q = 1 - s; return new THREE.Vector3(q * q * a[0] + 2 * q * s * c[0] + s * s * b[0], q * q * a[1] + 2 * q * s * c[1] + s * s * b[1], z); }); };
  const arcM = new THREE.LineDashedMaterial({ color: Viz.pal.rose, dashSize: .08, gapSize: .06, transparent: true, opacity: .9 }); arcM.userData.pal = 'rose';
  const arcs = [-.8, 0, .8, ZW].map(z => { const l = new THREE.Line(new THREE.BufferGeometry().setFromPoints(arcPts(z)), arcM); v.rig.add(l); return { l, z }; });
  const lStep = lab(v, '', [0, 0, ZW], { color: 'ink', weight: 800, px: 26, bg: null, scale: .1 });
  lab(v, 'ZnO', [XZ / 2, yE(-1.25) + .25, ZW], { color: 'green', weight: 700 }); lab(v, 'FTO', [(X0 + XZ) / 2, yE(-1.25) + .25, ZW], { color: 'blue', weight: 700 }); lab(v, 'As-doped CdSeTe', [1.9, yE(-1.25) + .25, ZW], { color: 'warm', weight: 700 });
  lab(v, 'Ec', [X1 + .25, yE(EcA(X1)), ZW], { color: 'ink' }); lab(v, 'Ev', [X1 + .25, yE(EvA(X1)), ZW], { color: 'ink' });
  // electrons riding Ec toward the front; recombination sparks along the arc
  const NE = phone ? 70 : 140, NSP = 80, R = mulberry(3);
  const eM = basic('cyan', { depthWrite: true }), elec = inst(v, sphereG(), eM, NE), spM = basic('rose', { blending: THREE.AdditiveBlending }), sparks = inst(v, sphereG(), spM, NSP);
  const E = Array.from({ length: NE }, () => ({ x: R() * X1, z: (R() * 2 - 1) * ZW * .9, sp: .7 + R() * .8, dec: false })), SPK = Array.from({ length: NSP }, () => ({ life: 0, s: 0, z: 0 })); let sk = 0, act = 0;
  let ver = -1, label = '';
  const apply = () => {
    const c = P.cliff; if (!c) return; dEc = c.dEc; sZ.set();
    const y1 = yE(EcA(0)), y2 = yE(EcZ(0)); step.scale.y = Math.max(.02, Math.abs(y2 - y1)); step.position.set(0, (y1 + y2) / 2, 0);
    stepM.userData.pal = dEc > 0 ? 'hot' : 'green'; stepM.userData.emissive = stepM.userData.pal; stepM.color.set(Viz.pal[stepM.userData.pal]); stepM.emissive.set(Viz.pal[stepM.userData.pal]);
    arcs.forEach(a => { a.l.geometry.dispose(); a.l.geometry = new THREE.BufferGeometry().setFromPoints(arcPts(a.z)); a.l.computeLineDistances(); });
    const top = Math.max(y1, y2), bot = yE(EvA(0)); ifP.scale.y = top - bot; ifP.position.y = (top + bot) / 2;
    const t = `${sgn(dEc)} eV ${dEc > 0 ? 'spike' : 'cliff'} · S ${c.logS < 2.5 ? (Math.pow(10, c.logS) < 10 ? Math.pow(10, c.logS).toFixed(1) : Math.round(Math.pow(10, c.logS))) : '10' + sup(c.logS.toFixed(1))} cm/s`;
    if (t !== label) { label = t; lStep.userData.label.text = t; lStep.userData.label.o.color = dEc > 0 ? 'hot' : 'green'; redrawLabel(lStep, v.dark); }
    lStep.position.set(-.2, top + .45, ZW);
  };
  v.onTheme = () => { label = ''; ver = -1; };
  v.update = (vv, t, dt) => {
    if (P.v !== ver) { ver = P.v; apply(); }
    const c = P.cliff; if (!c) return false;
    const pr = c.voc == null ? .5 : clamp((970 - c.voc) / 250, .03, .95), h = Math.min(.05, (dt || 16) / 1000), yA = yE(EvA(0));
    for (let i = 0; i < NE; i++) {
      const e = E[i], xp = e.x; e.x -= e.sp * h * (e.x > 0 ? 1 + 2.2 * (1 - sstep(0, 1.6, e.x)) : 1.8);
      if (xp >= 0 && e.x < 0 && !e.dec) { e.dec = true; if (R() < pr) { const s = SPK[sk++ % NSP]; s.life = 1; s.s = 0; s.z = e.z; act = Math.min(1, act + .12); e.x = X1 + R() * .4; e.dec = false; } }
      if (e.x < X0 + .05) { e.x = X1 + R() * .3; e.dec = false; }
      const y = (e.x >= 0 ? yE(EcA(e.x)) : e.x >= XZ ? yE(EcZ(e.x)) : yE(-.08)) + .06;
      M4.compose(V3.set(e.x, y, e.z), Q4, SC.set(.05, .05, .05)); elec.setMatrixAt(i, e.x > X1 ? Z : M4);
    }
    const a0 = [0, yE(EcZ(0))], c0 = [-1.0, (a0[1] + yA) / 2];
    for (let k = 0; k < NSP; k++) { const s = SPK[k]; if (s.life <= 0) { sparks.setMatrixAt(k, Z); continue; } s.life -= h * 2.2; s.s = Math.min(1, s.s + h * 3); const q = 1 - s.s, x = q * q * a0[0] + 2 * q * s.s * c0[0], y = q * q * a0[1] + 2 * q * s.s * c0[1] + s.s * s.s * yA, r = .03 + .05 * Math.sin(Math.PI * clamp(s.life, 0, 1)); M4.compose(V3.set(x, y, s.z), Q4, SC.set(r, r, r)); sparks.setMatrixAt(k, M4); }
    act *= Math.pow(.3, h); ifM.opacity = .05 + .35 * act;
    elec.instanceMatrix.needsUpdate = true; sparks.instanceMatrix.needsUpdate = true; return true;
  };
}, { camera: [-1.7, 1.3, 9.8], target: [.35, -.25, 0], fov: 34, rot: .3, tilt: .04, aspect: 1.33 });

/* ======================================================================== 03 valley (needs cliff.json) */
P.cliffData.then(J => { if (!J) return; Viz.view('[data-viz="valley"]', v => {
  const A = Viz.axes(v, { size: [5, 2.4, 3.6], x: { lo: -.37, hi: .13, ticks: [-.3, -.2, -.1, 0, .1], fmt: t => mn(t.toFixed(1)), label: 'ΔEc (eV)' }, y: { ...yAxisLog, label: 'Δχ²' }, z: { lo: 0, hi: 6, ticks: [0, 2, 4, 6], fmt: t => (6 - t) ? '10' + sup(6 - t) : '1', label: 'S (cm/s)' } });
  const zS = ls => 6 - ls;   // low S in front
  const O = J.offsets, G = Array.from({ length: 121 }, (_, i) => i * .05), W = .014;
  const hAt = (o, ls) => { const f = o.fine; if (ls < f[0][0] - 1e-9 || ls > f[f.length - 1][0] + 1e-9) return null; let k = 1; while (k < f.length - 1 && f[k][0] < ls) k++; const a = f[k - 1], b = f[k]; return lerp(a[3], b[3], clamp((ls - a[0]) / ((b[0] - a[0]) || 1), 0, 1)); };
  const H = O.map(o => G.map(ls => { const x = hAt(o, ls); return x == null ? null : lg(x); }));
  const stops = () => ['cyan', 'blue', 'cool', 'grey'].map(k => new THREE.Color(Viz.pal[k]));
  const colAt = (y, st, out) => { const t = clamp((y - yAxisLog.lo) / (3.7 - yAxisLog.lo), 0, 1) * (st.length - 1), a = Math.min(st.length - 2, Math.floor(t)); return out.copy(st[a]).lerp(st[a + 1], t - a); };
  // ribbons (one per simulated offset): a top strip and a skirt to the floor
  const pos = [], col = [], idx = [], skI = [], skin = [], skinC = [], skinI = [], c = new THREE.Color(), base = A.map(0, yAxisLog.lo, 0).y;
  const vtx = (arr, carr, p, y) => { arr.push(p.x, p.y, p.z); colAt(y, ST, c); carr.push(c.r, c.g, c.b); return arr.length / 3 - 1; };
  let ST = stops();
  const build = () => {
    pos.length = col.length = idx.length = skI.length = skin.length = skinC.length = skinI.length = 0; ST = stops();
    O.forEach((o, i) => { let prev = null; G.forEach((ls, j) => { const y = H[i][j]; if (y == null) { prev = null; return; } const p = A.map(o.dEc, y, zS(ls)); const a = vtx(pos, col, V3.set(p.x - W * 10, p.y, p.z), y), b = vtx(pos, col, V3.set(p.x + W * 10, p.y, p.z), y), fa = vtx(pos, col, V3.set(p.x - W * 10, base, p.z), y), fb = vtx(pos, col, V3.set(p.x + W * 10, base, p.z), y); if (prev) { idx.push(prev[0], a, prev[1], prev[1], a, b); skI.push(prev[2], fa, prev[0], prev[0], fa, a, prev[1], b, prev[3], prev[3], b, fb); } prev = [a, b, fa, fb]; }); });
    for (let i = 0; i < O.length - 1; i++) { let prev = null; G.forEach((ls, j) => { const y0 = H[i][j], y1 = H[i + 1][j]; if (y0 == null || y1 == null) { prev = null; return; } const p0 = A.map(O[i].dEc, y0, zS(ls)), p1 = A.map(O[i + 1].dEc, y1, zS(ls)); const a = vtx(skin, skinC, p0, y0), b = vtx(skin, skinC, p1, y1); if (prev) skinI.push(prev[0], a, prev[1], prev[1], a, b); prev = [a, b]; }); }
  };
  build();
  const mk = (p, cc, ii, mat) => { const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(p, 3)); g.setAttribute('color', new THREE.Float32BufferAttribute(cc, 3)); g.setIndex(ii); g.computeVertexNormals(); const m = new THREE.Mesh(g, mat); v.rig.add(m); return m; };
  const ribM = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: .45, metalness: .1, side: THREE.DoubleSide }), skinM = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: .6, transparent: true, opacity: .3, side: THREE.DoubleSide, depthWrite: false });
  const wallM = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: .6, transparent: true, opacity: .42, side: THREE.DoubleSide, depthWrite: false });
  let rib = mk(pos, col, idx, ribM), wl = mk(pos, col, skI, wallM), sk = mk(skin, skinC, skinI, skinM); v.pickables.push(rib);
  // the 95 % "water level" (delta chi2 = 6.2): where the floor dips below it is the 95 % region
  const lvl = A.map(0, lg(6.2), 0).y, water = new THREE.Mesh(new THREE.PlaneGeometry(5, 3.6), Viz.mat('cyan', { opacity: .16, side: THREE.DoubleSide, depthWrite: false, emissive: 'cyan', emissiveIntensity: .3 })); water.rotation.x = -Math.PI / 2; water.position.y = lvl; v.rig.add(water);
  lab(v, 'Δχ² = 6.2: below this plane, the 95 % region', A.map(.13, lg(6.2), 0).add(V3.set(.2, .08, 0)).toArray(), { color: 'cyan', px: 20 });
  // ridge (best S per offset) as a tube, best fit and the published spike as markers
  const rp = O.map(o => A.map(o.dEc, lg(o.dchi2_profile), zS(o.ridge)));
  const ridge = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(rp, false, 'centripetal'), 120, .022, 8), Viz.mat('rose', { emissive: 'rose', emissiveIntensity: .5 })); v.rig.add(ridge);
  lab(v, 'best S for each offset (ridge)', rp[6].clone().add(V3.set(.1, .35, 0)).toArray(), { color: 'rose', px: 20 });
  const ball = (p, key, r) => { const m = new THREE.Mesh(sphereG(), Viz.mat(key, { emissive: key, emissiveIntensity: .7 })); m.scale.setScalar(r); m.position.copy(p); v.rig.add(m); return m; };
  const best = O.find(o => Math.abs(o.dEc + .3) < 1e-6), spk = O.find(o => Math.abs(o.dEc - .1) < 1e-6);
  const pBest = A.map(-.3, lg(best.dchi2_profile), zS(best.ridge)), pSpk = A.map(.1, lg(spk.dchi2_profile), zS(spk.ridge));
  ball(pBest, 'hot', .07); ball(pSpk, 'hot', .07);
  lab(v, 'best fit −0.30 eV, S ≈ 5 cm/s', pBest.clone().add(V3.set(-.2, .42, 0)).toArray(), { color: 'ink', weight: 700, px: 22, bg: null });
  lab(v, 'published +0.10 eV spike · Δχ² ≈ 589', pSpk.clone().add(V3.set(-.3, .38, 0)).toArray(), { color: 'ink', weight: 700, px: 22, bg: null });
  // XPS band on the floor and its two values
  const x0 = A.map(-.32, 0, 0).x, x1 = A.map(-.22, 0, 0).x, xps = new THREE.Mesh(new THREE.BoxGeometry(x1 - x0, .03, 3.6), Viz.mat('green', { opacity: .45, emissive: 'green', emissiveIntensity: .3, depthWrite: false })); xps.position.set((x0 + x1) / 2, base + .015, 0); v.rig.add(xps);
  [-.32, -.22].forEach(d => { const p = A.map(d, yAxisLog.lo, 0); const post = new THREE.Mesh(new THREE.CylinderGeometry(.012, .012, 1.2, 6), Viz.mat('green', { emissive: 'green', emissiveIntensity: .5 })); post.position.set(p.x, base + .6, -1.85); v.rig.add(post); });
  lab(v, 'XPS cliffs −0.32 / −0.22 eV (Liu 2022)', [(x0 + x1) / 2, base + 1.35, -1.85], { color: 'green', weight: 700, px: 20 });
  // camera poses for the sticky steps
  const POSE = { map: [[-4.0, 3.5, 5.9], [.2, -.4, 0]], ridge: [[.2, 7.8, 1.4], [0, -.7, 0]], floor: [[-4.3, 1.0, 4.8], [-1.6, -1.0, .9]], xps: [[-.4, 2.0, 6.0], [-1.4, -.9, .5]], spike: [[5.8, 3.0, 4.6], [1.7, .3, -1.0]] };
  const cp = new THREE.Vector3(...POSE.map[0]), ct = new THREE.Vector3(...POSE.map[1]), tp = new THREE.Vector3(), tt = new THREE.Vector3();
  v.camera.position.copy(cp); v.camera.lookAt(ct);
  let cv = -1;
  v.update = vv => {
    let ch = false; const pose = POSE[P.valley] || POSE.map; tp.set(...pose[0]); tt.set(...pose[1]);
    if (cp.distanceToSquared(tp) > 1e-5 || ct.distanceToSquared(tt) > 1e-5) { cp.lerp(tp, .06); ct.lerp(tt, .06); vv.camera.position.copy(cp); vv.camera.lookAt(ct); ch = true; }
    if (Math.abs(vv.p - cv) > 1e-4) { cv = vv.p; const e = ease(vv.p); rib.scale.y = wl.scale.y = sk.scale.y = Math.max(.02, e); rib.position.y = wl.position.y = sk.position.y = base * (1 - e); ch = true; }
    return ch;
  };
  v.onTheme = () => { build(); [rib, wl, sk].forEach(m => { v.rig.remove(m); m.geometry.dispose(); }); rib = mk(pos, col, idx, ribM); wl = mk(pos, col, skI, wallM); sk = mk(skin, skinC, skinI, skinM); v.pickables.length = 0; v.pickables.push(rib); cv = -1; };
  v.hover = hit => { const p = hit.point.clone(); v.rig.worldToLocal(p); const d = (p.x + 2.5) / 5 * .5 - .37, ls = 6 - (p.z + 1.8) / 3.6 * 6; let o = O[0]; O.forEach(q => { if (Math.abs(q.dEc - d) < Math.abs(o.dEc - d)) o = q; }); const x = hAt(o, clamp(ls, 0, 6)); return x == null ? null : `<b>ΔEc ${sgn(o.dEc)} eV</b>S ≈ 10${sup(ls.toFixed(1))} cm/s · Δχ² ${x < 10 ? x.toFixed(1) : Math.round(x)}`; };
}, { camera: [-4.4, 4.0, 6.6], target: [.2, -.4, 0], fov: 34, aspect: 1.05 }); });

/* ======================================================================== 04 fluctuation gate */
Viz.view('[data-viz="fluct"]', v => {
  const F = D.fluct, n = phone ? 11 : 16, sp = .2, KX = 7, R = mulberry(17), g = Array.from({ length: n * n }, () => gauss(R));
  const L = new THREE.Group(); L.position.set(-2.55, 0, 0); v.rig.add(L);
  const tileG = new THREE.BoxGeometry(sp * .86, .05, sp * .86), cb = inst(v, tileG, new THREE.MeshStandardMaterial({ roughness: .4, metalness: .1 }), n * n, L), vb = inst(v, tileG, new THREE.MeshStandardMaterial({ roughness: .4, metalness: .1 }), n * n, L);
  const pillar = inst(v, new THREE.BoxGeometry(sp * .18, 1, sp * .18), new THREE.MeshBasicMaterial({ transparent: true, opacity: .25, depthWrite: false }), n * n, L);
  const cHot = new THREE.Color(), cCool = new THREE.Color(), cMid = new THREE.Color(), c = new THREE.Color();
  const Lc = Viz.label(v, '', [0, 1.95, 0], { parent: L, px: 26, scale: .09, bg: null, color: 'ink', weight: 800 });
  Viz.label(v, 'conduction-band edge of each domain', [0, 1.45, -1.9], { parent: L, px: 20, scale: .08, bg: false, color: 'muted' }); Viz.label(v, 'valence-band edge of each domain', [0, -1.55, -1.9], { parent: L, px: 20, scale: .08, bg: false, color: 'muted' });
  // right: profile delta chi2 against dEc at sigma
  const Rg = new THREE.Group(); Rg.position.set(1.95, 0, 0); v.rig.add(Rg); const rig0 = v.rig; v.rig = Rg;
  const A = Viz.axes(v, { size: [3.2, 2.6, .9], x: { lo: -.56, hi: .1, ticks: [-.5, -.4, -.3, -.2, -.1, 0], fmt: t => mn(t.toFixed(1)), label: 'ΔEc (eV)' }, y: { ...yAxisLog, label: 'Δχ²' }, z: { lo: 0, hi: 1 } });
  const nd = F.dEc.length, dotM = Viz.mat('cyan', { emissive: 'cyan', emissiveIntensity: .5 }), dots = inst(v, sphereG(), dotM, nd); v.pickables.push(dots);
  const rpos = new Float32Array(nd * 2 * 3), ridx = []; for (let i = 0; i < nd - 1; i++) ridx.push(2 * i, 2 * i + 1, 2 * i + 2, 2 * i + 1, 2 * i + 3, 2 * i + 2);
  const rg = new THREE.BufferGeometry(); rg.setAttribute('position', new THREE.BufferAttribute(rpos, 3)); rg.setIndex(ridx); const rmesh = new THREE.Mesh(rg, Viz.mat('cyan', { side: THREE.DoubleSide, opacity: .75, emissive: 'cyan', emissiveIntensity: .4 })); Rg.add(rmesh);
  const yw = A.map(0, lg(447), 0).y, yb = A.map(0, yAxisLog.lo, 0).y, xs0 = A.map(.025, 0, 0).x, xs1 = A.map(.095, 0, 0).x;
  const wall = new THREE.Mesh(new THREE.BoxGeometry(xs1 - xs0 + .1, yw - yb, .9), Viz.mat('rose', { opacity: .3, emissive: 'rose', emissiveIntensity: .35, depthWrite: false })); wall.position.set((xs0 + xs1) / 2, (yw + yb) / 2, 0); Rg.add(wall);
  const cap = new THREE.Mesh(new THREE.BoxGeometry(xs1 - xs0 + .14, .02, .96), Viz.mat('rose', { emissive: 'rose', emissiveIntensity: .8 })); cap.position.set((xs0 + xs1) / 2, yw, 0); Rg.add(cap);
  Viz.label(v, 'spike floor: Δχ² ≥ 447\nunder every S bound and prior', [(xs0 + xs1) / 2 - .35, yw + .52, .5], { parent: Rg, px: 20, scale: .08, bg: null, color: 'rose', weight: 700 });
  const bestM = new THREE.Mesh(sphereG(), Viz.mat('hot', { emissive: 'hot', emissiveIntensity: .8 })); bestM.scale.setScalar(.075); Rg.add(bestM);
  const Lb = Viz.label(v, '', [0, 0, 0], { parent: Rg, px: 20, scale: .08, bg: null, color: 'ink', weight: 700 });
  v.rig = rig0;
  let sig = P.sigma, ver = -1, lastS = -1;
  const rowAt = s => { const k = clamp(s / 5, 0, F.sigma.length - 1), a = Math.floor(k), b = Math.min(F.sigma.length - 1, a + 1); return F.dchi2[a].map((x, i) => lerp(x, F.dchi2[b][i], k - a)); };
  const paintTiles = () => { cHot.set(Viz.pal.hot); cCool.set(Viz.pal.cool); cMid.set(Viz.pal.grey); for (let i = 0; i < n * n; i++) { const t = clamp(g[i] / 2.2, -1, 1); c.copy(cMid).lerp(t < 0 ? cHot : cCool, Math.abs(t)); cb.setColorAt(i, c); vb.setColorAt(i, c); } cb.instanceColor.needsUpdate = vb.instanceColor.needsUpdate = true; pillar.material.color.set(Viz.pal.muted); };
  paintTiles();
  const place = s => {
    for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) {
      const k = i * n + j, x = (i - (n - 1) / 2) * sp, z = (j - (n - 1) / 2) * sp, d = g[k] * s / 1000 * KX;  // delta (eV) * KX units/eV; f_cb = 0.5
      M4.compose(V3.set(x, .95 + d / 2, z), Q4, SC.set(1, 1, 1)); cb.setMatrixAt(k, M4); M4.compose(V3.set(x, -.95 - d / 2, z), Q4, SC.set(1, 1, 1)); vb.setMatrixAt(k, M4);
      M4.compose(V3.set(x, d * 0, z), Q4, SC.set(1, 1.9 + d, 1)); pillar.setMatrixAt(k, M4);
    }
    cb.instanceMatrix.needsUpdate = vb.instanceMatrix.needsUpdate = pillar.instanceMatrix.needsUpdate = true;
    const row = rowAt(s); let bi = 0; row.forEach((x, i) => { if (x < row[bi]) bi = i; });
    for (let i = 0; i < nd; i++) { const p = A.map(F.dEc[i], lg(row[i]), .5); rpos.set([p.x, p.y, p.z - .22, p.x, p.y, p.z + .22], i * 6); M4.compose(p, Q4, SC.set(.05, .05, .05)); dots.setMatrixAt(i, M4); }
    rg.attributes.position.needsUpdate = true; rg.computeVertexNormals(); rg.computeBoundingSphere(); dots.instanceMatrix.needsUpdate = true;
    bestM.position.copy(A.map(F.dEc[bi], lg(row[bi]), .5));
    const ks = Math.round(s / 5) * 5; if (ks !== lastS) { lastS = ks; Lc.userData.label.text = `σ = ${ks} meV`; redrawLabel(Lc, v.dark); const k = F.sigma.indexOf(ks), r = F.dchi2[k]; let b = 0; r.forEach((x, i) => { if (x < r[b]) b = i; }); Lb.userData.label.text = `best at this σ: ${sgn(F.dEc[b])} eV`; redrawLabel(Lb, v.dark); }
    Lb.position.copy(bestM.position).add(V3.set(0, .32, 0));
  };
  place(sig);
  v.onTheme = () => { paintTiles(); lastS = -1; place(sig); };
  v.update = (vv, t, dt) => { let ch = false; if (Math.abs(sig - P.sigma) > .05) { sig += (P.sigma - sig) * .12; place(sig); ch = true; } else if (sig !== P.sigma) { sig = P.sigma; place(sig); ch = true; } return ch; };
  v.hover = hit => { if (hit.object !== dots) return null; const i = hit.instanceId, k = F.sigma.indexOf(P.sigma); return `<b>ΔEc ${sgn(F.dEc[i])} eV, σ = ${P.sigma} meV</b>Δχ² ${Math.round(F.dchi2[k][i] * 10) / 10} · S = 10${sup(F.logS[k][i].toFixed(2))} cm/s`; };
}, { camera: [0, 2.6, 8.4], target: [0, -.1, 0], fov: 34, rot: -.18, tilt: .04, aspect: 2 });

/* ======================================================================== 05 ZnO paradox */
Viz.view('[data-viz="zno"]', v => {
  const Z0 = D.zno, R = mulberry(23), NSP = phone ? 120 : 220;
  const block = (x, title, logS, key) => {
    const g = new THREE.Group(); g.position.x = x; v.rig.add(g);
    const zno = new THREE.Mesh(new THREE.BoxGeometry(1.35, .45, 1.35), Viz.mat('green', { opacity: .55, depthWrite: false })); zno.position.y = .3; g.add(zno);
    const ab = new THREE.Mesh(new THREE.BoxGeometry(1.35, 1.4, 1.35), Viz.mat(key, { opacity: .7, depthWrite: false })); ab.position.y = -.65; g.add(ab);
    const ifc = new THREE.Mesh(new THREE.PlaneGeometry(1.35, 1.35), basic('rose', { opacity: .12, side: THREE.DoubleSide, blending: THREE.AdditiveBlending })); ifc.rotation.x = -Math.PI / 2; ifc.position.y = .075; g.add(ifc);
    Viz.label(v, title, [0, 1.1, 0], { parent: g, px: 22, scale: .085, bg: null, color: 'ink', weight: 700 });
    Viz.label(v, 'ZnO', [-.86, .3, .7], { parent: g, px: 20, scale: .075, bg: false, color: 'green', weight: 700 });
    return { g, logS, ifc, sp: Array.from({ length: NSP }, () => ({ life: 0, x: 0, z: 0 })), im: inst(v, sphereG(), basic('rose', { blending: THREE.AdditiveBlending }), NSP, g), acc: 0 };
  };
  const cu = block(-3.45, `Cu-doped absorber · S ≈ 10${sup(Z0.logS_cu.toFixed(0))} cm/s\nZnO cells average 8.0 %`, Z0.logS_cu, 'warm'), as = block(-1.6, 'As-doped 21.4 % cell · S ≈ 5 cm/s', Z0.logS_as, 'warm');
  // right: Voc of the best cells of the Mg series, measured against the one-S model (columns from 700 mV)
  const Rg = new THREE.Group(); Rg.position.set(2.05, -.1, 0); v.rig.add(Rg); const rig0 = v.rig; v.rig = Rg;
  const ser = Z0.series, A = Viz.axes(v, { size: [3.2, 2.2, 1.0], x: { lo: -.6, hi: 4.6, ticks: [0, 1, 2, 3, 4], fmt: t => 'x ' + ser[t].x.toFixed(2).replace(/^0/, '').replace('.00', '0'), label: 'Mg fraction (MgₓZn₁₋ₓO)' }, y: { lo: 700, hi: 900, ticks: [700, 750, 800, 850, 900], label: 'Voc (mV)' }, z: { lo: 0, hi: 2 } });
  const items = []; ser.forEach((r, i) => { items.push({ x: i, y: r.voc_best, z: .6, color: 'ink', r, kind: 'measured best cell' }); items.push({ x: i, y: r.voc_model, z: 1.4, color: 'cyan', r, kind: 'model, shared S = 10⁵ cm/s' }); });
  const bars = Viz.bars(v, A, items, { width: .16, depth: .16 });
  v.rig = rig0;
  let cv = -1;
  v.update = (vv, t, dt) => {
    const h = Math.min(.05, (dt || 16) / 1000);
    if (Math.abs(vv.p - cv) > 1e-4) { cv = vv.p; bars.draw(ease(vv.p)); }
    for (const b of [cu, as]) {
      b.acc += Math.max(0, b.logS - .5) * 9 * h;               // spark rate grows with log S
      while (b.acc >= 1) { b.acc -= 1; const s = b.sp.find(q => q.life <= 0); if (s) { s.life = 1; s.x = (R() - .5) * 1.25; s.z = (R() - .5) * 1.25; } }
      b.sp.forEach((s, k) => { if (s.life <= 0) { b.im.setMatrixAt(k, Z); return; } s.life -= h * 2.6; const r = .02 + .05 * Math.sin(Math.PI * clamp(s.life, 0, 1)); M4.compose(V3.set(s.x, .08, s.z), Q4, SC.set(r, r, r)); b.im.setMatrixAt(k, M4); });
      b.im.instanceMatrix.needsUpdate = true; b.ifc.material.opacity = .06 + .02 * b.logS;
    }
    return true;
  };
  v.hover = hit => { if (hit.object !== bars.mesh) return null; const it = items[hit.instanceId]; return `<b>x = ${it.r.x.toFixed(2)} · ${it.kind}</b>V<sub>oc</sub> ${it.y.toFixed(1)} mV · XPS ΔE<sub>c</sub> ${sgn(it.r.dEc)} eV`; };
}, { camera: [-.2, 1.8, 7.4], target: [-.5, -.25, 0], fov: 34, rot: .1, tilt: .03, aspect: 2 });

/* ======================================================================== 06 design staircase */
Viz.view('[data-viz="design"]', v => {
  const Dd = D.design, st = Dd.steps, nCol = st.length + 4;
  const A = Viz.axes(v, { size: [6.2, 2.6, 1.0], x: { lo: -.6, hi: nCol - .4, ticks: [] }, y: { lo: 16.5, hi: 27, ticks: [17, 19, 21, 23, 25, 27], label: 'model efficiency (%)' }, z: { lo: 0, hi: 1 } });
  const parts = [], picks = [], W = .62 * 6.2 / nCol;
  const box = (i, y0, y1, key, o = {}) => { const a = A.map(i, y0, .5), b = A.map(i, y1, .5); const hgt = Math.max(.012, Math.abs(b.y - a.y)); const m = new THREE.Mesh(new THREE.BoxGeometry(W, hgt, .62), Viz.mat(key, { emissive: key, emissiveIntensity: o.glow ?? .25, roughness: .35 })); m.position.set(a.x, (a.y + b.y) / 2, 0); m.userData.info = o.info; v.rig.add(m); picks.push(m); parts.push({ mesh: m, from: [0, 1.6, 0], delay: i / nCol * .55, span: .45 }); return m; };
  let lvl = Dd.eta0; const names = ['calibrated\ncell'];
  box(0, lvl - .06, lvl + .06, 'ink', { glow: .2, info: `<b>Model baseline</b>${lvl.toFixed(2)} % (the calibrated fit, R<sub>s</sub> 0, no radiative term)` });
  st.forEach((s, k) => { const i = k + 1, y0 = lvl, y1 = lvl + s.d; box(i, Math.min(y0, y1), Math.max(y0, y1), s.d >= 0 ? 'cyan' : 'hot', { info: `<b>${s.name}: ${s.detail}</b>${s.d >= 0 ? '+' : '−'}${Math.abs(s.d).toFixed(2)} points` }); names.push(['remove\ncliff', 'τ 300 ns', 'N_A ×3', 'back\n0.30 eV', 'optics', 'non-\nadditivity'][k]); lvl = y1; });
  const iC = st.length + 1; box(iC, Dd.cons_ideal - .06, Dd.cons_ideal + .06, 'green', { glow: .4, info: `<b>Conservative design, no R<sub>s</sub>/R<sub>sh</sub></b>${Dd.cons_ideal.toFixed(2)} % (simulated)` }); names.push('design\n(ideal)');
  box(iC + 1, Dd.cons, Dd.cons_ideal, 'hot', { info: `<b>R<sub>s</sub> 0.45, R<sub>sh</sub> 2500 Ω cm²</b>${Dd.penalty.toFixed(2)} points` }); names.push('Rs, Rsh');
  const fin = box(iC + 2, Dd.cons - .1, Dd.cons + .1, 'green', { glow: .9, info: `<b>Conservative design, penalised</b>Sesame ${Dd.cons.toFixed(2)} % (${Dd.cons_voc.toFixed(1)} mV) · SCAPS ${Dd.scaps.toFixed(2)} % (${Dd.scaps_voc.toFixed(1)} mV)` }); names.push('design');
  const ex = Viz.exploded(v, parts);
  // the calibrated baseline with the same penalties, as a plane across the staircase
  const pb = A.map(0, Dd.baseline_pen, 0), plane = new THREE.Mesh(new THREE.PlaneGeometry(6.2, 1.0), Viz.mat('violet', { opacity: .22, side: THREE.DoubleSide, depthWrite: false, emissive: 'violet', emissiveIntensity: .3 })); plane.rotation.x = -Math.PI / 2; plane.position.y = pb.y; v.rig.add(plane);
  lab(v, `calibrated baseline, same penalties: ${Dd.baseline_pen.toFixed(2)} %`, [-1.35, pb.y + .14, .55], { color: 'violet', weight: 700, px: 20 });
  lab(v, `SCAPS ${Dd.scaps.toFixed(2)} % · Sesame ${Dd.cons.toFixed(2)} %`, [fin.position.x - .35, fin.position.y + .42, 0], { color: 'green', weight: 800, px: 24, bg: null });
  names.forEach((t, i) => lab(v, t, [A.map(i, 16.5, 1).x, A.map(0, 16.5, 0).y - .32, .62], { px: 22, scale: .085, color: 'ink' }));
  // connectors between levels
  let l2 = Dd.eta0; const conn = [[0, l2]]; st.forEach((s, k) => { l2 += s.d; conn.push([k + 1, l2]); }); conn.push([iC, Dd.cons_ideal], [iC + 1, Dd.cons_ideal], [iC + 1, Dd.cons], [iC + 2, Dd.cons]);
  for (let k = 0; k < conn.length - 1; k++) { const [i0, y0] = conn[k], [i1, y1] = conn[k + 1]; if (i0 === i1) continue; const a = A.map(i0, y0, .5), b = A.map(i1, y1 === y0 ? y0 : y0, .5); Viz.line(v, [[a.x + W / 2, a.y, -.31], [b.x - W / 2, a.y, -.31]], 'muted', { opacity: .7 }); }
  v.pickables.push(...picks);
  let cv = -1; v.update = vv => { if (Math.abs(vv.p - cv) < 1e-4) return false; cv = vv.p; ex.draw(vv.p); plane.material.opacity = .22 * sstep(.6, 1, vv.p); return true; };
  v.hover = hit => hit.object.userData.info || null;
}, { camera: [.9, 1.3, 6.9], target: [0, 0, 0], fov: 34, rot: -.14, tilt: .04, aspect: 2 });

/* ======================================================================== 07 solvers */
Viz.view('[data-viz="solvers"]', v => {
  const SV = D.solvers.dark, cols = ['hot', 'cyan', 'violet', 'green'];
  const A = Viz.axes(v, { size: [4.2, 2.6, 2.4], x: { lo: .28, hi: .97, ticks: [.3, .5, .7, .9], fmt: t => t.toFixed(1), label: 'voltage (V)' }, y: { lo: -5, hi: 2, ticks: [-4, -2, 0, 2], fmt: t => '10' + sup(t), label: 'J dark (mA/cm²)' }, z: { lo: 0, hi: 4, ticks: [.5, 1.5, 2.5, 3.5], fmt: t => sgn(SV[Math.floor(t)].dEc) + ' eV' } });
  const rib = SV.map((c, k) => Viz.ribbon(v, A, c.V, c.sesame.map(Math.log10), { z: k + .5, width: .22, color: cols[k], name: `Sesame, ΔEc ${sgn(c.dEc)} eV`, unit: 'mA/cm²', skirtOpacity: .1 }));
  const nP = SV.reduce((a, c) => a + c.V.length, 0), dots = inst(v, sphereG(), Viz.mat('ink', { emissive: 'ink', emissiveIntensity: .3 }), nP); v.pickables.push(dots); const ref = [];
  SV.forEach((c, k) => c.V.forEach((V, i) => { const q = A.map(V, Math.log10(c.scaps[i]), k + .5).add(V3.set(0, 0, .14)); M4.compose(q, Q4, SC.set(.042, .042, .042)); dots.setMatrixAt(ref.length, M4); ref.push([k, i]); }));
  const cur = new THREE.Mesh(new THREE.PlaneGeometry(2.4, 2.6), Viz.mat('warm', { opacity: .14, side: THREE.DoubleSide, depthWrite: false, emissive: 'warm', emissiveIntensity: .5 })); cur.rotation.y = Math.PI / 2; v.rig.add(cur);
  const edge = new THREE.Mesh(new THREE.BoxGeometry(.012, 2.6, .012), Viz.mat('warm', { emissive: 'warm', emissiveIntensity: .8 })); edge.position.z = 1.2; v.rig.add(edge);
  let x = A.map(.6, 0, 0).x, cv = -1;
  v.update = vv => {
    let ch = false; if (Math.abs(vv.p - cv) > 1e-4) { cv = vv.p; rib.forEach(r => r.draw(ease(vv.p))); dots.visible = vv.p > .9; ch = true; }
    const tx = A.map(P.sweep.V ?? .6, 0, 0).x; if (Math.abs(tx - x) > 1e-4) { x += (tx - x) * .12; ch = true; } cur.position.set(x, 0, 0); edge.position.x = x; return ch;
  };
  v.hover = hit => { if (hit.object === dots) { const [k, i] = ref[hit.instanceId], c = SV[k]; return `<b>SCAPS, ΔEc ${sgn(c.dEc)} eV</b>${c.V[i].toFixed(2)} V · ${c.scaps[i].toPrecision(3)} mA/cm² (Sesame ${c.sesame[i].toPrecision(3)})`; } const ud = hit.object.userData; if (!ud.xs) return null; const i = Viz.ribbonIndex(hit, A); return `<b>${ud.series}</b>${ud.xs[i].toFixed(2)} V · ${Math.pow(10, ud.ys[i]).toPrecision(3)} mA/cm²`; };
}, { camera: [2.1, 1.4, 6.6], target: [0, -.1, 0], fov: 32 });

/* ======================================================================== 08 ZnSe collapse map */
Viz.view('[data-viz="znse"]', v => {
  const Zs = D.znse, ns = Zs.sets.length;
  const A = Viz.axes(v, { size: [5.0, 2.4, 3.2], x: { lo: -.12, hi: .82, ticks: [0, .2, .4, .6, .8], fmt: t => (t > 0 ? '+' : '') + t.toFixed(1), label: 'ZnSe/absorber ΔEc (eV)' }, y: { lo: 0, hi: 25, ticks: [0, 5, 10, 15, 20, 25], label: 'efficiency (%)' }, z: { lo: 0, hi: ns } });
  const rib = [], blocked = [];
  Zs.sets.forEach((s, k) => {
    const key = s.label.includes('10¹⁷') ? 'violet' : 'cyan', xs = Zs.dEc, ys = s.eta.map(e => e ?? 0);
    rib.push(Viz.ribbon(v, A, xs, ys, { z: k + .5, width: .22, color: key, name: s.label, unit: '%', skirtOpacity: .12 }));
    s.eta.forEach((e, i) => { if (e == null) blocked.push(A.map(xs[i], .4, k + .5)); });
    lab(v, s.label, A.map(.84, ys[0] * 0 + 1, k + .5).add(V3.set(.35, 0, 0)).toArray(), { px: 17, scale: .066 });
  });
  const bl = inst(v, new THREE.BoxGeometry(1, 1, 1), Viz.mat('hot', { emissive: 'hot', emissiveIntensity: .6 }), blocked.length); blocked.forEach((p, i) => { M4.compose(p, Q4, SC.set(.06, .06, .06)); bl.setMatrixAt(i, M4); }); bl.instanceMatrix.needsUpdate = true;
  const x0 = A.map(Zs.dft[0] - Zs.dft[1], 0, 0).x, x1 = A.map(Math.min(.82, Zs.dft[0] + Zs.dft[1]), 0, 0).x, xc = A.map(Zs.dft[0], 0, 0).x;
  const band = new THREE.Mesh(new THREE.BoxGeometry(x1 - x0, 2.4, 3.2), Viz.mat('warm', { opacity: .1, depthWrite: false, emissive: 'warm', emissiveIntensity: .3 })); band.position.set((x0 + x1) / 2, 0, 0); v.rig.add(band);
  const mid = new THREE.Mesh(new THREE.PlaneGeometry(3.2, 2.4), Viz.mat('warm', { opacity: .3, side: THREE.DoubleSide, depthWrite: false, emissive: 'warm', emissiveIntensity: .5 })); mid.rotation.y = Math.PI / 2; mid.position.x = xc; v.rig.add(mid);
  lab(v, 'DFT +0.55 ± 0.3 eV', [xc, 1.5, -1.6], { color: 'warm', weight: 800, px: 24, bg: null });
  lab(v, 'harmless up to +0.20 to +0.40 eV', A.map(.1, 24.5, 0).toArray(), { color: 'ink', px: 20 });
  let cv = -1; v.update = vv => { if (Math.abs(vv.p - cv) < 1e-4) return false; cv = vv.p; rib.forEach(r => r.draw(ease(vv.p))); bl.visible = vv.p > .9; return true; };
  v.hover = hit => { const ud = hit.object.userData; if (!ud.xs) return null; const i = Viz.ribbonIndex(hit, A), set = Zs.sets.find(s => s.label === ud.series), st = set ? set.status[i] : 'ok'; return `<b>${ud.series}</b>ΔEc ${sgn(ud.xs[i])} eV · ${st === 'ok' ? 'η ' + ud.ys[i].toFixed(2) + ' %' : st}`; };
}, { camera: [3.4, 2.6, 6.8], target: [0, -.2, 0], fov: 34, aspect: 2 });

window.__body = true;
