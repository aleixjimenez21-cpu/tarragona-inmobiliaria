// La urna · Test a ciegas 29-N
// Motor de render determinista: escena 3D (Three.js) + postprocesado cinematográfico + rótulos.
// Se controla desde tools/render.js con window.setup(timings) y window.renderFrame(n).
import * as THREE from 'three';

const W = 1080, H = 1920;
const COL = { room: 0x0b0e14, paper: '#EFE6D2', ink: '#141414', amber: '#FFB46B', wax: 0xb3261e };

// ------------------------------------------------------------------ utilidades
function rng(seed) { let a = seed >>> 0; return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lerp = (a, b, t) => a + (b - a) * t;
const smooth = (t) => { t = clamp(t); return t * t * (3 - 2 * t); };
const smoother = (t) => { t = clamp(t); return t * t * t * (t * (t * 6 - 15) + 10); };
const easeOut = (t) => 1 - Math.pow(1 - clamp(t), 3);
const easeIn = (t) => Math.pow(clamp(t), 2);
const range = (t, a, b) => clamp((t - a) / (b - a));
const bell = (t, a, b) => { const u = range(t, a, b); return Math.sin(Math.PI * u) ** 2; };
const DEG = Math.PI / 180;
function mk(w, h) { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; }
const V = (x, y, z) => new THREE.Vector3(x, y, z);
// ruido suave 1D determinista (para respiración de cámara)
function vnoise(x, s) { const i = Math.floor(x), f = x - i; const h = (n) => { const r = Math.sin((n + s * 17.13) * 127.1) * 43758.5453; return r - Math.floor(r); }; const u = f * f * (3 - 2 * f); return lerp(h(i), h(i + 1), u) * 2 - 1; }

// --------------------------------------------------------------- renderer base
const canvas = document.createElement('canvas');
canvas.width = W; canvas.height = H;
document.body.appendChild(canvas);
const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(1);
renderer.setSize(W, H, false);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.NoToneMapping;
renderer.outputColorSpace = THREE.LinearSRGBColorSpace;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x07090d);
scene.fog = new THREE.FogExp2(0x07090d, 0.16);
const camera = new THREE.PerspectiveCamera(32, W / H, 0.02, 14);

// ---------------------------------------------------------------- texturas 2D
const PAPER_SEED = 2911;
function paperCanvas(w, h, seed, opt = {}) {
  const c = mk(w, h), x = c.getContext('2d'), R = rng(seed);
  x.fillStyle = opt.base || COL.paper; x.fillRect(0, 0, w, h);
  // manchas suaves de pulpa
  for (let i = 0; i < 160; i++) {
    const px = R() * w, py = R() * h, r = (0.04 + R() * 0.22) * Math.max(w, h);
    const g = x.createRadialGradient(px, py, 0, px, py, r);
    const light = R() < 0.5;
    g.addColorStop(0, light ? 'rgba(255,251,240,0.05)' : 'rgba(150,120,80,0.028)');
    g.addColorStop(1, 'rgba(0,0,0,0)');
    x.fillStyle = g; x.fillRect(px - r, py - r, 2 * r, 2 * r);
  }
  // fibras
  x.lineCap = 'round';
  const nf = Math.floor(w * h / 220 * (opt.fiber ?? 1));
  for (let i = 0; i < nf; i++) {
    const px = R() * w, py = R() * h, len = 3 + R() * 20 * (w / 1024), a = R() * Math.PI * 2, cu = (R() - 0.5) * 1.2;
    x.strokeStyle = R() < 0.62 ? `rgba(105,84,55,${0.04 + R() * 0.09})` : `rgba(255,253,246,${0.07 + R() * 0.12})`;
    x.lineWidth = 0.4 + R() * 1.1;
    x.beginPath(); x.moveTo(px, py);
    x.quadraticCurveTo(px + Math.cos(a + cu) * len * 0.5, py + Math.sin(a + cu) * len * 0.5, px + Math.cos(a) * len, py + Math.sin(a) * len);
    x.stroke();
  }
  // motas
  for (let i = 0; i < w * h / 3000; i++) { x.fillStyle = `rgba(70,55,35,${0.05 + R() * 0.2})`; const s = 0.6 + R() * 1.6; x.fillRect(R() * w, R() * h, s, s); }
  // bordes envejecidos
  const e = opt.edge ?? 0.18;
  if (e > 0) {
    const m = Math.min(w, h) * 0.08;
    for (const [x0, y0, x1, y1] of [[0, 0, m, 0], [w, 0, w - m, 0], [0, 0, 0, m], [0, h, 0, h - m]]) {
      const g = x.createLinearGradient(x0, y0, x1, y1);
      g.addColorStop(0, `rgba(120,92,55,${e})`); g.addColorStop(1, 'rgba(120,92,55,0)');
      x.fillStyle = g; x.fillRect(0, 0, w, h);
    }
  }
  return c;
}

// Tinta de máquina de escribir: capa de texto erosionada + sangrado leve
function inkComposite(ctx, layer, seed, alpha = 0.94, bleed = 1.4) {
  const lx = layer.getContext('2d'), R = rng(seed);
  lx.globalCompositeOperation = 'destination-out';
  const n = Math.floor(layer.width * layer.height / 700);
  for (let i = 0; i < n; i++) { lx.fillStyle = `rgba(0,0,0,${R() * 0.6})`; const s = 0.6 + R() * 2.4; lx.fillRect(R() * layer.width, R() * layer.height, s, s); }
  lx.globalCompositeOperation = 'source-over';
  ctx.save();
  ctx.globalAlpha = 0.32; ctx.filter = `blur(${bleed}px)`; ctx.drawImage(layer, 0, 0);
  ctx.filter = 'none'; ctx.globalAlpha = alpha; ctx.drawImage(layer, 0, 0);
  ctx.restore();
}
function typeChars(lx, chars, seed, color = COL.ink) {
  // chars: [{ch,x,y,size,font}]
  const R = rng(seed);
  for (let i = 0; i < chars.length; i++) {
    const c = chars[i];
    const dx = (R() - 0.5) * 2.2, dy = (R() - 0.5) * 2.4, rot = (R() - 0.5) * 0.025, a = 0.8 + R() * 0.2, dbl = R();
    lx.save();
    lx.translate(c.x + dx, c.y + dy); lx.rotate(rot);
    lx.font = c.font; lx.fillStyle = color; lx.globalAlpha = a; lx.textBaseline = 'alphabetic';
    lx.fillText(c.ch, 0, 0);
    if (dbl < 0.18) { lx.globalAlpha = 0.25; lx.fillText(c.ch, 0.9, 0.4); }
    lx.restore();
  }
}
function layoutMono(text, x0, y0, cols, size, lineH, font) {
  const words = text.split(' ');
  const lines = []; let cur = '';
  for (const w of words) { if ((cur + (cur ? ' ' : '') + w).length > cols && cur) { lines.push(cur); cur = w; } else cur += (cur ? ' ' : '') + w; }
  if (cur) lines.push(cur);
  const adv = size * 0.6, out = [];
  lines.forEach((ln, li) => { for (let k = 0; k < ln.length; k++) if (ln[k] !== ' ') out.push({ ch: ln[k], x: x0 + k * adv, y: y0 + li * lineH, font }); });
  // índice de tecleo también para espacios (ritmo constante)
  return { chars: out, lines };
}

// -------------------------------------------------------------- materiales/escena
let TL = null; // timeline
const OBJ = {};

function canvasTex(c, srgb = true) {
  const t = new THREE.CanvasTexture(c);
  if (srgb) t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8; t.generateMipmaps = true; t.minFilter = THREE.LinearMipmapLinearFilter;
  return t;
}

function woodCanvas() {
  const w = 2048, h = 2048, c = mk(w, h), x = c.getContext('2d'), R = rng(77);
  x.fillStyle = '#150d08'; x.fillRect(0, 0, w, h);
  for (let i = 0; i < 900; i++) {
    const y = R() * h, amp = 4 + R() * 30, fr = 0.002 + R() * 0.004, ph = R() * 6.28, lw = 0.6 + R() * 3.5;
    const l = R();
    x.strokeStyle = l < 0.5 ? `rgba(6,4,2,${0.15 + R() * 0.35})` : `rgba(52,34,20,${0.08 + R() * 0.2})`;
    x.lineWidth = lw; x.beginPath();
    for (let px = -20; px <= w + 20; px += 16) { const yy = y + Math.sin(px * fr + ph) * amp + Math.sin(px * fr * 3.1 + ph * 2) * amp * 0.25; px === -20 ? x.moveTo(px, yy) : x.lineTo(px, yy); }
    x.stroke();
  }
  // poros
  for (let i = 0; i < 30000; i++) { x.fillStyle = `rgba(0,0,0,${0.1 + R() * 0.3})`; x.fillRect(R() * w, R() * h, 1 + R() * 5, 0.8); }
  // juntas de tablones
  for (let k = 1; k < 4; k++) { x.fillStyle = 'rgba(0,0,0,0.65)'; x.fillRect(0, k * h / 4 - 1.5, w, 3); }
  return c;
}

function softRect(w, h, pad) {
  const c = mk(256, 256), x = c.getContext('2d');
  x.filter = `blur(${pad}px)`;
  x.fillStyle = '#fff'; x.fillRect(pad * 1.6, pad * 1.6, 256 - pad * 3.2, 256 - pad * 3.2);
  return c;
}

function buildEnvironment() {
  const env = new THREE.Scene();
  const box = new THREE.Mesh(new THREE.SphereGeometry(10, 32, 16), new THREE.MeshBasicMaterial({ color: 0x06080c, side: THREE.BackSide }));
  env.add(box);
  const lamp = new THREE.Mesh(new THREE.CircleGeometry(0.35, 32), new THREE.MeshBasicMaterial({ color: new THREE.Color(1.0, 0.62, 0.32).multiplyScalar(5) }));
  lamp.position.set(0, 6, 0); lamp.lookAt(0, 0, 0); env.add(lamp);
  for (const [px, pz, ry] of [[-6, -5, 0.6], [5, -6, -0.5]]) {
    const win = new THREE.Mesh(new THREE.PlaneGeometry(2.4, 3.2), new THREE.MeshBasicMaterial({ color: new THREE.Color(0.25, 0.38, 0.6).multiplyScalar(1.4) }));
    win.position.set(px, 2.2, pz); win.lookAt(0, 1, 0); env.add(win);
  }
  const strip = new THREE.Mesh(new THREE.PlaneGeometry(14, 0.4), new THREE.MeshBasicMaterial({ color: new THREE.Color(0.9, 0.6, 0.35).multiplyScalar(0.6) }));
  strip.position.set(0, -1, 7); strip.lookAt(0, 0, 0); env.add(strip);
  const pm = new THREE.PMREMGenerator(renderer);
  const rt = pm.fromScene(env, 0.02);
  return rt.texture;
}

// dimensiones (metros)
const URN = { w: 0.28, h: 0.32, d: 0.28, t: 0.006 };
const ENV = { w: 0.12, l: 0.17, t: 0.0032, r: 0.315 };
const BAL = { w: 0.10, l: 0.14, out: 0.161 };
const SEAL_AT = V(3, 0, 0);
const phiOf = (k) => k * 72 * DEG; // k = 0..4
const SPOT_I = 15, SSPOT_I = 2.2;

