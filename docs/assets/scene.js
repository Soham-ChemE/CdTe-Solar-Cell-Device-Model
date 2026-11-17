/* Hero: the 21.4 % cell as a 3D layer stack that becomes its own band diagram.
   Stack (stylised thicknesses, true order): glass | FTO | ZnO | As-doped CdSeTe -> CdTe (graded) | back contact.
   Photons enter through the glass and are absorbed in the absorber (mostly near the front), each creating an electron-hole
   pair; electrons drift to the ZnO front, holes to the back contact. Electrons reaching the ZnO/CdSeTe interface recombine
   there (a spark along the buffer-CB -> absorber-VB path) with a probability that grows with log S at the current offset.
   Scroll (SITE.hero.t, scrubbed by site.js): 0-0.36 the slabs deform into the band-gap volumes between Ec and Ev; 0.42-0.88
   the conduction-band step at the interface moves from the published +0.10 eV spike to the fitted -0.30 eV cliff, S following
   the identifiability ridge (ident_profile.csv via window.CDTE.profile; window.PAGE.heroState is the shared timeline).
   Band shapes away from the interface (bending, grading, back barrier) are schematic; the step and S are the data.
   The stage mounts when the hero is near the viewport and is disposed when it is far away, then rebuilt on return. */
import { THREE, createStage, cameraPath, makeLabel, redrawLabel, palette } from './three-kit.js?v=f87cbbf5a1';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { Line2 } from 'three/addons/lines/Line2.js';
import { LineMaterial } from 'three/addons/lines/LineMaterial.js';
import { LineGeometry } from 'three/addons/lines/LineGeometry.js';

const D = window.CDTE, S = window.SITE, P = window.PAGE, reduced = S.reduced, phone = S.phone;
const clamp = (v, a, b) => Math.min(b, Math.max(a, v)), lerp = (a, b, t) => a + (b - a) * t;
const sstep = (a, b, x) => { const t = clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };
const mulberry = a => () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };

/* ---------- geometry (scene units) and schematic band energies (eV, relative to E_F) */
const L = { glass: [-6.15, -4.55], fto: [-4.55, -3.97], zno: [-3.97, -3.35], abs: [-3.35, 3.35], back: [3.35, 3.95] };
const XI = L.abs[0], ZW = 2.0, YS = 1.8, K = 1.5, E0 = 0.2, EFLOOR = -1.55;
const yE = E => K * (E - E0);
const ua = x => clamp((x - L.abs[0]) / (L.abs[1] - L.abs[0]), 0, 1);
const EcAbs = x => { const t = ua(x); let e = 1.32 - .70 * Math.pow(Math.max(0, 1 - t / .24), 2); const b = Math.max(0, (t - .86) / .14); return e - .32 * b * b; };
const EgAbs = x => 1.41 + .09 * sstep(.08, .7, ua(x));               // CdSeTe front gap 1.41 eV grading to CdTe (schematic)
const EvAbs = x => EcAbs(x) - EgAbs(x);
const EcZnO = (x, dEc) => lerp(.08, EcAbs(XI) + dEc, clamp((x - L.zno[0]) / (L.zno[1] - L.zno[0]), 0, 1));
const EC_FTO = -.08;
// ridge log S at a continuous offset (linear between the simulated offsets of the profile)
const PROF = [...D.profile].sort((a, b) => a.dEc - b.dEc);
const ridgeAt = d => { let k = 1; while (k < PROF.length - 1 && PROF[k].dEc < d) k++; const a = PROF[k - 1], b = PROF[k]; return lerp(a.logS, b.logS, clamp((d - a.dEc) / (b.dEc - a.dEc), 0, 1)); };
const pRec = d => Math.min(.92, Math.pow(clamp((ridgeAt(d) - .3) / 5.6, .02, 1), 1.2));