function buildScene(fontsReady) {
  scene.environment = buildEnvironment();

  // --- luces
  const amber = new THREE.Color(COL.amber);
  const spot = new THREE.SpotLight(amber, 70, 0, 0.24, 0.32, 2);
  spot.position.set(0, 2.6, 0); spot.target.position.set(0, 0, 0);
  spot.castShadow = true; spot.shadow.mapSize.set(2048, 2048); spot.shadow.bias = -0.00015; spot.shadow.normalBias = 0.004; spot.shadow.radius = 4;
  spot.shadow.camera.near = 1.2; spot.shadow.camera.far = 3.4;
  scene.add(spot, spot.target); OBJ.spot = spot;
  const sspot = new THREE.SpotLight(amber, 0, 0, 0.085, 0.8, 2);
  sspot.position.copy(SEAL_AT).add(V(0.25, 1.1, 0.35)); sspot.target.position.copy(SEAL_AT);
  sspot.castShadow = true; sspot.shadow.mapSize.set(1024, 1024); sspot.shadow.bias = -0.0002; sspot.shadow.radius = 3;
  sspot.shadow.camera.near = 0.5; sspot.shadow.camera.far = 2.2;
  scene.add(sspot, sspot.target); OBJ.sspot = sspot;
  const hemi = new THREE.HemisphereLight(0x2a3a55, 0x050608, 0.22); scene.add(hemi); OBJ.hemi = hemi;
  const rim = new THREE.DirectionalLight(0x6f92c8, 0.30); rim.position.set(-1.4, 1.2, -2.2); scene.add(rim); OBJ.rim = rim;
  const rim2 = new THREE.DirectionalLight(0x5f7fb0, 0.12); rim2.position.set(1.8, 0.9, 1.0); scene.add(rim2); OBJ.rim2 = rim2;

  // --- mesa
  const woodTex = canvasTex(woodCanvas()); woodTex.wrapS = woodTex.wrapT = THREE.RepeatWrapping; woodTex.repeat.set(1.2, 1.2);
  const woodMat = new THREE.MeshStandardMaterial({ map: woodTex, roughness: 0.34, bumpMap: woodTex, bumpScale: 1.2, envMapIntensity: 0.55 });
  const table = new THREE.Mesh(new THREE.BoxGeometry(2.4, 0.05, 2.2), woodMat);
  table.position.set(0, -0.025, 0); table.receiveShadow = true; scene.add(table);
  const legMat = new THREE.MeshStandardMaterial({ color: 0x120c08, roughness: 0.6 });
  for (const [lx, lz] of [[-1.1, -1.0], [1.1, -1.0], [-1.1, 1.0], [1.1, 1.0]]) { const leg = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.74, 0.06), legMat); leg.position.set(lx, -0.42, lz); scene.add(leg); }
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(14, 14), new THREE.MeshStandardMaterial({ color: 0x07090c, roughness: 0.95 }));
  floor.rotation.x = -Math.PI / 2; floor.position.y = -0.79; floor.receiveShadow = true; scene.add(floor);
  // pared del fondo con luz de persiana (azul noche)
  const blinds = mk(512, 512), bx = blinds.getContext('2d');
  bx.fillStyle = '#000'; bx.fillRect(0, 0, 512, 512);
  bx.filter = 'blur(6px)';
  for (let i = 0; i < 9; i++) { bx.fillStyle = `rgba(110,150,210,${0.75 - i * 0.05})`; bx.fillRect(120, 70 + i * 40, 280, 18); }
  const blTex = canvasTex(blinds);
  const wall = new THREE.Mesh(new THREE.PlaneGeometry(7, 4), new THREE.MeshStandardMaterial({ color: 0x0e1218, roughness: 0.95, emissive: 0xffffff, emissiveMap: blTex, emissiveIntensity: 0.10 }));
  wall.position.set(0.9, 0.9, -2.6); wall.rotation.z = 0.0; scene.add(wall);
  // seal set: papel crema
  const sealPaperTex = canvasTex(paperCanvas(1024, 1024, 513, { edge: 0 }));
  const sealPaper = new THREE.Mesh(new THREE.PlaneGeometry(0.7, 0.7), new THREE.MeshStandardMaterial({ map: sealPaperTex, bumpMap: sealPaperTex, bumpScale: 1.5, roughness: 0.88, envMapIntensity: 0.2 }));
  sealPaper.rotation.x = -Math.PI / 2; sealPaper.position.copy(SEAL_AT).add(V(0, 0.0, 0)); sealPaper.receiveShadow = true; scene.add(sealPaper);

  // --- urna de metacrilato
  const acrylic = new THREE.MeshPhysicalMaterial({ color: 0xe4f2ee, metalness: 0, roughness: 0.10, transparent: true, opacity: 0.13, depthWrite: false,
    clearcoat: 0.6, clearcoatRoughness: 0.12, specularIntensity: 1, envMapIntensity: 2.2, side: THREE.DoubleSide });
  const edgeMat = new THREE.MeshPhysicalMaterial({ color: 0xd6ece6, roughness: 0.1, transparent: true, opacity: 0.55, depthWrite: false, envMapIntensity: 2.5, emissive: 0x30342e, emissiveIntensity: 0.4 });
  const urn = new THREE.Group(); OBJ.urn = urn;
  const t = URN.t, uw = URN.w, uh = URN.h, ud = URN.d;
  const panel = (sx, sy, sz, px, py, pz) => { const m = new THREE.Mesh(new THREE.BoxGeometry(sx, sy, sz), acrylic); m.position.set(px, py, pz); urn.add(m); return m; };
  panel(uw, uh, t, 0, uh / 2, ud / 2 - t / 2);
  panel(uw, uh, t, 0, uh / 2, -ud / 2 + t / 2);
  panel(t, uh, ud - 2 * t, uw / 2 - t / 2, uh / 2, 0);
  panel(t, uh, ud - 2 * t, -uw / 2 + t / 2, uh / 2, 0);
  panel(uw, t, ud, 0, t / 2, 0);
  // tapa con ranura (ranura a lo largo de x, en z=0)
  const lw = uw + 0.012, ld = ud + 0.012, slotL = 0.18, slotW = 0.014, lt = 0.008, ly = uh + lt / 2;
  const half = (ld - slotW) / 2;
  panel(lw, lt, half, 0, ly, slotW / 2 + half / 2);
  panel(lw, lt, half, 0, ly, -slotW / 2 - half / 2);
  panel((lw - slotL) / 2, lt, slotW, slotL / 2 + (lw - slotL) / 4, ly, 0);
  panel((lw - slotL) / 2, lt, slotW, -slotL / 2 - (lw - slotL) / 4, ly, 0);
  // aristas pulidas (brillo de canto)
  const edgeGeo = new THREE.BoxGeometry(0.0035, uh, 0.0035);
  for (const [ex, ez] of [[1, 1], [1, -1], [-1, 1], [-1, -1]]) { const e = new THREE.Mesh(edgeGeo, edgeMat); e.position.set(ex * (uw / 2 - 0.0018), uh / 2, ez * (ud / 2 - 0.0018)); urn.add(e); }
  scene.add(urn);
  // sombra suave bajo la urna (la luz atraviesa el metacrilato: sombra tenue)
  const shTex = canvasTex(softRect(256, 256, 22), false);
  const urnShadow = new THREE.Mesh(new THREE.PlaneGeometry(uw + 0.07, ud + 0.07), new THREE.MeshBasicMaterial({ color: 0x000000, alphaMap: shTex, transparent: true, opacity: 0.45, depthWrite: false }));
  urnShadow.rotation.x = -Math.PI / 2; urnShadow.position.y = 0.0006; scene.add(urnShadow);

  // --- sobres
  const front = [], back = [];
  const paperBase = paperCanvas(1024, 1450, PAPER_SEED);
  OBJ.envelopes = [];
  const edgeTex = new THREE.MeshStandardMaterial({ color: 0xd9cdb4, roughness: 0.9 });
  const bulge = (geo, sign) => {
    const p = geo.attributes.position;
    for (let i = 0; i < p.count; i++) { const x = p.getX(i) / (ENV.w / 2), y = p.getY(i) / (ENV.l / 2); p.setZ(i, sign * 0.0009 * (1 - x * x) * (1 - y * y)); }
    geo.computeVertexNormals();
  };
  for (let k = 0; k < 5; k++) {
    // anverso: número
    const fc = mk(1024, 1450), fx = fc.getContext('2d'); fx.drawImage(paperBase, 0, 0);
    // pestaña de cierre visible al trasluz: línea muy tenue en la parte inferior
    fx.strokeStyle = 'rgba(110,88,58,0.18)'; fx.lineWidth = 3; fx.beginPath(); fx.moveTo(40, 1300); fx.lineTo(984, 1300); fx.stroke();
    const lf = mk(1024, 1450), lfx = lf.getContext('2d');
    lfx.textAlign = 'left';
    const digit = String(k + 1), size = 560;
    typeChars(lfx, [{ ch: digit, x: 512 - size * 0.3, y: 900, font: `700 ${size}px CourierPrime` }], 900 + 0); // misma semilla para todos
    lfx.font = '400 64px CourierPrime'; lfx.fillStyle = COL.ink; lfx.globalAlpha = 0.85;
    typeChars(lfx, [...'Nº'].map((ch, i) => ({ ch, x: 512 - 38 + i * 38.4, y: 330, font: '400 64px CourierPrime' })), 901);
    inkComposite(fx, lf, 4242);
    const ft = canvasTex(fc); front.push(ft);
    // reverso: solapa + partido (se dibuja tras conocer TL)
    const bc = mk(1024, 1450); back.push(bc);
    const env = new THREE.Group();
    const body = new THREE.Mesh(new THREE.BoxGeometry(ENV.w - 0.0006, ENV.t * 0.9, ENV.l - 0.0006), edgeTex);
    body.castShadow = true; env.add(body);
    const fg = new THREE.PlaneGeometry(ENV.w, ENV.l, 10, 14); bulge(fg, 1); fg.rotateX(-Math.PI / 2); fg.translate(0, ENV.t / 2, 0);
    const fm = new THREE.MeshStandardMaterial({ map: ft, bumpMap: ft, bumpScale: 1.6, roughness: 0.86, envMapIntensity: 0.25 });
    const fmesh = new THREE.Mesh(fg, fm); fmesh.castShadow = true; fmesh.receiveShadow = true; env.add(fmesh);
    const bg = new THREE.PlaneGeometry(ENV.w, ENV.l, 10, 14); bulge(bg, 1); bg.rotateX(Math.PI / 2); bg.translate(0, -ENV.t / 2, 0);
    const bt = canvasTex(bc);
    const bm = new THREE.MeshStandardMaterial({ map: bt, bumpMap: bt, bumpScale: 1.6, roughness: 0.86, envMapIntensity: 0.25 });
    const bmesh = new THREE.Mesh(bg, bm); bmesh.castShadow = true; bmesh.receiveShadow = true; env.add(bmesh);
    // papeleta
    const balC = mk(1024, 1434);
    const balT = canvasTex(balC);
    const balG = new THREE.PlaneGeometry(BAL.w, BAL.l, 6, 10); balG.rotateX(-Math.PI / 2);
    const balM = new THREE.MeshStandardMaterial({ map: balT, bumpMap: balT, bumpScale: 1.2, roughness: 0.82, side: THREE.DoubleSide, envMapIntensity: 0.25 });
    const bal = new THREE.Mesh(balG, balM); bal.position.y = 0.0002; bal.castShadow = true; bal.receiveShadow = true; env.add(bal);
    scene.add(env);
    // sombra de contacto
    const cs = new THREE.Mesh(new THREE.PlaneGeometry(ENV.w + 0.016, ENV.l + 0.016), new THREE.MeshBasicMaterial({ color: 0x000000, alphaMap: shTex, transparent: true, opacity: 0.5, depthWrite: false }));
    cs.rotation.x = -Math.PI / 2; cs.position.y = 0.0004; scene.add(cs);
    const bcs = new THREE.Mesh(new THREE.PlaneGeometry(BAL.w + 0.012, BAL.l + 0.012), new THREE.MeshBasicMaterial({ color: 0x000000, alphaMap: shTex, transparent: true, opacity: 0.14, depthWrite: false }));
    bcs.rotation.x = -Math.PI / 2; bcs.position.y = 0.0003; scene.add(bcs);
    OBJ.envelopes.push({ g: env, bal, balC, balT, bc, bt, cs, bcs });
  }
  OBJ.paperBase = paperBase;
  OBJ.ballotBases = [0, 1, 2, 3, 4].map((k) => {
    // misma hoja, mismo diseño y misma semilla para las cinco; solo cambia el número
    const c = paperCanvas(1024, 1434, PAPER_SEED + 1, { base: '#F1E9D7', edge: 0.12 }), x = c.getContext('2d');
    x.strokeStyle = 'rgba(20,20,20,0.5)'; x.lineWidth = 3; x.strokeRect(62, 62, 900, 1310);
    x.lineWidth = 1.5; x.strokeRect(78, 78, 868, 1278);
    x.fillStyle = 'rgba(20,20,20,0.72)'; x.font = '500 36px PlexMono'; x.textAlign = 'left';
    x.letterSpacing = '9px';
    x.fillText('PROPUESTA', 356, 262);
    x.fillText('DE VIVIENDA', 356, 318);
    x.letterSpacing = '0px';
    x.fillRect(120, 420, 784, 3);
    const lay = mk(1024, 1434), lx = lay.getContext('2d');
    typeChars(lx, [{ ch: String(k + 1), x: 118, y: 392, font: '700 330px CourierPrime' }], 6100);
    inkComposite(x, lay, 4245, 0.96, 1.6);
    return c;
  });

  // --- sello de lacre
  const sealGroup = new THREE.Group(); OBJ.seal = sealGroup;
  const sealCanvas = mk(1024, 1024), sx = sealCanvas.getContext('2d');
  // mapa de relieve: gris medio = base; claro = alto
  sx.fillStyle = '#6a6a6a'; sx.fillRect(0, 0, 1024, 1024);
  sx.filter = 'blur(3px)';
  sx.strokeStyle = '#d8d8d8'; sx.lineWidth = 46; sx.beginPath(); sx.arc(512, 512, 392, 0, Math.PI * 2); sx.stroke();
  sx.fillStyle = '#3a3a3a'; sx.beginPath(); sx.arc(512, 512, 360, 0, Math.PI * 2); sx.fill();
  sx.strokeStyle = '#9a9a9a'; sx.lineWidth = 8; sx.beginPath(); sx.arc(512, 512, 318, 0, Math.PI * 2); sx.stroke();
  for (let i = 0; i < 48; i++) { const a = i / 48 * Math.PI * 2; sx.fillStyle = '#a0a0a0'; sx.beginPath(); sx.arc(512 + Math.cos(a) * 290, 512 + Math.sin(a) * 290, 6, 0, 7); sx.fill(); }
  sx.fillStyle = '#e8e8e8'; sx.textAlign = 'center'; sx.textBaseline = 'middle'; sx.font = '600 250px Fraunces';
  sx.letterSpacing = '6px';
  sx.fillText('29-N', 512, 530);
  sx.filter = 'none';
  const sealBump = canvasTex(sealCanvas, false);
  // color: el relieve alto algo más claro (cera estirada)
  const scol = mk(512, 512), scx = scol.getContext('2d'); scx.drawImage(sealCanvas, 0, 0, 512, 512);
  const id = scx.getImageData(0, 0, 512, 512); const R0 = rng(5);
  for (let i = 0; i < id.data.length; i += 4) {
    const v = id.data[i] / 255; const n = R0() * 0.06;
    id.data[i] = 179 * (0.62 + 0.55 * v + n); id.data[i + 1] = 38 * (0.6 + 0.5 * v + n); id.data[i + 2] = 30 * (0.6 + 0.5 * v + n); id.data[i + 3] = 255;
  }
  scx.putImageData(id, 0, 0);
  const sealColTex = canvasTex(scol);
  const waxSide = new THREE.MeshPhysicalMaterial({ color: COL.wax, roughness: 0.42, clearcoat: 0.45, clearcoatRoughness: 0.3, sheen: 0.3, sheenColor: new THREE.Color(0.9, 0.4, 0.35), envMapIntensity: 0.7 });
  const waxTop = new THREE.MeshPhysicalMaterial({ map: sealColTex, bumpMap: sealBump, bumpScale: 5, roughness: 0.38, clearcoat: 0.5, clearcoatRoughness: 0.25, envMapIntensity: 0.7 });
  const blob = (r, h, rough, seg = 128) => {
    const g = new THREE.CylinderGeometry(r * 0.96, r, h, seg, 2);
    const p = g.attributes.position, uv = g.attributes.uv;
    for (let i = 0; i < p.count; i++) {
      const x = p.getX(i), y = p.getY(i), z = p.getZ(i);
      const a = Math.atan2(x, z), rr = Math.hypot(x, z);
      const k = 1 + rough * (Math.sin(a * 3 + 1.3) * 0.5 + Math.sin(a * 7 + 0.4) * 0.3 + Math.sin(a * 13 + 2.2) * 0.2);
      const nx = x * k, nz = z * k;
      p.setXYZ(i, nx, y, nz);
      uv.setXY(i, nx / (2 * r) + 0.5, -nz / (2 * r) + 0.5);
    }
    g.computeVertexNormals();
    return g;
  };
  const disc = new THREE.Mesh(blob(0.027, 0.0055, 0.025), [waxSide, waxTop, waxSide]); disc.position.y = 0.0055 / 2 + 0.002; disc.castShadow = true;
  const puddle = new THREE.Mesh(blob(0.034, 0.0022, 0.08), [waxSide, waxSide, waxSide]); puddle.position.y = 0.0011; puddle.castShadow = true; puddle.scale.set(1, 1, 1);
  sealGroup.add(disc, puddle); OBJ.puddle = puddle; OBJ.disc = disc;
  scene.add(sealGroup);

  // --- polvo en el haz
  OBJ.dust = buildDust();
  OBJ.burst = buildBurst();
}

// ------------------------------------------------------------------ polvo
const DUST_VS = /* glsl */`
attribute vec4 seed;
uniform float time, cocK, focus, cocMax, pxPerRad, tImpact, burst;
uniform vec3 sPos, sDir, s2Pos, s2Dir, sCol; uniform float sCos, sInt, s2Cos, s2Int;
uniform vec3 origin;
varying float vA; varying vec3 vC; varying float vZ; varying float vSize;
float spotLit(vec3 p, vec3 P, vec3 D, float c){ vec3 L = p - P; float d = length(L); float ca = dot(L/d, D); return smoothstep(c, mix(c, 1.0, 0.45), ca) / (d*d); }
void main(){
  vec3 p = position;
  if (burst > 0.5) {
    float tt = max(time - tImpact, 0.0);
    vec3 v = seed.xyz;
    float k = 3.2;
    p = origin + v * (1.0 - exp(-k*tt)) / k + vec3(0.0, -0.012*tt*tt, 0.0) + vec3(sin(tt*2.0+seed.w*30.0), 0.0, cos(tt*1.7+seed.w*20.0))*0.004*tt;
    p.y = max(p.y, 0.0005);
  } else {
    float ph = seed.w * 6.2831;
    p += vec3(sin(time*0.13 + ph)*0.05 + sin(time*0.41 + ph*3.0)*0.012,
              sin(time*0.09 + ph*2.0)*0.04 - fract(time*0.004*seed.y + seed.z)*0.0,
              cos(time*0.11 + ph)*0.05 + cos(time*0.37 + ph*5.0)*0.012);
  }
  vec4 mv = modelViewMatrix * vec4(p, 1.0);
  float z = -mv.z;
  float coc = clamp(cocK * abs(1.0/z - 1.0/focus), 0.0, cocMax);
  float intrinsic = (burst > 0.5 ? 0.0006 : 0.0009) * (0.5 + seed.x*seed.x*1.6 + 0.0) / z * pxPerRad;
  float size = max(max(1.5, intrinsic), coc * 2.0);
  vSize = size;
  gl_PointSize = size;
  float lit = sInt * spotLit(p, sPos, sDir, sCos) + s2Int * spotLit(p, s2Pos, s2Dir, s2Cos);
  float energy = pow(max(1.5, intrinsic) / size, 2.0);
  float tw = 0.55 + 0.45 * sin(time * (1.0 + seed.y*2.0) + seed.w * 40.0);
  vA = lit * energy * tw * (burst > 0.5 ? smoothstep(0.0, 0.05, time - tImpact) * exp(-max(time - tImpact,0.0)*0.9) * 1.0 : 1.0);
  vC = sCol;
  vZ = z;
  gl_Position = projectionMatrix * mv;
}`;
const DUST_FS = /* glsl */`
#include <packing>
uniform sampler2D tDepth; uniform vec2 res; uniform float cNear, cFar, gain;
varying float vA; varying vec3 vC; varying float vZ; varying float vSize;
void main(){
  vec2 q = gl_PointCoord * 2.0 - 1.0; float r = length(q);
  if (r > 1.0) discard;
  float edge = vSize > 6.0 ? smoothstep(1.0, 0.86, r) * (0.82 + 0.3 * smoothstep(0.55, 0.95, r)) : exp(-r*r*3.0);
  float sd = texture2D(tDepth, gl_FragCoord.xy / res).x;
  float sz = -perspectiveDepthToViewZ(sd, cNear, cFar);
  float soft = smoothstep(0.0, 0.006, sz - vZ);
  gl_FragColor = vec4(vC * vA * edge * soft * gain, 1.0);
}`;
function dustMaterial(burst) {
  return new THREE.ShaderMaterial({
    vertexShader: DUST_VS, fragmentShader: DUST_FS, transparent: true, depthTest: false, depthWrite: false, blending: THREE.AdditiveBlending,
    uniforms: {
      time: { value: 0 }, cocK: { value: 10 }, focus: { value: 1 }, cocMax: { value: 30 }, pxPerRad: { value: 1000 }, tImpact: { value: 0 }, burst: { value: burst ? 1 : 0 },
      sPos: { value: V(0, 2.6, 0) }, sDir: { value: V(0, -1, 0) }, sCos: { value: Math.cos(0.24) }, sInt: { value: 1 },
      s2Pos: { value: V() }, s2Dir: { value: V(0, -1, 0) }, s2Cos: { value: Math.cos(0.085) }, s2Int: { value: 0 },
      sCol: { value: new THREE.Color(COL.amber) }, origin: { value: SEAL_AT.clone() },
      tDepth: { value: null }, res: { value: new THREE.Vector2(W, H) }, cNear: { value: 0.02 }, cFar: { value: 14 }, gain: { value: 1 },
    },
  });
}
function buildDust() {
  const N = 2600, R = rng(31);
  const pos = new Float32Array(N * 3), sd = new Float32Array(N * 4);
  for (let i = 0; i < N; i++) {
    const a = R() * Math.PI * 2, r = Math.sqrt(R()) * 0.95, y = 0.02 + Math.pow(R(), 0.8) * 2.3;
    pos.set([Math.sin(a) * r, y, Math.cos(a) * r], i * 3); sd.set([R(), R(), R(), R()], i * 4);
  }
  // polvo cercano al set del sello
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setAttribute('seed', new THREE.BufferAttribute(sd, 4));
  const pts = new THREE.Points(g, dustMaterial(false)); pts.frustumCulled = false;
  const ds = new THREE.Scene(); ds.add(pts);
  // motas alrededor del sello (ambiente)
  const N2 = 500, p2 = new Float32Array(N2 * 3), s2 = new Float32Array(N2 * 4);
  for (let i = 0; i < N2; i++) { p2.set([SEAL_AT.x + (R() - 0.5) * 0.5, 0.005 + R() * 0.35, SEAL_AT.z + (R() - 0.5) * 0.5], i * 3); s2.set([R() * 0.6, R(), R(), R()], i * 4); }
  const g2 = new THREE.BufferGeometry(); g2.setAttribute('position', new THREE.BufferAttribute(p2, 3)); g2.setAttribute('seed', new THREE.BufferAttribute(s2, 4));
  const pts2 = new THREE.Points(g2, dustMaterial(false)); pts2.frustumCulled = false; ds.add(pts2);
  return { scene: ds, mats: [pts.material, pts2.material] };
}
function buildBurst() {
  const N = 700, R = rng(44);
  const pos = new Float32Array(N * 3), sd = new Float32Array(N * 4);
  for (let i = 0; i < N; i++) {
    const a = R() * Math.PI * 2, sp = 0.03 + Math.pow(R(), 2) * 0.22, up = 0.02 + R() * 0.12;
    const r0 = 0.03 + R() * 0.01;
    pos.set([0, 0, 0], i * 3);
    sd.set([Math.sin(a) * sp + Math.sin(a) * r0, up, Math.cos(a) * sp + Math.cos(a) * r0, R()], i * 4);
  }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setAttribute('seed', new THREE.BufferAttribute(sd, 4));
  const pts = new THREE.Points(g, dustMaterial(true)); pts.frustumCulled = false;
  OBJ.dust.scene.add(pts); OBJ.dust.mats.push(pts.material);
  return pts;
}