function mount(canvas) {
  const st = createStage(canvas, { fov: 34, bloom: { strength: .42, radius: .5, threshold: .92 }, exposure: 1.0, envIntensity: .45, stage: { dark: '#0b1220', light: '#eef2f7' }, maxDpr: phone ? 1.5 : 1.75 });
  if (st.failed) return null;
  window.__heroReady = true;
  const { scene, camera, renderer } = st; const pal = () => st.pal;
  const ctr = new OrbitControls(camera, canvas); ctr.enableDamping = true; ctr.enableZoom = false; ctr.enablePan = false; ctr.enabled = !phone; ctr.minPolarAngle = .55; ctr.maxPolarAngle = 1.75; ctr.rotateSpeed = .5;
  const hemi = new THREE.HemisphereLight(0xffffff, 0x223355, .85), dl = new THREE.DirectionalLight(0xffffff, 1.6); dl.position.set(-6, 9, 8); const fill = new THREE.DirectionalLight(0xffffff, .5); fill.position.set(6, -2, 6); scene.add(hemi, dl, fill);
  const G = new THREE.Group(); scene.add(G);
  // labels live in an overlay scene drawn after the post-processing chain, without tone mapping or bloom, so they keep their
  // exact colours and stay crisp in both themes
  const LS = new THREE.Scene(), baseRender = st.render;
  st.render = () => { baseRender(); const r = st.renderer, tm = r.toneMapping, ac = r.autoClear; r.toneMapping = THREE.NoToneMapping; r.autoClear = false; r.render(LS, camera); r.autoClear = ac; r.toneMapping = tm; };
  const disposables = [];

  /* ---------- deformable slabs: a box per layer whose top and bottom faces move from the slab faces to Ec(x) and Ev(x) */
  function slab(key, nx, mat) {
    const [x0, x1] = L[key], g = new THREE.BoxGeometry(x1 - x0, 2 * YS, 2 * ZW, nx, 1, 1); g.translate((x0 + x1) / 2, 0, 0);
    const pos = g.attributes.position, n = pos.count, xs = new Float32Array(n), top = new Uint8Array(n), base = Float32Array.from(pos.array);
    for (let i = 0; i < n; i++) { xs[i] = pos.getX(i); top[i] = pos.getY(i) > 0 ? 1 : 0; }
    const mesh = new THREE.Mesh(g, mat); mesh.renderOrder = 1; G.add(mesh); return { key, g, pos, xs, top, base, mesh, mat };
  }
  function morph(s, m, topFn, botFn, dx = 0) {
    for (let i = 0; i < s.xs.length; i++) { const x = s.xs[i], y0 = s.base[3 * i + 1], y1 = s.top[i] ? topFn(x) : botFn(x); s.pos.setXYZ(i, x + dx, lerp(y0, y1, m), s.base[3 * i + 2]); }
    s.pos.needsUpdate = true; s.g.computeVertexNormals(); s.g.computeBoundingSphere();
  }
  const M = (o = {}) => new THREE.MeshStandardMaterial({ roughness: .35, metalness: .08, transparent: true, depthWrite: false, side: THREE.DoubleSide, ...o });
  const glass = slab('glass', 1, new THREE.MeshPhysicalMaterial({ roughness: .06, metalness: 0, transmission: 0, transparent: true, opacity: .28, clearcoat: 1, clearcoatRoughness: .1, depthWrite: false, side: THREE.DoubleSide }));
  const fto = slab('fto', 2, M({ opacity: .5 })), zno = slab('zno', 2, M({ opacity: .55 }));
  const absM = M({ vertexColors: true, opacity: .62, roughness: .5 }); const abs = slab('abs', 64, absM);
  const back = slab('back', 1, new THREE.MeshStandardMaterial({ roughness: .5, metalness: .45, transparent: true, opacity: .9, envMapIntensity: .6 }));
  const absCol = new Float32Array(abs.pos.count * 3); abs.g.setAttribute('color', new THREE.BufferAttribute(absCol, 3));
  const paintSlabs = () => {
    const p = pal(), c0 = new THREE.Color(p.rose), c1 = new THREE.Color(p.warm), c = new THREE.Color();
    for (let i = 0; i < abs.xs.length; i++) { c.copy(c0).lerp(c1, sstep(.05, .75, ua(abs.xs[i]))); absCol[3 * i] = c.r; absCol[3 * i + 1] = c.g; absCol[3 * i + 2] = c.b; }
    abs.g.attributes.color.needsUpdate = true;
    glass.mat.color.set(p.acrylic); fto.mat.color.set(p.blue); zno.mat.color.set(p.green); back.mat.color.set(p.steel);
  };

  /* ---------- band ribbons (sheets across z) peeled off the slab faces: Ec and Ev of the absorber, Ec of ZnO and FTO */
  function sheet(x0, x1, nx, color, opacity = .8) {
    const g = new THREE.PlaneGeometry(x1 - x0, 2 * ZW, nx, 1); g.rotateX(-Math.PI / 2); g.translate((x0 + x1) / 2, 0, 0);
    const mat = new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: .55, roughness: .3, metalness: .2, transparent: true, opacity: 0, side: THREE.DoubleSide, depthWrite: false });
    const mesh = new THREE.Mesh(g, mat); mesh.renderOrder = 2; G.add(mesh); const pos = g.attributes.position; const xs = new Float32Array(pos.count); for (let i = 0; i < pos.count; i++) xs[i] = pos.getX(i);
    return { g, pos, xs, mat, mesh, opacity, set(fn, op) { for (let i = 0; i < xs.length; i++) pos.setY(i, fn(xs[i])); pos.needsUpdate = true; g.computeVertexNormals(); mat.opacity = op * opacity; mesh.visible = op > .01; } };
  }
  const shEcA = sheet(L.abs[0], L.abs[1], 96, 0xffffff, .62), shEvA = sheet(L.abs[0], L.abs[1], 96, 0xffffff, .62), shEcZ = sheet(L.zno[0], L.zno[1], 4, 0xffffff, .9), shEcF = sheet(L.fto[0], L.fto[1], 2, 0xffffff, .55);

  /* ---------- fat lines (Line2): front edges of the ribbons, the interface step, E_F, the recombination path */
  const lines = [];
  function line(n, o = {}) {
    const geo = new LineGeometry(); geo.setPositions(new Float32Array(n * 3));
    const mat = new LineMaterial({ color: 0xffffff, linewidth: o.w || 3, transparent: true, opacity: 1, dashed: !!o.dashed, dashSize: o.dash || .12, gapSize: o.gap || .1, depthWrite: false });
    const l = new Line2(geo, mat); l.renderOrder = 5; l.frustumCulled = false; G.add(l); const o2 = { l, geo, mat, n, key: o.key, hdr: o.hdr ?? 1.6 }; lines.push(o2); return o2;
  }
  const setLine = (ln, pts, op = 1) => { const a = new Float32Array(pts.length * 3); pts.forEach((p, i) => { a[3 * i] = p[0]; a[3 * i + 1] = p[1]; a[3 * i + 2] = p[2]; }); ln.geo.setPositions(a); if (ln.mat.dashed) ln.l.computeLineDistances(); ln.mat.opacity = op; ln.l.visible = op > .01; };
  const lEcA = line(97, { key: 'warm', w: 3.2 }), lEvA = line(97, { key: 'warm', w: 3.2 }), lEcZ = line(2, { key: 'green', w: 4.5, hdr: 2 }), lEcF = line(2, { key: 'blue', w: 3 });
  const lStep = line(2, { key: 'hot', w: 6, hdr: 2.4 }), lEF = line(2, { key: 'muted', w: 1.5, dashed: true, dash: .18, gap: .14, hdr: 1 });
  const ARCZ = phone ? [0] : [-1.2, 0, 1.2, ZW]; const lArc = ARCZ.map(z => line(25, { key: 'rose', w: z === ZW ? 3 : 1.6, dashed: true, dash: .08, gap: .06, hdr: 2.2 }));
  const paintLines = () => { const p = pal(), dark = st.dark; for (const ln of lines) { ln.mat.color.set(p[ln.key] || ln.key); if (dark) ln.mat.color.multiplyScalar(ln.hdr); } };

  /* ---------- light: volumetric beams through the glass, and photons */
  const beamG = new THREE.CylinderGeometry(.05, .05, 1, 8, 1, true); beamG.rotateZ(Math.PI / 2);
  const beamM = new THREE.MeshBasicMaterial({ transparent: true, opacity: .16, blending: THREE.AdditiveBlending, depthWrite: false });
  const NB = phone ? 4 : 7, beams = new THREE.InstancedMesh(beamG, beamM, NB); G.add(beams);
  const rnd = mulberry(11), BY = [], BZ = []; for (let i = 0; i < NB; i++) { BY.push((rnd() * 2 - 1) * YS * .75); BZ.push((rnd() * 2 - 1) * ZW * .8); }
  const sph = new THREE.SphereGeometry(1, 10, 8);
  const pm = (o = {}) => new THREE.MeshBasicMaterial({ transparent: true, depthWrite: false, ...o });
  const NS = phone ? 90 : 210, NSP = phone ? 70 : 150, NFL = phone ? 40 : 90;
  const photonG = new THREE.CylinderGeometry(1, 1, 1, 6, 1); photonG.rotateZ(Math.PI / 2);
  const photons = new THREE.InstancedMesh(photonG, pm({ blending: THREE.AdditiveBlending }), NS), elec = new THREE.InstancedMesh(sph, pm(), NS), hole = new THREE.InstancedMesh(sph, pm(), NS);
  const sparks = new THREE.InstancedMesh(sph, pm({ blending: THREE.AdditiveBlending }), NSP), flashG = new THREE.CylinderGeometry(1, 1, 1, 6, 1), flashes = new THREE.InstancedMesh(flashG, pm({ blending: THREE.AdditiveBlending, opacity: .8 }), NFL);
  [photons, elec, hole, sparks, flashes].forEach(im => { im.frustumCulled = false; im.renderOrder = 6; G.add(im); });
  const paintParticles = () => {
    const p = pal(), k = st.dark ? 2.4 : 1.25;
    photons.material.color.set(p.yellow).multiplyScalar(st.dark ? 1.5 : 1.3); elec.material.color.set(p.cyan).multiplyScalar(st.dark ? 1.7 : 1.15); hole.material.color.set(p.rose).multiplyScalar(st.dark ? 1.5 : 1.15);
    sparks.material.color.set(st.dark ? '#ffc2d1' : p.rose).multiplyScalar(st.dark ? 2.6 : 1.8); flashes.material.color.set(p.yellow).multiplyScalar(st.dark ? 1.15 : 1); beamM.color.set(p.yellow); beamM.opacity = st.dark ? .14 : .22;
  };
  // interface sheet (glows with recent recombination)
  const ifM = new THREE.MeshBasicMaterial({ transparent: true, opacity: .1, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide });
  const ifSheet = new THREE.Mesh(new THREE.PlaneGeometry(2 * ZW, 1), ifM); ifSheet.rotation.y = Math.PI / 2; ifSheet.position.x = XI; ifSheet.renderOrder = 4; G.add(ifSheet);
  const groundG = new THREE.PlaneGeometry(26, 14), groundM = new THREE.MeshStandardMaterial({ roughness: .95, metalness: 0, transparent: true, opacity: .5, depthWrite: false });
  const ground = new THREE.Mesh(groundG, groundM); ground.rotation.x = -Math.PI / 2; ground.position.y = -3.0; ground.renderOrder = 0; G.add(ground);

  /* ---------- labels */
  const labs = [];
  const lab = (t, o = {}) => { const s = makeLabel(t, { px: 30, scale: phone ? .19 : .15, color: 'muted', bg: false, weight: 800, ...o }); LS.add(s); labs.push(s); return s; };
  const LL = [['glass', 'glass', 'muted'], ['fto', 'FTO', 'blue'], ['zno', 'ZnO', 'green'], ['abs', 'As-doped CdSeTe → CdTe', 'warm'], ['back', 'back contact', 'steel']].map(([k, t, c]) => ({ k, s: lab(t, { color: c, weight: 700, px: 28 }) }));
  const lSun = lab('sunlight', { color: 'yellow', weight: 700, px: 28 }), lEc = lab('Ec · conduction band', { color: 'ink', weight: 600 }), lEv = lab('Ev · valence band', { color: 'ink', weight: 600 }), lEf = lab('EF', { color: 'muted' }), lBack = lab('back barrier 0.50 eV', { color: 'muted' }), lRec = lab('interface recombination', { color: 'rose', weight: 700 });
  const lStepLab = lab('+0.10 eV spike', { color: 'ink', weight: 800, px: 32, bg: null });
  let stepText = '';

  /* ---------- particles: one slot = photon, then an electron-hole pair */
  const R = mulberry(5), N = NS;
  const sl = Array.from({ length: N }, () => ({ st: 2, wait: R() * 2.5, px: 0, xa: 0, yS: 0, z: 0, ex: 0, eAlive: false, hx: 0, hAlive: false, yeS: 0, yhS: 0, eDone: false, eRec: false, eFade: 1 }));
  const SP = Array.from({ length: NSP }, () => ({ life: 0, z: 0, s: 0 })), FL = Array.from({ length: NFL }, () => ({ life: 0, x: 0, z: 0 }));
  let spk = 0, flk = 0, activity = 0;
  const arcPt = (s, z, out, h) => { const a = [XI - .02, h.yZ + .02], b = [XI + .02, h.yV], c = [XI - .95, (h.yZ + h.yV) / 2]; const q = 1 - s; out.set(q * q * a[0] + 2 * q * s * c[0] + s * s * b[0], q * q * a[1] + 2 * q * s * c[1] + s * s * b[1], z); return out; };
  function newSlot(o) { o.st = 0; o.px = -10.5 - R() * 2; o.xa = clamp(XI + .08 + (-Math.log(1 - R() * .985)) * 1.05, XI + .08, L.abs[1] - .15); o.yS = (R() * 2 - 1) * YS * .8; o.z = lerp((R() * 2 - 1) * ZW * .85, -ZW * .9 + R() * ZW * 1.1, H.m); /* band phase: keep the front edge (Ec, Ev, the step) clear */ o.yeS = (R() * 2 - 1) * YS * .8; o.yhS = (R() * 2 - 1) * YS * .8; o.eDone = o.eRec = false; o.eFade = 1; o.jit = (R() - .5) * .3; }
  const tmpM = new THREE.Matrix4(), tmpV = new THREE.Vector3(), Q = new THREE.Quaternion(), one = new THREE.Vector3(1, 1, 1), sc = new THREE.Vector3(), zero = new THREE.Matrix4().makeScale(0, 0, 0);
  // band geometry helpers at the current morph (m) and offset (dEc)
  const H = { m: 0, dEc: .1, yZ: 0, yV: 0 };
  const yEcAt = x => x >= XI ? yE(EcAbs(x)) : x >= L.zno[0] ? yE(EcZnO(x, H.dEc)) : yE(EC_FTO);
  function step(dt) {
    const m = H.m, sp = 9, pr = pRec(H.dEc);
    for (let i = 0; i < N; i++) {
      const o = sl[i];
      if (o.st === 2) { o.wait -= dt; if (o.wait <= 0) newSlot(o); photons.setMatrixAt(i, zero); elec.setMatrixAt(i, zero); hole.setMatrixAt(i, zero); continue; }
      if (o.st === 0) {
        o.px += sp * dt; const yb = lerp(o.yS, (yE(EcAbs(o.xa)) + yE(EvAbs(o.xa))) / 2 + o.jit, m);
        if (o.px >= o.xa) { o.st = 1; o.ex = o.hx = o.xa; o.eAlive = o.hAlive = true; photons.setMatrixAt(i, zero); const f = FL[flk++ % NFL]; f.life = 1; f.x = o.xa; f.z = o.z; f.y = yb; }
        else { if (o.px < lerp(-11, -7.5, m) || (m > .5 && i % 3 !== 0)) { photons.setMatrixAt(i, zero); elec.setMatrixAt(i, zero); hole.setMatrixAt(i, zero); continue; } const len = .45, fade = o.px > XI ? clamp(1 - (o.px - XI) / Math.max(.3, o.xa - XI) * .6, .3, 1) : 1; tmpV.set(o.px, yb, o.z); sc.set(len, .014 * fade, .014 * fade); tmpM.compose(tmpV, Q, sc); photons.setMatrixAt(i, tmpM); }
        elec.setMatrixAt(i, zero); hole.setMatrixAt(i, zero); continue;
      }
      // electron: drifts to the front, faster in the depletion region
      if (o.eAlive) {
        const v = o.ex > XI ? 1.1 + 3.2 * (1 - sstep(0, .3, ua(o.ex))) : 2.4; const xPrev = o.ex; o.ex -= v * dt;
        if (xPrev >= XI && o.ex < XI && !o.eDone) { o.eDone = true; if (R() < pr) { o.eRec = true; o.eAlive = false; const s = SP[spk++ % NSP]; s.life = 1; s.z = o.z; s.s = 0; activity = Math.min(1, activity + .18); } }
        if (o.ex < L.fto[0] + .05) o.eAlive = false;
        if (o.eAlive) { const y = lerp(o.yeS, yEcAt(o.ex) + .07, m); tmpV.set(o.ex, y, o.z); const r = .062; sc.set(r, r, r); tmpM.compose(tmpV, Q, sc); elec.setMatrixAt(i, tmpM); } else elec.setMatrixAt(i, zero);
      } else elec.setMatrixAt(i, zero);
      // hole: drifts to the back contact
      if (o.hAlive) {
        o.hx += (.95 + .5 * (1 - sstep(0, .3, ua(o.hx)))) * dt; if (o.hx > L.abs[1] - .02) o.hAlive = false;
        if (o.hAlive) { const y = lerp(o.yhS, yE(EvAbs(o.hx)) - .07, m); tmpV.set(o.hx, y, o.z); const r = .062; sc.set(r, r, r); tmpM.compose(tmpV, Q, sc); hole.setMatrixAt(i, tmpM); } else hole.setMatrixAt(i, zero);
      } else hole.setMatrixAt(i, zero);
      if (!o.eAlive && !o.hAlive) { o.st = 2; o.wait = R() * .6; }
    }
    // sparks run down the recombination path (band phase) or flash on the interface plane (stack phase)
    for (let k = 0; k < NSP; k++) {
      const s = SP[k]; if (s.life <= 0) { sparks.setMatrixAt(k, zero); continue; }
      s.life -= dt * 2.4; s.s = Math.min(1, s.s + dt * 3.2);
      arcPt(s.s, s.z, tmpV, H);                      // band-phase position on the buffer-CB -> absorber-VB path
      const xs = XI - .03, ys = lerp(-YS * .8, YS * .8, ((k * 37) % 100) / 100); tmpV.set(lerp(xs, tmpV.x, m), lerp(ys, tmpV.y, m), s.z);
      const r = .035 + .06 * Math.sin(Math.PI * clamp(s.life, 0, 1)); sc.set(r, r, r); tmpM.compose(tmpV, Q, sc); sparks.setMatrixAt(k, tmpM);
    }
    for (let k = 0; k < NFL; k++) {
      const f = FL[k]; if (f.life <= 0) { flashes.setMatrixAt(k, zero); continue; } f.life -= dt * 4.5;
      const yc = yE(EcAbs(f.x)), yv = yE(EvAbs(f.x)), hgt = lerp(.35, yc - yv, m), cy = lerp(f.y, (yc + yv) / 2, m), w = .007 * clamp(f.life, 0, 1) + .002;
      tmpV.set(f.x, cy, f.z); sc.set(w, hgt * clamp(f.life * 1.4, 0, 1), w); tmpM.compose(tmpV, Q, sc); flashes.setMatrixAt(k, tmpM);
    }
    activity *= Math.pow(.25, dt);
    [photons, elec, hole, sparks, flashes].forEach(im => im.instanceMatrix.needsUpdate = true);
  }

  /* ---------- per-state geometry */
  let lastM = -1, lastD = 99;
  function applyBands(m, dEc) {
    H.m = m; H.dEc = dEc; H.yZ = lerp(YS * .2, yE(EcZnO(XI, dEc)), m); H.yV = lerp(-YS * .2, yE(EvAbs(XI)), m);
    const yF = yE(EFLOOR);
    morph(glass, 1, () => YS, () => -YS, -m * 3.2); glass.mat.opacity = .28 * (1 - m); glass.mesh.visible = m < .99;
    morph(fto, m, () => yE(EC_FTO), () => yF); morph(zno, m, x => yE(EcZnO(x, dEc)), () => yF);
    morph(abs, m, x => yE(EcAbs(x)), x => yE(EvAbs(x))); morph(back, m, () => yE(0), () => yF);
    fto.mat.opacity = lerp(.5, .16, m); zno.mat.opacity = lerp(.55, .2, m); absM.opacity = lerp(.62, .1, m); back.mat.opacity = lerp(.9, .55, m);
    const ribbon = sstep(.15, .9, m);
    shEcA.set(x => lerp(YS + .002, yE(EcAbs(x)), m), ribbon); shEvA.set(x => lerp(-YS - .002, yE(EvAbs(x)), m), ribbon);
    shEcZ.set(x => lerp(YS + .002, yE(EcZnO(x, dEc)), m), ribbon); shEcF.set(() => lerp(YS + .002, yE(EC_FTO), m), ribbon);
    const N1 = 96, xa = i => L.abs[0] + (L.abs[1] - L.abs[0]) * i / N1;
    const edge = lerp(.55, 1, ribbon);
    setLine(lEcA, Array.from({ length: N1 + 1 }, (_, i) => [xa(i), lerp(YS, yE(EcAbs(xa(i))), m), ZW]), edge);
    setLine(lEvA, Array.from({ length: N1 + 1 }, (_, i) => [xa(i), lerp(-YS, yE(EvAbs(xa(i))), m), ZW]), edge);
    setLine(lEcZ, [[L.zno[0], lerp(YS, yE(EcZnO(L.zno[0], dEc)), m), ZW], [L.zno[1], lerp(YS, yE(EcZnO(L.zno[1], dEc)), m), ZW]], edge);
    setLine(lEcF, [[L.fto[0], lerp(YS, yE(EC_FTO), m), ZW], [L.fto[1], lerp(YS, yE(EC_FTO), m), ZW]], edge);
    setLine(lStep, [[XI, lerp(YS, yE(EcAbs(XI)), m), ZW + .01], [XI, lerp(YS, yE(EcZnO(XI, dEc)), m), ZW + .01]], ribbon);
    lStep.mat.color.set(dEc > 0 ? pal().hot : pal().green); if (st.dark) lStep.mat.color.multiplyScalar(2.4);
    setLine(lEF, [[L.fto[0], yE(0), ZW], [L.back[1] + .3, yE(0), ZW]], sstep(.5, 1, m) * .9);
    lArc.forEach((ln, j) => { const z = ARCZ[j]; setLine(ln, Array.from({ length: 25 }, (_, i) => { arcPt(i / 24, z, tmpV, H); return [tmpV.x, tmpV.y, z]; }), sstep(.4, 1, m) * (z === ZW ? .95 : .45)); });
    const top = Math.max(H.yZ, lerp(YS, yE(EcAbs(XI)), m)), bot = H.yV; ifSheet.scale.y = Math.max(.05, lerp(2 * YS, top - bot, m)); ifSheet.position.y = lerp(0, (top + bot) / 2, m);
    // labels
    const cx = k => (L[k][0] + L[k][1]) / 2, yTop = 2.35;
    const yFl = yE(EFLOOR) + .28;
    LL.forEach(({ k, s }) => { const zt = k === 'abs' ? 0 : ZW * .4; s.position.set(cx(k) + (k === 'glass' ? -m * 3.2 : 0) + (k === 'fto' ? -m * .1 : 0) + (k === 'abs' ? m * 2.3 : 0), lerp(yTop + (k === 'fto' || k === 'glass' ? .36 : 0), k === 'abs' ? yE(EvAbs(2.3)) - .95 : yFl + (k === 'zno' ? .42 : 0), m), lerp(zt, ZW + .05, m)); s.material.opacity = k === 'glass' ? 1 - m : 1; });
    lSun.position.set(lerp(-8.9, -7.4, m), lerp(.95, yE(.35) + .7, m), 0); lSun.material.opacity = lerp(1, .8, m);
    const lb = sstep(.4, .85, m);
    lEc.position.set(-1.5, yE(EcAbs(-1.5)) - .32, ZW); lEv.position.set(-1.1, yE(EvAbs(-1.1)) + .32, ZW);   // inside the gap, clear of the particles on the bands lEf.position.set(L.back[1] + .65, yE(0), ZW);
    lBack.position.set(2.75, yE(EvAbs(L.abs[1])) - .55, ZW); lRec.position.set(XI - 1.55, (H.yZ + H.yV) / 2 - .15, ZW);
    [lEc, lEv, lEf, lBack, lRec].forEach(s => s.material.opacity = lb);
    lStepLab.position.set(XI - .1, Math.max(H.yZ, yE(EcAbs(XI))) + .62, ZW); lStepLab.material.opacity = sstep(.45, .9, m);
    beams.visible = true;
    for (let i = 0; i < NB; i++) { const x0 = -11, x1 = lerp(XI, XI + .6, m), len = x1 - x0; tmpV.set((x0 + x1) / 2, lerp(BY[i], (yE(EcAbs(XI + .4)) + yE(EvAbs(XI + .4))) / 2 + BY[i] * .25, m), BZ[i]); sc.set(len, lerp(1, .6, m), lerp(1, .6, m)); tmpM.compose(tmpV, Q, sc); beams.setMatrixAt(i, tmpM); }
    beams.instanceMatrix.needsUpdate = true;
  }
  function setStepLabel(near) {
    const p = near, t = p.dEc > 0 ? `${p.dEc > 0 ? '+' : ''}${p.dEc.toFixed(2)} eV spike` : `${p.dEc.toFixed(2).replace('-', '−')} eV cliff`;
    const full = t + (Math.abs(p.dEc + .3) < 1e-6 ? ' · S ≈ 5 cm/s' : '');
    if (full === stepText) return; stepText = full; lStepLab.userData.label.text = full; lStepLab.userData.label.o.color = p.dEc > 0 ? 'hot' : 'green'; redrawLabel(lStepLab, st.dark);
  }

  /* ---------- theme */
  const ground0 = () => { groundM.color.set(st.dark ? '#0b1220' : '#dfe6ef'); groundM.opacity = st.dark ? .55 : .35; };
  const paint = () => { const p = pal(); paintSlabs(); paintLines(); paintParticles(); ifM.color.set(p.rose); [shEcA, shEvA].forEach(s => { s.mat.color.set(p.warm); s.mat.emissive.set(p.warm); }); shEcZ.mat.color.set(p.green); shEcZ.mat.emissive.set(p.green); shEcF.mat.color.set(p.blue); shEcF.mat.emissive.set(p.blue); ground0(); hemi.intensity = .85 * st.lights; dl.intensity = 1.6 * st.lights; fill.intensity = .5 * st.lights; };
  st.onTheme = dark => { labs.forEach(l => redrawLabel(l, dark)); paint(); lastM = -1; st.dirty = true; };
  paint();

  /* ---------- camera paths and layout */
  const wide = () => (canvas.clientWidth / Math.max(1, canvas.clientHeight)) > 1.15;
  const pathW = cameraPath([[-12.0, 6.4, 15.0], [-3.2, 2.4, 16.8], [-4.8, 1.6, 12.6], [-5.4, 1.15, 9.6]], [[-1.0, -.5, 0], [-.4, -.3, 0], [-1.6, -.15, 0], [-2.35, -.1, 0]]);
  const pathN = cameraPath([[-7.5, 5.5, 27.0], [-2.2, 2.5, 25.0], [-3.8, 1.5, 17.0], [-4.6, 1.1, 12.8]], [[-1.0, -2.0, 0], [-.6, -.7, 0], [-2.0, -.3, 0], [-2.6, -.15, 0]]);
  const pos3 = new THREE.Vector3(), tgt3 = new THREE.Vector3(); let dragging = false, dragT = 0;
  canvas.addEventListener('pointerdown', () => { dragging = true; }); const up = () => { if (dragging) dragT = performance.now(); dragging = false; }; addEventListener('pointerup', up);
  ctr.addEventListener('change', () => st.dirty = true);
  const pathAt = T => { const h = P.heroState(T); return h.m * .42 + h.u * .58; };
  const T0 = reduced ? 1 : S.hero.t; const h0 = P.heroState(T0);
  // reduced motion shows the final keyframe with the headline still on screen: slide the view so the cliff sits right of the copy
  const atT = T => { (wide() ? pathW : pathN).at(pathAt(T), pos3, tgt3); if (reduced && wide()) { pos3.x -= 1.3; tgt3.x -= 1.3; } };
  applyBands(h0.m, h0.dEc); setStepLabel(h0.near); atT(T0); camera.position.copy(pos3); ctr.target.copy(tgt3); ctr.update();
  if (reduced) { for (let k = 0; k < 240; k++) step(1 / 30); }
  let lastT = -1, idle = 0;
  st.loop((t, dtMs) => {
    const T = reduced ? 1 : S.hero.t, h = P.heroState(T); let changed = false;
    if (Math.abs(h.m - lastM) > 1e-4 || Math.abs(h.dEc - lastD) > 1e-4) { applyBands(h.m, h.dEc); lastM = h.m; lastD = h.dEc; changed = true; }
    setStepLabel(h.near);
    if (!reduced) { step(Math.min(.05, (dtMs || 16) / 1000)); changed = true; }
    ifM.opacity = lerp(.03, .05, H.m) + .16 * activity;
    atT(T);
    const free = !dragging && performance.now() - dragT > 2500;
    if (free && camera.position.distanceToSquared(pos3) > 1e-6) { camera.position.lerp(pos3, reduced ? 1 : .07); changed = true; }
    if (free) ctr.target.lerp(tgt3, .07);
    ctr.update(); if (dragging) changed = true;
    st.setBloom(.5 + .2 * (S.hero.glow || 0));
    if (Math.abs(T - lastT) > 1e-4) { lastT = T; changed = true; }
    return changed;
  });
  window.__hero = { st, applyBands, H };
  return () => { removeEventListener('pointerup', up); ctr.dispose(); disposables.forEach(d => d.dispose()); [beamG, sph, photonG, flashG].forEach(g => g.dispose()); labs.forEach(l => { l.material.map && l.material.map.dispose(); l.material.dispose(); }); st.dispose(); };
}