// ------------------------------------------------------------- postproceso
const FS_VS = `varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`;
const fsGeo = new THREE.BufferGeometry();
fsGeo.setAttribute('position', new THREE.Float32BufferAttribute([-1, -1, 0, 3, -1, 0, -1, 3, 0], 3));
fsGeo.setAttribute('uv', new THREE.Float32BufferAttribute([0, 0, 2, 0, 0, 2], 2));
const fsCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
function makePass(fs, uniforms) {
  const m = new THREE.ShaderMaterial({ vertexShader: FS_VS, fragmentShader: fs, uniforms, depthTest: false, depthWrite: false });
  const mesh = new THREE.Mesh(fsGeo, m); mesh.frustumCulled = false;
  const sc = new THREE.Scene(); sc.add(mesh);
  return { m, u: m.uniforms, run(target) { renderer.setRenderTarget(target); renderer.render(sc, fsCam); } };
}
const rtOpt = { type: THREE.HalfFloatType, minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter, depthBuffer: false };
let RT = {};
let P = {};
const CORE = /* glsl */`
#include <packing>
uniform float cNear, cFar, cocK, focus, cocMax;
float viewZ(float d){ return -perspectiveDepthToViewZ(d, cNear, cFar); }
float cocOf(float z){ return clamp(cocK * (1.0/focus - 1.0/z), -cocMax, cocMax); } // + fondo, - primer plano
float hash12(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
`;
function buildPost() {
  const main = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, samples: 0, depthBuffer: true });
  main.depthTexture = new THREE.DepthTexture(W, H); main.depthTexture.type = THREE.UnsignedIntType;
  RT.main = main;
  RT.half = new THREE.WebGLRenderTarget(W / 2, H / 2, rtOpt);
  RT.blur = new THREE.WebGLRenderTarget(W / 2, H / 2, rtOpt);
  RT.beam = new THREE.WebGLRenderTarget(W / 2, H / 2, rtOpt);
  RT.comp = new THREE.WebGLRenderTarget(W, H, rtOpt);
  RT.b = [4, 8, 16, 32].map((d) => new THREE.WebGLRenderTarget(Math.round(W / d), Math.round(H / d), rtOpt));
  const camU = () => ({ cNear: { value: 0.02 }, cFar: { value: 14 }, cocK: { value: 10 }, focus: { value: 1 }, cocMax: { value: 30 } });

  P.down = makePass(CORE + /* glsl */`
    uniform sampler2D tColor, tDepth; uniform vec2 texel; varying vec2 vUv;
    void main(){
      vec3 c = texture2D(tColor, vUv).rgb;
      // profundidad: la más cercana de 4 (evita halos)
      float d0 = texture2D(tDepth, vUv + texel*vec2(-0.5,-0.5)).x, d1 = texture2D(tDepth, vUv + texel*vec2(0.5,-0.5)).x;
      float d2 = texture2D(tDepth, vUv + texel*vec2(-0.5,0.5)).x, d3 = texture2D(tDepth, vUv + texel*vec2(0.5,0.5)).x;
      float z = viewZ(min(min(d0,d1),min(d2,d3)));
      gl_FragColor = vec4(c, cocOf(z));
    }`, { ...camU(), tColor: { value: null }, tDepth: { value: null }, texel: { value: new THREE.Vector2(1 / W, 1 / H) } });

  P.blur = makePass(CORE + /* glsl */`
    uniform sampler2D tHalf; uniform vec2 texel; varying vec2 vUv;
    const float GA = 2.39996323;
    void main(){
      vec4 c0 = texture2D(tHalf, vUv);
      float cs = abs(c0.a) * 0.5;               // en píxeles de media resolución
      vec3 col = c0.rgb; float tot = 1.0;
      float rad = 1.2;
      float maxR = cocMax * 0.5;
      float rot = hash12(gl_FragCoord.xy) * 6.2831;
      for (int i = 0; i < 110; i++) {
        if (rad >= maxR) break;
        float ang = rot + float(i) * GA;
        vec2 uv = vUv + vec2(cos(ang), sin(ang)) * texel * rad;
        vec4 s = texture2D(tHalf, uv);
        float ss = abs(s.a) * 0.5;
        if (s.a > c0.a) ss = clamp(ss, 0.0, cs * 2.0); // fondo detrás de algo más nítido
        float m = smoothstep(rad - 0.75, rad + 0.75, ss);
        col += mix(col / tot, s.rgb, m);
        tot += 1.0;
        rad += 1.35 / rad;
      }
      gl_FragColor = vec4(col / tot, c0.a);
    }`, { ...camU(), tHalf: { value: null }, texel: { value: new THREE.Vector2(2 / W, 2 / H) } });

  P.beam = makePass(CORE + /* glsl */`
    uniform sampler2D tDepth; uniform mat4 invProj, camWorld; uniform vec3 camPos;
    uniform vec3 sPos, sCol; uniform float sInt, tanA, density, time, gHG;
    varying vec2 vUv;
    float h3(vec3 p){ p = fract(p*0.3183099 + .1); p *= 17.0; return fract(p.x*p.y*p.z*(p.x+p.y+p.z)); }
    float n3(vec3 x){ vec3 i=floor(x), f=fract(x); f=f*f*(3.-2.*f);
      return mix(mix(mix(h3(i),h3(i+vec3(1,0,0)),f.x), mix(h3(i+vec3(0,1,0)),h3(i+vec3(1,1,0)),f.x),f.y),
                 mix(mix(h3(i+vec3(0,0,1)),h3(i+vec3(1,0,1)),f.x), mix(h3(i+vec3(0,1,1)),h3(i+vec3(1,1,1)),f.x),f.y), f.z); }
    void main(){
      if (sInt <= 0.0) { gl_FragColor = vec4(0.0); return; }
      float d = texture2D(tDepth, vUv).x;
      vec4 v = invProj * vec4(vUv*2.0-1.0, -1.0, 1.0); vec3 dv = normalize(v.xyz / v.w);
      float zs = d >= 1.0 ? 50.0 : viewZ(d);
      float tMax = zs / max(-dv.z, 1e-4);
      vec3 rd = normalize((camWorld * vec4(dv, 0.0)).xyz), ro = camPos;
      // cilindro envolvente vertical
      float Rm = tanA * sPos.y * 1.05;
      vec2 o2 = ro.xz - sPos.xz, d2 = rd.xz;
      float a = dot(d2,d2), b = 2.0*dot(o2,d2), c = dot(o2,o2) - Rm*Rm;
      float disc = b*b - 4.0*a*c;
      if (disc <= 0.0 || a < 1e-6) { gl_FragColor = vec4(0.0); return; }
      float sq = sqrt(disc); float t0 = (-b - sq)/(2.0*a), t1 = (-b + sq)/(2.0*a);
      // franja en altura [0, sPos.y]
      float ty0 = (0.0 - ro.y)/rd.y, ty1 = (sPos.y - ro.y)/rd.y;
      if (ty0 > ty1) { float tt = ty0; ty0 = ty1; ty1 = tt; }
      t0 = max(max(t0, ty0), 0.0); t1 = min(min(t1, ty1), tMax);
      if (t1 <= t0) { gl_FragColor = vec4(0.0); return; }
      const int STEPS = 20;
      float dt = (t1 - t0) / float(STEPS);
      float j = hash12(gl_FragCoord.xy + fract(time*7.31)*91.0);
      float acc = 0.0;
      for (int i = 0; i < STEPS; i++) {
        vec3 p = ro + rd * (t0 + (float(i) + j) * dt);
        float h = sPos.y - p.y;
        float rc = h * tanA;
        float r = length(p.xz - sPos.xz);
        float mask = 1.0 - smoothstep(rc*0.42, rc*0.80, r);
        mask *= 0.35 + 0.65 * smoothstep(0.0, 0.5, h);
        float fall = 1.0 / (0.35 + h*h*0.55);
        float n = n3(p*vec3(5.0,2.2,5.0) + vec3(0.0, time*0.06, time*0.035));
        float n2 = n3(p*vec3(13.0,7.0,13.0) - vec3(time*0.05, 0.0, 0.0));
        acc += mask * fall * (0.25 + 1.4*n*n + 0.4*n2*n2) * dt;
      }
      float ct = rd.y;
      float g = gHG; float ph = (1.0 - g*g) / pow(1.0 + g*g - 2.0*g*ct, 1.5) * 0.25;
      gl_FragColor = vec4(sCol * sInt * density * acc * ph, 1.0);
    }`, { ...camU(), tDepth: { value: null }, invProj: { value: new THREE.Matrix4() }, camWorld: { value: new THREE.Matrix4() }, camPos: { value: V() },
    sPos: { value: V(0, 2.6, 0) }, sCol: { value: new THREE.Color(COL.amber) }, sInt: { value: 1 }, tanA: { value: Math.tan(0.24) }, density: { value: 1.1 }, time: { value: 0 }, gHG: { value: 0.35 } });

  P.comp = makePass(CORE + /* glsl */`
    uniform sampler2D tColor, tDepth, tBlur, tBeam; uniform vec2 texel; uniform float sweepPos, sweepAmt, flash, haze;
    uniform vec3 hazeCol, sweepCol; uniform float dbgBeam; varying vec2 vUv;
    void main(){
      vec3 sharp = texture2D(tColor, vUv).rgb;
      float z = viewZ(texture2D(tDepth, vUv).x);
      float coc = abs(cocOf(z));
      vec4 bl = texture2D(tBlur, vUv);
      float w = smoothstep(0.7, 2.6, max(coc, abs(bl.a) * 0.85));
      vec3 col = mix(sharp, bl.rgb, w);
      vec3 beam = texture2D(tBeam, vUv).rgb;
      // ligera bruma azulada en profundidad
      col += hazeCol * haze * (1.0 - exp(-z*0.22));
      col += beam;
      if (dbgBeam > 0.5) col = beam * 12.0;
      // barrido de luz del foco
      float xs = vUv.x + (vUv.y - 0.5) * 0.35;
      float band = exp(-pow((xs - sweepPos) / 0.20, 2.0)) * sweepAmt;
      col = col * (1.0 + band * 3.2 + flash * 1.4) + sweepCol * (band * 0.10 + flash * 0.05);
      gl_FragColor = vec4(col, 1.0);
    }`, { ...camU(), tColor: { value: null }, tDepth: { value: null }, tBlur: { value: null }, tBeam: { value: null }, texel: { value: new THREE.Vector2(1 / W, 1 / H) }, dbgBeam: { value: 0 },
    sweepPos: { value: -1 }, sweepAmt: { value: 0 }, flash: { value: 0 }, haze: { value: 0.02 }, hazeCol: { value: new THREE.Color(0.05, 0.08, 0.13) }, sweepCol: { value: new THREE.Color(1.0, 0.7, 0.42) } });

  P.bright = makePass(/* glsl */`
    uniform sampler2D tSrc; uniform vec2 texel; uniform float thr; varying vec2 vUv;
    void main(){
      vec3 c = vec3(0.0);
      c += texture2D(tSrc, vUv + texel*vec2(-1.,-1.)).rgb; c += texture2D(tSrc, vUv + texel*vec2(1.,-1.)).rgb;
      c += texture2D(tSrc, vUv + texel*vec2(-1.,1.)).rgb;  c += texture2D(tSrc, vUv + texel*vec2(1.,1.)).rgb;
      c *= 0.25;
      float l = max(c.r, max(c.g, c.b));
      gl_FragColor = vec4(c * smoothstep(thr, thr*2.5, l), 1.0);
    }`, { tSrc: { value: null }, texel: { value: new THREE.Vector2() }, thr: { value: 0.9 } });
  P.dn = makePass(/* glsl */`
    uniform sampler2D tSrc; uniform vec2 texel; varying vec2 vUv;
    void main(){
      vec3 c = texture2D(tSrc, vUv).rgb * 0.25;
      c += texture2D(tSrc, vUv + texel*vec2(-1.,-1.)).rgb * 0.1875; c += texture2D(tSrc, vUv + texel*vec2(1.,-1.)).rgb * 0.1875;
      c += texture2D(tSrc, vUv + texel*vec2(-1.,1.)).rgb * 0.1875;  c += texture2D(tSrc, vUv + texel*vec2(1.,1.)).rgb * 0.1875;
      gl_FragColor = vec4(c, 1.0);
    }`, { tSrc: { value: null }, texel: { value: new THREE.Vector2() } });

  P.final = makePass(/* glsl */`
    uniform sampler2D tComp, tB0, tB1, tB2, tB3, tUI; uniform vec2 texel;
    uniform float exposure, time, grain, vign, ca, fade, bloomAmt, halAmt, uiAmt, lift;
    varying vec2 vUv;
    float hash12(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
    vec3 aces(vec3 x){ const float a=2.51, b=0.03, c=2.43, d=0.59, e=0.14; return clamp((x*(a*x+b))/(x*(c*x+d)+e), 0.0, 1.0); }
    vec3 toSRGB(vec3 c){ return mix(c*12.92, 1.055*pow(c, vec3(1.0/2.4)) - 0.055, step(0.0031308, c)); }
    vec3 tent(sampler2D t, vec2 uv, vec2 px){
      vec3 c = texture2D(t, uv).rgb*4.0;
      c += (texture2D(t, uv+vec2(px.x,0.)).rgb + texture2D(t, uv-vec2(px.x,0.)).rgb + texture2D(t, uv+vec2(0.,px.y)).rgb + texture2D(t, uv-vec2(0.,px.y)).rgb)*2.0;
      c += texture2D(t, uv+px).rgb + texture2D(t, uv-px).rgb + texture2D(t, uv+vec2(px.x,-px.y)).rgb + texture2D(t, uv+vec2(-px.x,px.y)).rgb;
      return c/16.0;
    }
    void main(){
      vec2 uv = vUv; vec2 cc = uv - 0.5; cc.x *= 0.5625;
      float r2 = dot(cc, cc);
      vec2 off = (uv - 0.5) * ca * r2 * 2.4;
      vec3 col;
      col.r = texture2D(tComp, uv - off).r;
      col.g = texture2D(tComp, uv).g;
      col.b = texture2D(tComp, uv + off).b;
      vec3 b0 = texture2D(tB0, uv).rgb, b1 = tent(tB1, uv, texel*8.0), b2 = tent(tB2, uv, texel*16.0), b3 = tent(tB3, uv, texel*32.0);
      vec3 bloom = b0*0.30 + b1*0.30 + b2*0.25 + b3*0.25;
      col += bloom * bloomAmt;
      col += vec3(1.0, 0.25, 0.08) * (b0.r*0.6 + b1.r*0.4) * halAmt;   // halación de película
      col *= exposure;
      col = aces(col);
      // gradación: sombras azul noche, luces cálidas
      float l = dot(col, vec3(0.2126,0.7152,0.0722));
      col = mix(col, col * vec3(0.86, 0.96, 1.16), (1.0 - smoothstep(0.0, 0.45, l)) * 0.55);
      col = mix(col, col * vec3(1.06, 1.0, 0.9), smoothstep(0.4, 1.0, l) * 0.35);
      vec3 roomLin = vec3(0.0033, 0.0044, 0.0070);
      col = roomLin * lift + col * (1.0 - roomLin * lift);
      // viñeta
      float vg = smoothstep(0.95, 0.18, length((uv - 0.5) * vec2(1.0, 0.82)) * 1.25);
      col *= mix(1.0 - vign, 1.0, vg);
      col = toSRGB(clamp(col, 0.0, 1.0));
      // rótulos
      vec4 ui = texture2D(tUI, uv);
      col = mix(col, ui.rgb, ui.a * uiAmt);
      // grano 35 mm
      float g1 = hash12(gl_FragCoord.xy + fract(time * 13.7) * 1000.0) - 0.5;
      float g2 = hash12(floor(gl_FragCoord.xy * 0.5) + fract(time * 7.1) * 500.0) - 0.5;
      float lum = dot(col, vec3(0.299,0.587,0.114));
      float ga = grain * (0.55 + 0.9 * (1.0 - lum) * lum * 4.0 * 0.5 + 0.25);
      col += (g1 * 0.65 + g2 * 0.55) * ga;
      col *= fade;
      col += (hash12(gl_FragCoord.xy * 1.37 + 3.1) - 0.5) / 255.0;
      gl_FragColor = vec4(col, 1.0);
    }`, { tComp: { value: null }, tB0: { value: null }, tB1: { value: null }, tB2: { value: null }, tB3: { value: null }, tUI: { value: null }, texel: { value: new THREE.Vector2(1 / W, 1 / H) },
    exposure: { value: 1 }, time: { value: 0 }, grain: { value: 0.05 }, vign: { value: 0.45 }, ca: { value: 0.012 }, fade: { value: 1 }, bloomAmt: { value: 0.6 }, halAmt: { value: 0.12 }, uiAmt: { value: 1 }, lift: { value: 1 } });
}

// --------------------------------------------------------------- rótulos (2D)
const ui = mk(W, H), ux = ui.getContext('2d');
const uiTex = new THREE.CanvasTexture(ui); uiTex.colorSpace = THREE.NoColorSpace; uiTex.minFilter = THREE.LinearFilter; uiTex.generateMipmaps = false;
const SAFE = { top: 250, bottom: H - 380, right: W - 120, left: 120 };
const CREAM = '#F3ECDD';

function spaced(ctx, text, x, y, spacingPx, align = 'center') {
  ctx.letterSpacing = spacingPx + 'px';
  const w = ctx.measureText(text).width - spacingPx; // el último espaciado sobra
  let sx = align === 'center' ? x - w / 2 : (align === 'right' ? x - w : x);
  ctx.textAlign = 'left';
  ctx.fillText(text, sx, y);
  ctx.letterSpacing = '0px';
  return w;
}
function title(lines, t, t0, t1, opt = {}) {
  const fi = opt.fadeIn ?? 0.55, fo = opt.fadeOut ?? 0.45;
  if (t < t0 || t > t1) return;
  const a = smooth(range(t, t0, t0 + fi)) * (1 - smooth(range(t, t1 - fo, t1)));
  if (a <= 0) return;
  const size = opt.size || 84, cy = opt.y || 430, lh = size * 1.22;
  const track = lerp(0.16, 0.24, easeOut(range(t, t0, t0 + 2.4))) * size;
  const slam = opt.slam ? 1 + 0.32 * Math.pow(1 - easeOut(range(t, t0, t0 + 0.16)), 2) : 1;
  ux.save();
  ux.font = `600 ${size}px Fraunces`;
  ux.textBaseline = 'alphabetic';
  ux.shadowColor = 'rgba(0,0,0,0.65)'; ux.shadowBlur = 30; ux.shadowOffsetY = 4;
  const blur = opt.slam ? 0 : (1 - easeOut(range(t, t0, t0 + fi))) * 8;
  if (blur > 0.3) ux.filter = `blur(${blur.toFixed(2)}px)`;
  ux.globalAlpha = a;
  ux.fillStyle = opt.color || CREAM;
  const x0 = opt.x || (SAFE.left + SAFE.right) / 2;
  if (slam !== 1) { ux.translate(x0, cy); ux.scale(slam, slam); ux.translate(-x0, -cy); }
  if (opt.kicker) { ux.save(); ux.font = '500 30px PlexMono'; ux.globalAlpha = a * 0.85; spaced(ux, opt.kicker, x0, cy - size * 0.95, 12); ux.restore(); }
  lines.forEach((ln, i) => spaced(ux, ln, x0, cy + i * lh - (lines.length - 1) * lh / 2 + size * 0.35, track));
  ux.restore();
}
function subtitles(t) {
  if (!TL) return;
  const subs = TL.subtitles;
  let cur = null;
  for (const c of subs) if (t >= c.start - 0.06 && t < c.hold) cur = c;
  if (!cur) return;
  const size = 76, lh = size * 1.18, maxW = SAFE.right - SAFE.left;
  ux.save();
  ux.font = `600 ${size}px InterDisplay`; ux.textBaseline = 'alphabetic';
  // re-maquetar por anchura real
  const words = cur.words, sp = ux.measureText(' ').width;
  const lines = []; let line = [], lw = 0;
  words.forEach((w, i) => { const ww = ux.measureText(w.text).width; if (line.length && lw + sp + ww > maxW) { lines.push({ idx: line, w: lw }); line = []; lw = 0; } lw += (line.length ? sp : 0) + ww; line.push(i); });
  if (line.length) lines.push({ idx: line, w: lw });
  const baseY = SAFE.bottom - 92; // última línea
  const cx = (SAFE.left + SAFE.right) / 2;
  const fadeOut = 1 - smooth(range(t, cur.hold - 0.12, cur.hold));
  lines.forEach((ln, li) => {
    const y = baseY - (lines.length - 1 - li) * lh;
    let x = cx - ln.w / 2;
    ln.idx.forEach((i) => {
      const w = words[i]; const ww = ux.measureText(w.text).width;
      const next = words[i + 1];
      const shown = smooth(range(t, w.start - 0.04, w.start + 0.06));
      const active = t >= w.start - 0.02 && t < (next ? next.start - 0.02 : w.end + 0.25);
      if (shown > 0) {
        const pop = 1 + (1 - easeOut(range(t, w.start - 0.04, w.start + 0.12))) * 0.06;
        ux.save();
        ux.globalAlpha = shown * fadeOut;
        ux.translate(x + ww / 2, y - size * 0.35); ux.scale(pop, pop); ux.translate(-(x + ww / 2), -(y - size * 0.35));
        ux.shadowColor = 'rgba(0,0,0,0.6)'; ux.shadowBlur = 20; ux.shadowOffsetY = 3;
        ux.fillStyle = active ? COL.amber : CREAM;
        ux.textAlign = 'left'; ux.fillText(w.text, x, y);
        ux.restore();
      }
      x += ww + sp;
    });
  });
  ux.restore();
}
function sourceLine(t, a) {
  if (a <= 0) return;
  ux.save();
  ux.font = '400 22px PlexMono'; ux.fillStyle = CREAM; ux.globalAlpha = 0.55 * a; ux.textBaseline = 'alphabetic';
  ux.shadowColor = 'rgba(0,0,0,0.7)'; ux.shadowBlur = 8;
  spaced(ux, 'Propuestas recogidas por Brains RE News · posiciones a oct. 2026', (SAFE.left + SAFE.right) / 2, SAFE.bottom - 14, 0.5);
  ux.restore();
}
function cornerNumber(k, a) {
  if (a <= 0) return;
  ux.save();
  ux.globalAlpha = a;
  ux.shadowColor = 'rgba(0,0,0,0.7)'; ux.shadowBlur = 24; ux.shadowOffsetY = 4;
  ux.fillStyle = CREAM; ux.textBaseline = 'alphabetic';
  ux.font = '500 24px PlexMono';
  spaced(ux, 'PROPUESTA', 104, 300, 7, 'left');
  ux.font = '700 236px CourierPrime';
  ux.fillText(String(k + 1), 92, 500);
  ux.restore();
}