/* ---------- lazy mount / dispose by distance from the viewport */
(function () {
  const track = document.querySelector('.hero-track'); let canvas = document.getElementById('heroCanvas'); if (!track || !canvas) return;
  let unmount = null;
  const fail = e => { if (e) console.warn('hero: falling back to the static render', e); const h = document.querySelector('.hero'); h.classList.add('no-webgl'); const fb = h.querySelector('.fallback'); if (fb) fb.src = 'assets/hero_' + (S.isDark() ? 'dark' : 'light') + '.webp'; const ro = document.getElementById('heroReadout'); if (ro) ro.style.opacity = 1; };
  const doMount = () => { if (unmount || document.querySelector('.hero.no-webgl')) return; try { unmount = mount(canvas) || null; } catch (e) { unmount = null; fail(e); return; } if (!unmount) fail(); };
  const doUnmount = () => { if (!unmount) return; unmount(); unmount = null; const fresh = canvas.cloneNode(false); canvas.replaceWith(fresh); canvas = fresh; };
  new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) doMount(); }), { rootMargin: '50% 0px 50% 0px' }).observe(track);
  new IntersectionObserver(es => es.forEach(e => { if (!e.isIntersecting) doUnmount(); }), { rootMargin: '150% 0px 150% 0px' }).observe(track);
})();