// ----------------------------------------------------------- dibujo de papel
const BALLOT_LAYOUT = [];
function prepareTexts() {
  const font = '400 84px CourierPrime';
  TL.proposals.forEach((p, k) => {
    const txt = p.charAt(0).toUpperCase() + p.slice(1);
    BALLOT_LAYOUT[k] = layoutMono(txt, 132, 560, 15, 84, 112, font);
  });
  // reversos con partido: misma tipografía, mismo tamaño, misma tinta
  TL.parties.forEach((name, k) => {
    const e = OBJ.envelopes[k];
    const c = e.bc, x = c.getContext('2d');
    x.drawImage(OBJ.paperBase, 0, 0);
    // solapa (V) y costuras
    x.save();
    x.strokeStyle = 'rgba(95,74,46,0.30)'; x.lineWidth = 3;
    x.beginPath(); x.moveTo(20, 20); x.lineTo(512, 520); x.lineTo(1004, 20); x.stroke();
    const g = x.createLinearGradient(0, 470, 0, 560); g.addColorStop(0, 'rgba(70,50,30,0.10)'); g.addColorStop(1, 'rgba(70,50,30,0)');
    x.fillStyle = g; x.beginPath(); x.moveTo(20, 20); x.lineTo(512, 520); x.lineTo(1004, 20); x.lineTo(1004, 60); x.lineTo(512, 580); x.lineTo(20, 60); x.fill();
    x.strokeStyle = 'rgba(95,74,46,0.16)'; x.lineWidth = 2;
    x.beginPath(); x.moveTo(20, 1430); x.lineTo(400, 900); x.moveTo(1004, 1430); x.lineTo(624, 900); x.stroke();
    x.restore();
    const lay = mk(1024, 1450), lx = lay.getContext('2d');
    const size = 150, adv = size * 0.6, up = name.toUpperCase();
    const x0 = 512 - (up.length * adv) / 2;
    typeChars(lx, [...up].map((ch, i) => ({ ch, x: x0 + i * adv, y: 930, font: `700 ${size}px CourierPrime` })), 1200);
    // número pequeño arriba, idéntico tratamiento
    typeChars(lx, [...('Nº ' + (k + 1))].map((ch, i) => ({ ch, x: 512 - 2 * 33.6 + i * 33.6, y: 700, font: '400 56px CourierPrime' })), 1201);
    inkComposite(x, lay, 4243);
    e.bt.needsUpdate = true;
  });
  for (let k = 0; k < 5; k++) drawBallot(k, 0);
}
const ballotState = [-1, -1, -1, -1, -1];
function drawBallot(k, n) {
  if (ballotState[k] === n) return;
  ballotState[k] = n;
  const e = OBJ.envelopes[k];
  const c = e.balC, x = c.getContext('2d');
  x.drawImage(OBJ.ballotBases[k], 0, 0);
  if (n > 0) {
    const lay = mk(1024, 1434), lx = lay.getContext('2d');
    typeChars(lx, BALLOT_LAYOUT[k].chars.slice(0, n), 7000); // misma semilla para todas
    inkComposite(x, lay, 4244, 0.95, 1.3);
  }
  e.balT.needsUpdate = true;
}

// ------------------------------------------------------------ animación
function radial(phi, r, y = 0) { return V(Math.sin(phi) * r, y, Math.cos(phi) * r); }
const qStand = new THREE.Quaternion().setFromEuler(new THREE.Euler(Math.PI / 2 - 0.35, 0, 0));
const INSIDE = [[0.0, 0.07, 0.0], [0.026, 0.037, 0.05], [-0.028, 0.004, -0.045], [0.018, -0.029, 0.06], [-0.02, -0.062, -0.05]];
function envState(k, t) {
  const T = TL.timeline;
  const s2 = T.s2[0];
  const f0 = s2 + 0.15 + k * 0.62, Df = 1.75;
  const phi = phiOf(k);
  const target = radial(phi, ENV.r, ENV.t / 2);
  const qFlat = new THREE.Quaternion().setFromEuler(new THREE.Euler(0, phi, 0));
  const [ix, iz, tilt] = INSIDE[k];
  const pIn = V(ix, URN.t + ENV.l / 2 * 0.93 + 0.002, iz);
  const qIn = new THREE.Quaternion().setFromEuler(new THREE.Euler(Math.PI / 2 - 0.40 + tilt * 0.6, tilt, 0));
  let pos = pIn.clone(), q = qIn.clone(), sound = 0;
  const u = range(t, f0, f0 + Df);
  if (u > 0) {
    if (u < 0.42) {
      const a = smoother(u / 0.42);
      pos = V(lerp(ix, 0, a), lerp(pIn.y, URN.h + ENV.l / 2 + 0.012, a), lerp(iz, 0, a));
      q = qIn.clone().slerp(qStand, a);
    } else {
      const b = clamp((u - 0.42) / 0.58), e = 1 - Math.pow(1 - b, 2.6);
      const p0 = V(0, URN.h + ENV.l / 2 + 0.012, 0), p2 = target, p1 = V(target.x * 0.62, URN.h + 0.08, target.z * 0.62);
      pos = p0.clone().multiplyScalar((1 - e) * (1 - e)).add(p1.clone().multiplyScalar(2 * (1 - e) * e)).add(p2.clone().multiplyScalar(e * e));
      const qs = new THREE.Quaternion().setFromEuler(new THREE.Euler(Math.PI / 2, phi * 0.5, 0, 'YXZ'));
      q = qStand.clone().slerp(qFlat, smoother(Math.min(1, b * 1.15)));
    }
  }
  // revelación: volteo sobre el eje tangencial
  let flip = 0, lift = 0;
  if (T.blocks_r) {
    const rb = T.blocks_r[k][0];
    const fu = range(t, rb + T.flip_land - T.flip_dur, rb + T.flip_land);
    if (fu > 0) {
      const ang = Math.PI * smoother(fu);
      lift = Math.sin(Math.PI * fu) * 0.095 + Math.sin(ang) * 0.0;
      flip = ang;
      // micro-rebote tras el golpe
      const tb = t - (rb + T.flip_land);
      if (tb > 0) lift += Math.max(0, Math.sin(tb * 30) * Math.exp(-tb * 16) * 0.0015);
    }
  }
  if (flip > 0) {
    const qf = new THREE.Quaternion().setFromAxisAngle(V(1, 0, 0), flip);
    q = qFlat.clone().multiply(qf);
    pos = target.clone(); pos.y += lift;
  }
  return { pos, q, flown: u >= 1, lift: Math.max(lift, u > 0 && u < 1 ? pos.y : (u >= 1 ? 0 : 1)) };
}
function ballotSlide(k, t) {
  const T = TL.timeline;
  const [b0, b1] = T.blocks_p[k];
  if (t < b0 || t >= b1) return { out: 0, n: 0 };
  const tau = t - b0;
  const out = easeOut(range(tau, 0.32, 1.05)) * BAL.out;
  const len = BALLOT_LAYOUT[k].chars.length;
  const n = Math.floor(range(tau, 1.0, 1.0 + 2.6) * len + 1e-6);
  return { out, n };
}

// ----------------------------------------------------------------- cámara
function lookQuat(pos, target, up = V(0, 1, 0)) {
  const m = new THREE.Matrix4().lookAt(pos, target, up);
  return new THREE.Quaternion().setFromRotationMatrix(m);
}
function shot(pos, target, fov, K, up, focusOverride) {
  return { pos, q: lookQuat(pos, target, up || V(0, 1, 0)), fov, K, focus: focusOverride ?? pos.distanceTo(target), target, up: (up || V(0, 1, 0)).clone() };
}
// mezcla en coordenadas cilíndricas alrededor del eje de la urna (la cámara nunca atraviesa la urna)
function blendShot(a, b, w) {
  if (w <= 0) return a; if (w >= 1) return b;
  const ra = Math.hypot(a.pos.x, a.pos.z), rb = Math.hypot(b.pos.x, b.pos.z);
  const aa = Math.atan2(a.pos.x, a.pos.z); let ab = Math.atan2(b.pos.x, b.pos.z);
  while (ab - aa > Math.PI) ab -= 2 * Math.PI; while (ab - aa < -Math.PI) ab += 2 * Math.PI;
  const r = lerp(ra, rb, w), an = lerp(aa, ab, w), y = lerp(a.pos.y, b.pos.y, w);
  const pos = V(Math.sin(an) * r, y, Math.cos(an) * r);
  const target = a.target.clone().lerp(b.target, w);
  const up = a.up.clone().lerp(b.up, w).normalize();
  return { pos, q: lookQuat(pos, target, up), fov: lerp(a.fov, b.fov, w), K: lerp(a.K, b.K, w), focus: lerp(a.focus, b.focus, w), target, up };
}
function orbitPoint(phi, rTarget, dist, elevDeg, yT = 0.0) {
  const tgt = radial(phi, rTarget, yT);
  const el = elevDeg * DEG;
  const pos = radial(phi, rTarget + dist * Math.cos(el), dist * Math.sin(el));
  return { pos, tgt };
}
function proposalShot(k, tau, P) {
  const phi = phiOf(k) + lerp(-2.2, 2.2, smooth(tau / P)) * DEG;
  const u = smooth(tau / P);
  const dist = lerp(0.47, 0.43, u), el = lerp(58, 62, u);
  const rB = ENV.r + BAL.out;
  const o = orbitPoint(phi, rB + 0.036, dist, el, 0.0);
  return shot(o.pos, o.tgt, 36, 11, null, o.pos.distanceTo(radial(phiOf(k), rB, 0)));
}
function topShot(t, t0, t1, h0, h1, rot0, rot1) {
  const u = smooth(range(t, t0, t1));
  const h = lerp(h0, h1, u), rot = lerp(rot0, rot1, range(t, t0, t1));
  const pos = V(Math.sin(rot) * h * 0.22, h, Math.cos(rot) * h * 0.22);
  const up = V(-Math.sin(rot), 0, -Math.cos(rot));
  return shot(pos, V(Math.sin(rot) * 0.05, 0, Math.cos(rot) * 0.05), 46, 7, up, h);
}
function revealOrbit(t) {
  const T = TL.timeline;
  const r0 = T.blocks_r[0][0];
  // la cámara reposa en cada sobre durante el volteo y viaja entre sobres (idéntico para los cinco)
  const x = (t - (r0 + T.flip_land)) / T.R;
  let k = Math.floor(x), f = (x - k) * T.R, ang;
  const m0 = 0.62, m1 = T.R - T.flip_dur - 0.08;
  if (k < 0) ang = 0;
  else if (k >= 4) ang = 288 * DEG + (t - (r0 + 4 * T.R + T.flip_land)) * 2.5 * DEG;
  else ang = 72 * DEG * (k + smoother((f - m0) / (m1 - m0)));
  const o = orbitPoint(ang, ENV.r + 0.068, 0.50, 77, 0.0);
  return shot(o.pos, o.tgt, 36, 10, null);
}

function getCam(t) {
  const T = TL.timeline;
  let s;
  if (t < T.cut_to_urn) {
    // macro del sello
    const u = t / T.cut_to_urn;
    const hitU = easeOut(range(t, T.seal_hit, T.seal_hit + 0.14));
    const dist = lerp(0.35, 0.32, smooth(u)) * (1 - 0.13 * hitU), el = 50 * DEG;
    const tgt = SEAL_AT.clone().add(V(0, 0.004, 0.022));
    const pos = tgt.clone().add(V(Math.sin(-0.08 + u * 0.05) * dist * Math.cos(el), dist * Math.sin(el), Math.cos(-0.08 + u * 0.05) * dist * Math.cos(el)));
    s = shot(pos, tgt, 30, 9);
    // golpe: sacudida
    const th = t - T.seal_hit;
    if (th > 0) { const a = Math.exp(-th * 11) * 0.0032; s.pos.add(V(Math.sin(th * 95) * a, Math.sin(th * 73 + 1) * a, Math.sin(th * 61) * a * 0.5)); }
  } else if (t < T.s2[0]) {
    const u = range(t, T.cut_to_urn, T.s2[0] + 1.2);
    const pos = V(lerp(-0.035, -0.02, u), lerp(0.46, 0.40, smooth(u)), lerp(1.78, 1.62, u));
    s = shot(pos, V(0, lerp(0.13, 0.11, u), 0), 32, 6);
  } else if (t < T.s3[0]) {
    const u = range(t, T.s2[0], T.s3[0]);
    const e = smoother(u);
    const pos = V(lerp(-0.02, 0.0, e), lerp(0.40, 1.05, e), lerp(1.62, 1.25, e));
    s = shot(pos, V(0, lerp(0.11, 0.03, e), 0), lerp(32, 44, e), lerp(6, 6, e));
  } else if (t < T.s4[0]) {
    const k = Math.min(4, Math.floor((t - T.s3[0]) / T.P));
    const tau = t - T.blocks_p[k][0];
    s = proposalShot(k, tau, T.P);
  } else if (t < T.s5[0]) {
    s = topShot(t, T.s4[0], T.s5[0], 2.3, 2.15, -6 * DEG, 10 * DEG);
  } else if (t < T.s6[0]) {
    const topEnd = topShot(T.s5[0], T.s4[0], T.s5[0], 2.3, 2.15, -6 * DEG, 10 * DEG);
    const r0 = T.blocks_r[0][0];
    const orb = revealOrbit(t);
    const w = smoother(range(t, T.s5[0] + 0.05, r0 + 0.2));
    s = blendShot(topEnd, orb, w);
    // al final: grúa hacia arriba para ver los cinco
    const lastLand = T.blocks_r[4][0] + T.flip_land;
    const fin = finalShot(t);
    const w2 = smoother(range(t, lastLand + 0.45, T.s6[0] + 1.0));
    if (w2 > 0) s = blendShot(s, fin, w2);
  } else {
    const T6 = T.s6;
    const lastLand = T.blocks_r[4][0] + T.flip_land;
    const orb = revealOrbit(t);
    const fin = finalShot(t);
    const w2 = smoother(range(t, lastLand + 0.45, T.s6[0] + 1.0));
    s = blendShot(orb, fin, w2);
  }
  if (window.coverMode) s = shot(V(0.0, 1.30, 1.62), V(0, 0.20, 0.0), 46, 6);
  if (window.debugCam) { const d = window.debugCam; s = shot(V(...d.pos), V(...d.target), d.fov || 40, 0.5); }
  // respiración de cámara: siempre se mueve un poco
  const br = 0.0016;
  s.pos = s.pos.clone().add(V(vnoise(t * 0.7, 1) * br, vnoise(t * 0.6, 2) * br, vnoise(t * 0.5, 3) * br));
  const qb = new THREE.Quaternion().setFromEuler(new THREE.Euler(vnoise(t * 0.45, 4) * 0.0018, vnoise(t * 0.4, 5) * 0.0018, vnoise(t * 0.3, 6) * 0.001));
  s.q = s.q.clone().multiply(qb);
  return s;
}
function finalShot(t) {
  const T = TL.timeline;
  const u = range(t, T.s6[0], T.s6[1]);
  const h = lerp(2.3, 2.15, u), rot = lerp(4 * DEG + 288 * DEG, 8 * DEG + 288 * DEG, u);
  // cenital, ligeramente inclinado
  const pos = V(Math.sin(rot) * h * 0.22, h, Math.cos(rot) * h * 0.22);
  const up = V(-Math.sin(rot), 0, -Math.cos(rot));
  return shot(pos, V(Math.sin(rot) * 0.05, 0, Math.cos(rot) * 0.05), 46, 7, up, h);
}

// ------------------------------------------------------------- update/render
let lastUiKey = '';
function update(t) {
  const T = TL.timeline;
  // --- luces
  const spot = OBJ.spot, sspot = OBJ.sspot;
  const inSeal = t < T.cut_to_urn;
  const dimEnd = range(t, T.s6[0] + 0.25, T.s6[0] + 1.0);
  const tc = t - T.cut_to_urn;
  const switchOn = tc < 0.1 ? 0 : tc < 0.15 ? 0.85 : tc < 0.21 ? 0.08 : tc < 0.26 ? 1.25 : 1.0 + 0.25 * Math.exp(-(tc - 0.26) * 6);
  const spotI = inSeal ? 0 : lerp(SPOT_I, SPOT_I * 0.1, smooth(dimEnd)) * switchOn;
  spot.intensity = spotI;
  sspot.intensity = inSeal ? SSPOT_I * smooth(range(t, 0.0, 0.1)) * (1 + 0.6 * Math.exp(-Math.max(0, t - T.seal_hit) * 9) * (t >= T.seal_hit ? 1 : 0)) : 0;
  OBJ.hemi.intensity = inSeal ? 0.05 : lerp(0.22, 0.14, dimEnd);
  OBJ.rim.intensity = inSeal ? 0.05 : 0.30;
  // --- sello
  const hit = T.seal_hit;
  const sy = t < hit ? lerp(0.10, 0.0, Math.pow(t / hit, 1.6)) : 0;
  OBJ.seal.position.copy(SEAL_AT).add(V(0, sy, 0));
  OBJ.seal.rotation.set((1 - range(t, 0, hit)) * 0.35, (1 - smooth(range(t, 0, hit))) * 0.5, (1 - range(t, 0, hit)) * -0.2);
  const squash = t >= hit ? 1 - Math.exp(-(t - hit) * 18) * 0.25 * Math.cos((t - hit) * 40) : 1;
  OBJ.disc.scale.set(1 + (1 - squash) * 0.3, squash, 1 + (1 - squash) * 0.3);
  OBJ.puddle.visible = t >= hit;
  OBJ.puddle.scale.setScalar(t >= hit ? 0.75 + 0.25 * easeOut(range(t, hit, hit + 0.12)) : 0.01);
  OBJ.seal.visible = t < T.cut_to_urn + 0.1;
  // --- sobres
  for (let k = 0; k < 5; k++) {
    const e = OBJ.envelopes[k];
    const st = envState(k, t);
    e.g.position.copy(st.pos); e.g.quaternion.copy(st.q);
    const sl = ballotSlide(k, t);
    e.bal.position.z = sl.out;
    drawBallot(k, sl.n);
    // sombras de contacto: solo cuando está sobre la mesa
    const onTable = st.flown || st.pos.y < 0.02;
    const h = Math.max(0, st.pos.y - ENV.t / 2);
    e.cs.visible = onTable || st.pos.y < 0.2;
    e.cs.position.set(st.pos.x, 0.0004, st.pos.z);
    e.cs.rotation.set(-Math.PI / 2, 0, phiOf(k));
    e.cs.material.opacity = 0.2 * Math.exp(-h * 30) * (st.flown || st.pos.y < 0.2 ? 1 : 0);
    const bp = radial(phiOf(k), ENV.r + sl.out, 0.0003);
    e.bcs.position.set(bp.x, 0.0003, bp.z); e.bcs.rotation.set(-Math.PI / 2, 0, phiOf(k));
    e.bcs.visible = sl.out > 0.01;
  }
}

function sweepParams(t) {
  // barrido de luz centrado en cada corte (entrada y salida de cada propuesta, idéntico)
  const T = TL.timeline;
  const cuts = []; for (let k = 0; k <= 5; k++) cuts.push(T.s3[0] + k * T.P);
  const half = 0.42;
  for (const c of cuts) {
    if (t >= c - half && t < c + half) {
      const u = (t - (c - half)) / (2 * half);
      return { pos: lerp(-0.45, 1.45, u), amt: Math.sin(Math.PI * u) ** 1.5, flash: Math.exp(-Math.pow((u - 0.5) / 0.12, 2)) };
    }
  }
  return { pos: -1, amt: 0, flash: 0 };
}

function drawUI(t) {
  const T = TL.timeline;
  ux.clearRect(0, 0, W, H);
  if (window.coverMode) {
    title(['¿DE QUIÉN ES', 'CADA', 'PROPUESTA?'], 10, 0, 20, { size: 84, y: 450, fadeIn: 0.001, fadeOut: 0.001 });
    ux.save(); ux.font = '500 30px PlexMono'; ux.fillStyle = CREAM; ux.globalAlpha = 0.8; ux.shadowColor = 'rgba(0,0,0,0.7)'; ux.shadowBlur = 12;
    spaced(ux, 'TEST A CIEGAS · VIVIENDA · 29-N', W / 2, 668, 8); ux.restore();
    uiTex.needsUpdate = true; return;
  }
  // títulos
  title(['ELIGE UNA'], t, T.seal_hit, T.s2[0] + 0.15, { size: 96, y: 440, slam: true, fadeIn: 0.06, kicker: 'TEST A CIEGAS · 29-N' });
  title(['NO TE DIGO', 'DE QUIÉN SON'], t, T.title_rules - 0.1, T.s3[0] - 0.12, { size: 76, y: 370 });
  title(['COMENTA', 'EL NÚMERO'], t, T.s4[0] + 0.35, T.s5[0] + 0.1, { size: 86, y: 430 });
  title(['¿TE HA', 'SORPRENDIDO?'], t, T.s6[0] + 0.9, T.s6[1] - 0.35, { size: 88, y: 840, fadeOut: 0.6 });
  // firma
  if (t > T.s6[0] + 1.4) {
    const a = smooth(range(t, T.s6[0] + 1.4, T.s6[0] + 2.0)) * (1 - smooth(range(t, T.s6[1] - 0.6, T.s6[1] - 0.25)));
    ux.save(); ux.globalAlpha = a * 0.72; ux.font = '600 30px InterDisplay'; ux.fillStyle = CREAM; ux.shadowColor = 'rgba(0,0,0,0.6)'; ux.shadowBlur = 10;
    spaced(ux, 'ALEIX JIMÉNEZ', W / 2, SAFE.bottom - 40, 9.5); ux.restore();
  }
  // número grande en la esquina (propuestas)
  if (t >= T.s3[0] && t < T.s4[0]) {
    const k = Math.min(4, Math.floor((t - T.s3[0]) / T.P));
    const tau = t - T.blocks_p[k][0];
    const a = smooth(range(tau, 0.22, 0.6)) * (1 - smooth(range(tau, T.P - 0.5, T.P - 0.3)));
  }
  // línea de fuente fija (propuestas, elección y revelación)
  const sa = smooth(range(t, T.s3[0] + 0.2, T.s3[0] + 0.6)) * (1 - smooth(range(t, T.s6[0] + 0.3, T.s6[0] + 0.8)));
  sourceLine(t, sa);
  subtitles(t);
  uiTex.needsUpdate = true;
}

const tmpM = new THREE.Matrix4();
function render(t) {
  const T = TL.timeline;
  const PR = window.__prof; const mark = (n) => { if (PR) { const gl = renderer.getContext(); const px = new Uint8Array(4); gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px); const now = performance.now(); PR[n] = (PR[n] || 0) + now - PR._t; PR._t = now; } }; if (PR) PR._t = performance.now();
  update(t);
  mark('update');
  const cam = getCam(t);
  camera.position.copy(cam.pos); camera.quaternion.copy(cam.q); camera.fov = cam.fov; camera.updateProjectionMatrix(); camera.updateMatrixWorld();
  // enfoque y profundidad de campo (modelo 1/z)
  const setCam = (u) => { u.cNear.value = camera.near; u.cFar.value = camera.far; u.cocK.value = cam.K; u.focus.value = cam.focus; u.cocMax.value = 30; };
  // 1) escena
  renderer.setRenderTarget(RT.main);
  if (!window.__skipScene) renderer.render(scene, camera);
  mark('scene');
  // 2) DOF media resolución
  setCam(P.down.u); P.down.u.tColor.value = RT.main.texture; P.down.u.tDepth.value = RT.main.depthTexture; P.down.run(RT.half);
  setCam(P.blur.u); P.blur.u.tHalf.value = RT.half.texture; P.blur.run(RT.blur);
  mark('dof');
  // 3) haz volumétrico
  setCam(P.beam.u);
  P.beam.u.tDepth.value = RT.main.depthTexture; P.beam.u.invProj.value.copy(camera.projectionMatrixInverse); P.beam.u.camWorld.value.copy(camera.matrixWorld);
  P.beam.u.camPos.value.copy(camera.position); P.beam.u.sInt.value = OBJ.spot.intensity / SPOT_I; P.beam.u.time.value = t;
  P.beam.run(RT.beam);
  mark('beam');
  // 4) composición + barrido
  const sw = sweepParams(t);
  setCam(P.comp.u);
  Object.assign(P.comp.u.tColor, { value: RT.main.texture }); P.comp.u.tDepth.value = RT.main.depthTexture; P.comp.u.tBlur.value = RT.blur.texture; P.comp.u.tBeam.value = RT.beam.texture;
  P.comp.u.dbgBeam.value = window.dbgBeam ? 1 : 0; P.comp.u.sweepPos.value = sw.pos; P.comp.u.sweepAmt.value = sw.amt; P.comp.u.flash.value = sw.flash + (t >= T.seal_hit && t < T.cut_to_urn ? 0.55 * Math.exp(-(t - T.seal_hit) * 16) : 0);
  P.comp.run(RT.comp);
  mark('comp');
  // 5) polvo (bokeh) sobre la composición
  const pxPerRad = H / (2 * Math.tan(camera.fov * DEG / 2));
  for (const m of OBJ.dust.mats) {
    const u = m.uniforms;
    u.time.value = t; u.cocK.value = cam.K; u.focus.value = cam.focus; u.pxPerRad.value = pxPerRad; u.tDepth.value = RT.main.depthTexture;
    u.sInt.value = OBJ.spot.intensity / SPOT_I * 9.0; u.s2Int.value = OBJ.sspot.intensity / SSPOT_I * 2.5;
    u.s2Pos.value.copy(OBJ.sspot.position); u.s2Dir.value.copy(OBJ.sspot.target.position).sub(OBJ.sspot.position).normalize();
    u.tImpact.value = T.seal_hit;
  }
  renderer.autoClear = false;
  renderer.setRenderTarget(RT.comp);
  renderer.render(OBJ.dust.scene, camera);
  renderer.autoClear = true;
  mark('dust');
  // 6) bloom
  P.bright.u.tSrc.value = RT.comp.texture; P.bright.u.texel.value.set(1 / W, 1 / H); P.bright.run(RT.b[0]);
  for (let i = 1; i < 4; i++) { P.dn.u.tSrc.value = RT.b[i - 1].texture; P.dn.u.texel.value.set(1 / RT.b[i - 1].width, 1 / RT.b[i - 1].height); P.dn.run(RT.b[i]); }
  mark('bloom');
  // 7) rótulos + final
  if (!window.__skipUI) drawUI(t);
  mark('ui');
  const F = P.final.u;
  F.tComp.value = RT.comp.texture; F.tB0.value = RT.b[0].texture; F.tB1.value = RT.b[1].texture; F.tB2.value = RT.b[2].texture; F.tB3.value = RT.b[3].texture; F.tUI.value = uiTex;
  F.time.value = t;
  F.exposure.value = inSealExposure(t);
  F.ca.value = 0.012 + (t >= T.seal_hit && t < T.cut_to_urn ? 0.07 * Math.exp(-(t - T.seal_hit) * 9) : 0);
  // fundido a negro al final (bucle) y desde negro al principio
  F.fade.value = smooth(range(t, 0.0, 0.07)) * (1 - smooth(range(t, T.s6[1] - 0.55, T.s6[1] - 0.04)));
  P.final.run(null);
  mark('final');
}
function inSealExposure(t) { const T = TL.timeline; return t < T.cut_to_urn ? 0.95 : 0.86; }

// ------------------------------------------------------------------- API
window.setup = async (timings) => {
  TL = timings;
  await Promise.all([
    document.fonts.load('400 70px CourierPrime'), document.fonts.load('700 70px CourierPrime'),
    document.fonts.load('400 22px PlexMono'), document.fonts.load('500 24px PlexMono'),
    document.fonts.load('600 80px Fraunces'), document.fonts.load('600 76px InterDisplay'),
  ]);
  buildScene();
  buildPost();
  prepareTexts();
  render(0);
  return { ok: true, frames: TL.timeline.frames };
};
window.renderFrame = (n, fmt = 'jpeg', q = 0.95) => {
  render(n / TL.fps);
  if (fmt === 'none') return '';
  return canvas.toDataURL(fmt === 'png' ? 'image/png' : 'image/jpeg', q);
};
window.renderAt = (t, fmt = 'jpeg', q = 0.95) => { render(t); return canvas.toDataURL(fmt === 'png' ? 'image/png' : 'image/jpeg', q); };
window.renderCover = () => {
  window.coverMode = true;
  const T = TL.timeline;
  render(T.s3[0] - 0.6);
  window.coverMode = false;
  return canvas.toDataURL('image/jpeg', 0.96);
};
window.__ready = true;
window.__dbg = { envState, OBJ, getCam: (t) => getCam(t), update };
