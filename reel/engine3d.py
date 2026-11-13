"""Motor 3D mínimo (proyección + pintor + sombreado plano) sobre skia, y las tres
"maquetas" que sustituyen a las grabaciones de Google Earth cuando no existen:
calle de Madrid, Candelago (costa) y A Barca (valle del Miño)."""
from __future__ import annotations

import math

import numpy as np
import skia

from gfx import H, W

SUN = np.array([-0.55, -0.42, 0.72])
SUN = SUN / np.linalg.norm(SUN)
WARM = np.array([1.00, 0.90, 0.76])     # luz cálida
COOL = np.array([0.42, 0.50, 0.66])     # ambiente frío (sombras)


def hexc(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])


def shade(base, n, amb=0.66, dif=0.85, sun=None):
    lam = max(0.0, float(np.dot(n, SUN if sun is None else sun)))
    sky = 0.5 + 0.5 * n[2]
    c = base * (COOL * amb * (0.75 + 0.35 * sky) + WARM * dif * lam)
    return np.clip(c, 0, 1)


def vnoise(x, y, seed=0):
    """Ruido suave (suma de senos) vectorizado."""
    r = np.random.RandomState(seed)
    out = np.zeros_like(np.asarray(x, float))
    amp = 1.0
    for k in range(5):
        fx, fy = r.uniform(0.6, 1.4, 2) * (2 ** k) / 120
        ph = r.uniform(0, 6.28, 2)
        out = out + amp * np.sin(x * fx + ph[0] + np.sin(y * fy * 0.7 + ph[1]) * 1.3) * np.cos(y * fy + ph[1])
        amp *= 0.5
    return out / 1.9


# --------------------------------------------------------------------------------------
class Camera:
    def __init__(self, pos, target, fov=58.0, vp=(0, 0, W, H), roll=0.0):
        self.pos = np.asarray(pos, float)
        self.target = np.asarray(target, float)
        self.fov = fov
        self.vp = vp
        f = self.target - self.pos
        f /= np.linalg.norm(f)
        r = np.cross(f, [0, 0, 1.0])
        r /= np.linalg.norm(r)
        u = np.cross(r, f)
        if roll:
            cr, sr = math.cos(roll), math.sin(roll)
            r, u = r * cr + u * sr, -r * sr + u * cr
        self.f, self.r, self.u = f, r, u
        self.fpx = (vp[3] / 2) / math.tan(math.radians(fov) / 2)

    def cam_space(self, P):
        d = np.asarray(P, float) - self.pos
        return d @ self.r, d @ self.u, d @ self.f

    def project(self, P, scale=1.0):
        """P (...,3) -> (...,2) en píxeles del viewport (escalado), y profundidad."""
        x, y, z = self.cam_space(P)
        zz = np.maximum(z, 1e-3)
        vx, vy, vw, vh = self.vp
        sx = (vx + vw / 2 + self.fpx * x / zz) * scale
        sy = (vy + vh / 2 - self.fpx * y / zz) * scale
        return np.stack([sx, sy], -1), z

    def p2(self, x, y, z=0.0):
        p, _ = self.project(np.array([x, y, z]))
        return float(p[0]), float(p[1])


# --------------------------------------------------------------------------------------
class Mesh:
    """Triángulos con color por vértice. obj = -1 -> se ordena por triángulo."""

    def __init__(self, sun=None):
        self.sun = SUN if sun is None else np.asarray(sun, float) / np.linalg.norm(sun)
        self.T, self.C, self.N, self.PN, self.obj, self.intra, self.layer, self.cull = [], [], [], [], [], [], [], []
        self.obj_count = 0

    def new_obj(self):
        self.obj_count += 1
        return self.obj_count - 1

    def tri(self, a, b, c, color, obj=-1, intra=0, layer=1, cull=True, outward=None, parent_n=None, lit=True):
        a, b, c = (np.asarray(p, float) for p in (a, b, c))
        n = np.cross(b - a, c - a)
        ln = np.linalg.norm(n)
        if ln < 1e-9:
            return
        n /= ln
        cen = (a + b + c) / 3
        if outward is not None and np.dot(n, cen - np.asarray(outward, float)) < 0:
            b, c, n = c, b, -n
        color = np.asarray(color, float)
        if color.ndim == 1:
            rgb = shade(color[:3], n, sun=self.sun) if lit else color[:3]
            a_ = color[3] if len(color) > 3 else 1.0
            cols = np.tile(np.r_[rgb, a_], (3, 1))
        else:
            cols = color
        self.T.append(np.stack([a, b, c]))
        self.C.append(cols)
        self.N.append(n)
        self.PN.append(np.zeros(3) if parent_n is None else np.asarray(parent_n, float))
        self.obj.append(obj)
        self.intra.append(intra)
        self.layer.append(layer)
        self.cull.append(cull)

    def quad(self, a, b, c, d, color, **kw):
        self.tri(a, b, c, color, **kw)
        self.tri(a, c, d, color, **kw)

    def box(self, x0, y0, z0, x1, y1, z1, color, obj=None, top=None, bottom=False, intra=0, parent_n=None, layer=1):
        if obj is None:
            obj = self.new_obj()
        ctr = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
        P = lambda x, y, z: (x, y, z)
        faces = [
            ((x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)),  # -y
            ((x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)),  # +y
            ((x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)),  # -x
            ((x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)),  # +x
            ((x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)),  # top
        ]
        for i, f in enumerate(faces):
            colr = top if (i == 4 and top is not None) else color
            self.quad(*[P(*v) for v in f], colr, obj=obj, intra=intra, outward=ctr, parent_n=parent_n, layer=layer)
        return obj

    def gable(self, x0, y0, x1, y1, zb, zw, zr, wall, roof, obj=None, along_x=True, overhang=0.35, roof2=None):
        """Casa con tejado a dos aguas. Cumbrera paralela a x (along_x) o a y."""
        if obj is None:
            obj = self.new_obj()
        self.box(x0, y0, zb, x1, y1, zw, wall, obj=obj, top=wall * 0.6)
        o = overhang
        ctr = np.array([(x0 + x1) / 2, (y0 + y1) / 2, (zw + zr) / 2])
        roof2 = roof if roof2 is None else roof2
        if along_x:
            ym = (y0 + y1) / 2
            # hastiales
            self.tri((x0, y0, zw), (x0, y1, zw), (x0, ym, zr), wall, obj=obj, intra=1, outward=ctr)
            self.tri((x1, y0, zw), (x1, y1, zw), (x1, ym, zr), wall, obj=obj, intra=1, outward=ctr)
            self.quad((x0 - o, y0 - o, zw - 0.2), (x1 + o, y0 - o, zw - 0.2), (x1 + o, ym, zr), (x0 - o, ym, zr), roof, obj=obj, intra=2, outward=ctr - [0, 0, 3])
            self.quad((x0 - o, y1 + o, zw - 0.2), (x1 + o, y1 + o, zw - 0.2), (x1 + o, ym, zr), (x0 - o, ym, zr), roof2, obj=obj, intra=2, outward=ctr - [0, 0, 3])
        else:
            xm = (x0 + x1) / 2
            self.tri((x0, y0, zw), (x1, y0, zw), (xm, y0, zr), wall, obj=obj, intra=1, outward=ctr)
            self.tri((x0, y1, zw), (x1, y1, zw), (xm, y1, zr), wall, obj=obj, intra=1, outward=ctr)
            self.quad((x0 - o, y0 - o, zw - 0.2), (x0 - o, y1 + o, zw - 0.2), (xm, y1 + o, zr), (xm, y0 - o, zr), roof, obj=obj, intra=2, outward=ctr - [0, 0, 3])
            self.quad((x1 + o, y0 - o, zw - 0.2), (x1 + o, y1 + o, zw - 0.2), (xm, y1 + o, zr), (xm, y0 - o, zr), roof2, obj=obj, intra=2, outward=ctr - [0, 0, 3])
        return obj

    def wall(self, p0, p1, z0, z1, thick, color, obj=None):
        """Muro fino entre dos puntos (x, y)."""
        if obj is None:
            obj = self.new_obj()
        p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
        d = p1 - p0
        L = np.linalg.norm(d)
        if L < 1e-6:
            return obj
        n = np.array([-d[1], d[0]]) / L * thick / 2
        a, b, c, e = p0 + n, p1 + n, p1 - n, p0 - n
        ctr = ((p0 + p1) / 2).tolist() + [(z0 + z1) / 2]
        Q = lambda q, z: (q[0], q[1], z)
        for u, v in ((a, b), (b, c), (c, e), (e, a)):
            self.quad(Q(u, z0), Q(v, z0), Q(v, z1), Q(u, z1), color, obj=obj, outward=ctr)
        self.quad(Q(a, z1), Q(b, z1), Q(c, z1), Q(e, z1), color, obj=obj, outward=ctr)
        return obj

    def blob(self, c, r, color, obj=None, rz=None, seed=0, intra=0):
        """Copa de árbol low-poly (icosaedro deformado)."""
        if obj is None:
            obj = self.new_obj()
        t = (1 + 5 ** 0.5) / 2
        V = np.array([[-1, t, 0], [1, t, 0], [-1, -t, 0], [1, -t, 0], [0, -1, t], [0, 1, t], [0, -1, -t], [0, 1, -t],
                      [t, 0, -1], [t, 0, 1], [-t, 0, -1], [-t, 0, 1]], float)
        V /= np.linalg.norm(V[0])
        rs = np.random.RandomState(seed)
        V = V * (1 + rs.uniform(-0.12, 0.12, (12, 1)))
        V = V * [r, r, rz or r] + np.asarray(c, float)
        F = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
             (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
        for a, b, cc in F:
            self.tri(V[a], V[b], V[cc], color, obj=obj, intra=intra, outward=c)
        return obj

    def cone(self, c, r, h, color, obj=None, n=7, intra=0):
        if obj is None:
            obj = self.new_obj()
        cx, cy, cz = c
        apex = (cx, cy, cz + h)
        ring = [(cx + r * math.cos(a), cy + r * math.sin(a), cz) for a in np.linspace(0, 2 * math.pi, n, endpoint=False)]
        for i in range(n):
            self.tri(ring[i], ring[(i + 1) % n], apex, color, obj=obj, intra=intra, outward=(cx, cy, cz + h * 0.3))
        return obj

    def finalize(self):
        self.T = np.array(self.T, np.float64)
        self.C = np.array(self.C, np.float64)
        self.N = np.array(self.N)
        self.PN = np.array(self.PN)
        self.obj = np.array(self.obj, int)
        self.intra = np.array(self.intra, int)
        self.layer = np.array(self.layer, int)
        self.cull = np.array(self.cull, bool)
        self.cen = self.T.mean(axis=1)
        n = max(self.obj_count, 1)
        self.obj_cen = np.zeros((n, 3))
        self.obj_rad = np.zeros(n)
        for o in range(self.obj_count):
            m = self.obj == o
            if m.any():
                pts = self.T[m].reshape(-1, 3)
                self.obj_cen[o] = (pts.min(0) + pts.max(0)) / 2
                self.obj_rad[o] = np.linalg.norm(pts.max(0) - pts.min(0)) / 2
        return self


def render_mesh(canvas, mesh: Mesh, cam: Camera, ss=1.0, fog=None, colors=None, near=0.6, obj_bias=1.0):
    """Dibuja la malla con algoritmo del pintor. fog=(rgb, d0, d1, max_amount)."""
    T = mesh.T
    C = mesh.C if colors is None else colors
    x, y, z = cam.cam_space(T)  # (n,3)
    valid = (z > near).all(axis=1)
    view = cam.pos - mesh.cen
    vis = (np.einsum("ij,ij->i", mesh.N, view) > 0) | ~mesh.cull
    pn_ok = (np.abs(mesh.PN).sum(1) == 0) | (np.einsum("ij,ij->i", mesh.PN, view) > 0)
    keep = valid & vis & pn_ok
    # profundidad de orden
    zc = z.mean(axis=1)
    key = zc.copy()
    has_obj = mesh.obj >= 0
    if has_obj.any():
        oc = mesh.obj_cen[mesh.obj[has_obj]]
        _, _, ozc = cam.cam_space(oc)
        key[has_obj] = ozc - mesh.obj_rad[mesh.obj[has_obj]] * obj_bias
    idx = np.nonzero(keep)[0]
    if len(idx) == 0:
        return
    order = np.lexsort((mesh.intra[idx], -key[idx], mesh.layer[idx]))
    idx = idx[order]
    vx, vy, vw, vh = cam.vp
    zz = z[idx]
    sx = (vx + vw / 2 + cam.fpx * x[idx] / zz) * ss
    sy = (vy + vh / 2 - cam.fpx * y[idx] / zz) * ss
    cols = C[idx].copy()
    if fog is not None:
        frgb, d0, d1, fmax = fog
        dist = np.linalg.norm(T[idx] - cam.pos, axis=2)
        fa = np.clip((dist - d0) / (d1 - d0), 0, 1) ** 1.2 * fmax
        cols[..., :3] = cols[..., :3] * (1 - fa[..., None]) + np.asarray(frgb)[None, None, :] * fa[..., None]
    c8 = (np.clip(cols, 0, 1) * 255).astype(np.uint32)
    argb = (c8[..., 3] << 24) | (c8[..., 0] << 16) | (c8[..., 1] << 8) | c8[..., 2]
    pts = [skia.Point(a, b) for a, b in zip(sx.ravel().tolist(), sy.ravel().tolist())]
    verts = skia.Vertices(skia.Vertices.kTriangles_VertexMode, pts, None, argb.ravel().tolist())
    canvas.drawVertices(verts, skia.Paint(), skia.BlendMode.kDst)


# --------------------------------------------------------------------------------------
# Terreno (heightfield) con color por vértice y sombreado suave
# --------------------------------------------------------------------------------------
class Terrain:
    def __init__(self, x0, x1, y0, y1, step, hfun, cfun, sun=None):
        sun = SUN if sun is None else np.asarray(sun, float) / np.linalg.norm(sun)
        xs = np.arange(x0, x1 + 1e-6, step)
        ys = np.arange(y0, y1 + 1e-6, step)
        X, Y = np.meshgrid(xs, ys)
        Z = hfun(X, Y)
        self.xs, self.ys, self.Z, self.hfun = xs, ys, Z, hfun
        gy, gx = np.gradient(Z, step)
        Nn = np.dstack([-gx, -gy, np.ones_like(Z)])
        Nn /= np.linalg.norm(Nn, axis=2, keepdims=True)
        base = cfun(X, Y, Z, Nn)  # (ny,nx,3)
        lam = np.clip(Nn @ sun, 0, 1)[..., None]
        sky = (0.5 + 0.5 * Nn[..., 2])[..., None]
        self.base = base
        self.lit = np.clip(base * (COOL * 0.66 * (0.75 + 0.35 * sky) + WARM * 0.85 * lam), 0, 1)
        self.water = Z <= 0.0
        self.X, self.Y = X, Y

    def height(self, x, y):
        return float(self.hfun(np.array(x, float), np.array(y, float)))

    def add_to(self, mesh: Mesh):
        ny, nx = self.Z.shape
        Zc = np.maximum(self.Z, 0.0)
        P = np.dstack([self.X, self.Y, Zc])
        self.vstart = len(mesh.T)
        for j in range(ny - 1):
            for i in range(nx - 1):
                a, b, c, d = P[j, i], P[j, i + 1], P[j + 1, i + 1], P[j + 1, i]
                ca, cb, cc, cd = (np.r_[self.lit[jj, ii], 1.0] for jj, ii in ((j, i), (j, i + 1), (j + 1, i + 1), (j + 1, i)))
                mesh.T.append(np.stack([a, b, c])); mesh.C.append(np.stack([ca, cb, cc]))
                mesh.T.append(np.stack([a, c, d])); mesh.C.append(np.stack([ca, cc, cd]))
                for _ in range(2):
                    mesh.N.append(np.array([0, 0, 1.0])); mesh.PN.append(np.zeros(3)); mesh.obj.append(-1)
                    mesh.intra.append(0); mesh.layer.append(1); mesh.cull.append(False)
        self.vend = len(mesh.T)
        self.grid_shape = (ny, nx)


def water_colors(mesh: Mesh, terr: Terrain, t, deep, shallow, foam):
    """Colores animados del agua (mar / río) para el instante t."""
    C = mesh.C.copy()
    s, e = terr.vstart, terr.vend
    T = mesh.T[s:e]
    zt = terr.hfun(T[..., 0], T[..., 1])
    wmask = zt < 0.6
    if not wmask.any():
        return C
    depth = np.clip(-zt / 9.0, 0, 1)
    wave = 0.5 + 0.5 * np.sin(T[..., 0] * 0.09 + T[..., 1] * 0.05 - t * 1.6) * np.sin(T[..., 1] * 0.07 - t * 0.9 + T[..., 0] * 0.02)
    wc = shallow[None, None, :] * (1 - depth[..., None]) + deep[None, None, :] * depth[..., None]
    wc = wc * (0.9 + 0.16 * wave[..., None])
    fz = np.clip(1 - np.abs(zt + 0.5) / 1.6, 0, 1) * (0.55 + 0.45 * np.sin(t * 2.2 - zt * 2.5 + T[..., 1] * 0.08))
    wc = wc * (1 - fz[..., None] * 0.7) + foam[None, None, :] * fz[..., None] * 0.7
    sub = C[s:e]
    land = sub[..., :3]
    blend = np.clip((0.6 - zt) / 0.8, 0, 1)[..., None]
    sub[..., :3] = land * (1 - blend) + wc * blend
    C[s:e] = sub
    return C


# --------------------------------------------------------------------------------------
# Maquetas
# --------------------------------------------------------------------------------------
class Madrid:
    PLAN_Y = 21.0  # centro de la planta sobre la calzada

    def __init__(self, seed=3):
        rs = np.random.RandomState(seed)
        m = Mesh(sun=(0.42, -0.62, 0.62))
        asphalt, sidewalk, curb = hexc("#3B3E43"), hexc("#9C968D"), hexc("#B9B2A6")
        y0, y1 = -80.0, 420.0
        G = dict(layer=0, cull=False)
        for ya in np.arange(y0, y1, 4.0):
            yb = ya + 4.0
            m.quad((-5.6, ya, 0), (5.6, ya, 0), (5.6, yb, 0), (-5.6, yb, 0), asphalt * (0.97 + 0.03 * np.sin(ya)), **G)
            for s in (-1, 1):
                m.quad((s * 5.6, ya, 0.15), (s * 9.5, ya, 0.15), (s * 9.5, yb, 0.15), (s * 5.6, yb, 0.15), sidewalk, **G)
                m.quad((s * 5.45, ya, 0.16), (s * 5.75, ya, 0.16), (s * 5.75, yb, 0.16), (s * 5.45, yb, 0.16), curb, **G)
        lane = hexc("#D8D2C6")
        for yy in np.arange(y0, y1, 9.0):
            if abs(yy - self.PLAN_Y) < 9:
                continue
            m.quad((-0.12, yy, 0.02), (0.12, yy, 0.02), (0.12, yy + 4.0, 0.02), (-0.12, yy + 4.0, 0.02), lane, **G)
        for zy in (68.0, 196.0):  # pasos de cebra
            for xx in np.arange(-5.0, 5.0, 1.1):
                m.quad((xx, zy, 0.03), (xx + 0.6, zy, 0.03), (xx + 0.6, zy + 4.5, 0.03), (xx, zy + 4.5, 0.03), lane * 0.95, **G)
        self.shadows = []
        facades = [hexc(h) for h in ("#E2D5C1", "#D6C3A5", "#C99B7C", "#E8E0D2", "#CBB596", "#D9CBB8", "#BE8E70")]
        glass, glass_lit = hexc("#465163"), hexc("#FFCB8A")
        for s in (-1, 1):
            yy = y0
            while yy < y1:
                bw = rs.uniform(10, 17)
                hgt = 3.2 * rs.randint(6, 9) + rs.uniform(0.5, 1.8)
                xa, xb = (9.5, 24) if s > 0 else (-24, -9.5)
                fc = facades[rs.randint(len(facades))] * rs.uniform(0.94, 1.04)
                ob = m.box(xa, yy, 0, xb, yy + bw - 0.25, hgt, fc, top=hexc("#7D746B"))
                face_x = xa if s > 0 else xb
                n_face = np.array([-s, 0, 0.0])
                # bajo comercial
                m.quad((face_x - s * 0.06, yy + 0.4, 0.2), (face_x - s * 0.06, yy + bw - 0.6, 0.2),
                       (face_x - s * 0.06, yy + bw - 0.6, 3.6), (face_x - s * 0.06, yy + 0.4, 3.6),
                       hexc("#4A423C"), obj=ob, intra=1, outward=(face_x - s * 5, yy + bw / 2, 2), parent_n=n_face)
                for k in range(int((bw - 1) // 3.4)):
                    wy = yy + 1.2 + k * 3.4
                    lit_c = glass_lit * 0.9 if rs.rand() < 0.5 else hexc("#3A4250")
                    m.quad((face_x - s * 0.1, wy, 0.6), (face_x - s * 0.1, wy + 2.4, 0.6), (face_x - s * 0.1, wy + 2.4, 3.0),
                           (face_x - s * 0.1, wy, 3.0), lit_c, obj=ob, intra=2, outward=(face_x - s * 5, wy, 2), parent_n=n_face, lit=False)
                # ventanas y balcones
                ncol = max(2, int(bw // 3.2))
                for fl in range(1, int(hgt // 3.2)):
                    zb = fl * 3.2 + 0.7
                    for k in range(ncol):
                        wy = yy + (k + 0.5) * (bw - 0.25) / ncol - 0.65
                        warm = rs.rand() < 0.12
                        gc = glass_lit if warm else glass * rs.uniform(0.85, 1.25)
                        m.quad((face_x - s * 0.08, wy, zb), (face_x - s * 0.08, wy + 1.3, zb), (face_x - s * 0.08, wy + 1.3, zb + 2.0),
                               (face_x - s * 0.08, wy, zb + 2.0), gc, obj=ob, intra=1,
                               outward=(face_x - s * 5, wy, zb), parent_n=n_face, lit=not warm)
                        if rs.rand() < 0.55:
                            bx0, bx1 = sorted((face_x, face_x - s * 0.9))
                            m.box(bx0, wy - 0.25, zb - 0.15, bx1, wy + 1.55, zb, hexc("#8A8278"), obj=ob, intra=3, parent_n=n_face)
                            outer = face_x - s * 0.9
                            m.box(outer - 0.05, wy - 0.25, zb, outer + 0.05, wy + 1.55, zb + 1.0,
                                  hexc("#3A3836"), obj=ob, intra=4, parent_n=n_face)
                # sombra proyectada (polígono en el suelo)
                fp = np.array([[xa, yy], [xb, yy], [xb, yy + bw], [xa, yy + bw]])
                off = -m.sun[:2] / m.sun[2] * hgt
                self.shadows.append((fp, off))
                yy += bw
        # árboles en las aceras
        for s in (-1, 1):
            for ty in np.arange(y0 + 4, y1, 11.0):
                if abs(ty - self.PLAN_Y) < 7 and False:
                    continue
                tx = s * 7.6 + rs.uniform(-0.2, 0.2)
                o = m.new_obj()
                m.box(tx - 0.18, ty - 0.18, 0, tx + 0.18, ty + 0.18, 3.4, hexc("#4B3E33"), obj=o)
                m.blob((tx, ty, 5.4), rs.uniform(2.1, 2.7), hexc("#5E7A55") * rs.uniform(0.85, 1.1), obj=o, rz=2.2, seed=int(ty) & 255, intra=1)
        # coches aparcados
        car_cols = [hexc(h) for h in ("#D9D4CC", "#2E3238", "#8A8F98", "#7A2E24", "#C8BBA6", "#3E4A5C")]
        for s in (-1, 1):
            for cy in np.arange(y0 + 10, y1, 7.5):
                if abs(cy - self.PLAN_Y) < 12 or rs.rand() < 0.3:
                    continue
                cx = s * 4.45
                cc = car_cols[rs.randint(len(car_cols))]
                o = m.new_obj()
                m.box(cx - 0.9, cy, 0.3, cx + 0.9, cy + 4.2, 1.05, cc, obj=o)
                m.box(cx - 0.8, cy + 1.0, 1.05, cx + 0.8, cy + 3.2, 1.55, hexc("#2A3038"), obj=o, intra=1)
        self.mesh = m.finalize()

    def camera(self, t, vp=(0, 0, W, H), dolly=0.0):
        """Cámara a baja altura avanzando despacio por la calle."""
        y = -6.0 + t * 1.3 + dolly
        return Camera((0.6, y, 11.5), (0.0, y + 26.0, 0.0), fov=62, vp=vp)

    def render(self, canvas, cam, ss):
        sky_paint(canvas, cam, ss, top="#273041", horizon="#D9C3A8")
        # suelo y sombras
        render_mesh(canvas, self.mesh_ground(), cam, ss, fog=(hexc("#D3BFA6"), 60, 380, 0.85))
        for fp, off in self.shadows:
            pts = np.vstack([fp, fp + off])
            hull = convex_hull(pts)
            P3 = np.c_[hull, np.full(len(hull), 0.2)]
            sp, z = cam.project(P3, ss)
            if (z < 0.6).any():
                continue
            p = skia.Paint(AntiAlias=True, Color=skia.ColorSetARGB(105, 18, 26, 44))
            p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 3 * ss))
            canvas.drawPath(_path(sp), p)
        render_mesh(canvas, self.mesh_objs(), cam, ss, fog=(hexc("#D3BFA6"), 60, 380, 0.85))

    def mesh_ground(self):
        if not hasattr(self, "_g"):
            self._g = _submesh(self.mesh, self.mesh.layer == 0)
            self._o = _submesh(self.mesh, self.mesh.layer != 0)
        return self._g

    def mesh_objs(self):
        self.mesh_ground()
        return self._o


class Candelago:
    """Aldea de piedra sobre la costa, con el mar a la vista."""

    def __init__(self, seed=7):
        rs = np.random.RandomState(seed)

        def shore(y):
            return -70 + 26 * np.sin(y / 75.0) + 11 * np.sin(y / 23.0 + 1.0)

        def h(x, y):
            d = x - shore(y)
            base = np.where(d < 0, d * 0.22, d * 0.16 + 6 * (1 - np.exp(-np.maximum(d, 0) / 6)))
            hills = 14 * (vnoise(x, y, 3) + 0.4) * np.clip(d / 120, 0, 1)
            return base + hills

        grass, grass2, forest, rock, sand = hexc("#7E9A6C"), hexc("#94A877"), hexc("#3F5A44"), hexc("#8E8B85"), hexc("#CBBFA5")

        def cf(X, Y, Z, N):
            n1 = vnoise(X * 2.1, Y * 2.1, 11)[..., None]
            c = grass * (1 - (n1 * 0.5 + 0.5)) + grass2 * (n1 * 0.5 + 0.5)
            fm = np.clip((vnoise(X * 1.3, Y * 1.3, 5)[..., None] - 0.15) * 3, 0, 1) * np.clip((Z[..., None] - 14) / 10, 0, 1)
            # parcelas (minifundio)
            u = X * 0.94 + Y * 0.34
            v = -X * 0.34 + Y * 0.94
            cell = (np.floor(u / 24) * 7.13 + np.floor(v / 15) * 3.71)
            hsh = (np.sin(cell * 12.9898) * 43758.5453) % 1.0
            tones = np.array([[0.62, 0.68, 0.45], [0.50, 0.62, 0.42], [0.70, 0.70, 0.50], [0.45, 0.56, 0.38], [0.58, 0.66, 0.48]])
            fc = tones[(hsh * 5).astype(int) % 5]
            fz = (np.clip((40 - Z) / 10, 0, 1) * np.clip(Z / 3, 0, 1))[..., None] * 0.75
            c = c * (1 - fz) + fc * fz
            c = c * (1 - fm) + forest * fm
            slope = 1 - N[..., 2:3]
            rk = np.clip((slope - 0.18) * 4, 0, 1)
            c = c * (1 - rk) + rock * rk
            sd = np.clip(1 - Z[..., None] / 1.6, 0, 1) * (Z[..., None] > -0.5)
            c = c * (1 - sd) + sand * sd
            return c

        self.h = h
        self.terrain = Terrain(-260, 260, -220, 380, 7.0, h, cf, sun=(-0.62, -0.25, 0.62))
        m = Mesh(sun=(-0.62, -0.25, 0.62))
        self.terrain.add_to(m)
        # casas de la aldea
        self.houses = []
        stone = [hexc(c) for c in ("#B3A796", "#A89C8A", "#C2B6A2", "#9E9282")]
        roofs = [hexc(c) for c in ("#5A5E63", "#8C5A45", "#6A6B6B", "#7D5040")]
        spots = [(35, 40), (52, 52), (28, 66), (62, 30), (46, 78), (70, 62), (18, 46), (82, 44), (58, 92)]
        for i, (hx, hy) in enumerate(spots):
            hx += rs.uniform(-3, 3)
            hy += rs.uniform(-3, 3)
            w, d = rs.uniform(7, 11), rs.uniform(5, 7)
            alx = rs.rand() < 0.5
            if not alx:
                w, d = d, w
            zb = min(h(np.array(hx - w / 2), np.array(hy - d / 2)), h(np.array(hx + w / 2), np.array(hy + d / 2))) - 0.8
            zb = float(zb)
            hw = rs.uniform(3.6, 5.2)
            o = m.gable(hx - w / 2, hy - d / 2, hx + w / 2, hy + d / 2, zb, zb + 0.8 + hw, zb + 0.8 + hw + rs.uniform(2.2, 3.0),
                        stone[i % 4], roofs[i % 4], along_x=alx)
            self.houses.append((o, (hx, hy, zb + hw)))
        # árboles
        for k in range(150):
            tx, ty = rs.uniform(-30, 240), rs.uniform(-200, 360)
            if (tx - 50) ** 2 + (ty - 60) ** 2 < 55 ** 2:
                continue
            zz = float(h(np.array(tx), np.array(ty)))
            if zz < 2:
                continue
            if rs.rand() < 0.5:
                m.cone((tx, ty, zz - 0.5), rs.uniform(2.2, 3.2), rs.uniform(9, 13), hexc("#3E5A42") * rs.uniform(0.85, 1.1))
            else:
                m.blob((tx, ty, zz + 3.5), rs.uniform(3, 4.5), hexc("#567150") * rs.uniform(0.85, 1.1), rz=3, seed=k)
        self.mesh = m.finalize()
        self.village = np.array([50.0, 60.0])
        self.sea_point = np.array([-150.0, 70.0, 0.0])

    def camera(self, t, vp=(0, 0, W, H), zoom=0.0, orbit=0.0):
        """Vista aérea oblicua hacia la aldea con el mar a la izquierda."""
        a = math.radians(-112 + orbit + t * 1.6)
        dist = 280 - zoom * 110 - t * 3.5
        cx, cy = 40.0, 58.0
        pos = (cx + dist * math.cos(a), cy + dist * math.sin(a), 105 + dist * 0.4)
        return Camera(pos, (cx - 24, cy + 6, 0.0), fov=54, vp=vp)

    def render(self, canvas, cam, ss, t, house_glow=None):
        sky_paint(canvas, cam, ss, top="#2A3446", horizon="#D7C4AC")
        C = water_colors(self.mesh, self.terrain, t, hexc("#26465A"), hexc("#4E8A92"), hexc("#E8E4DA"))
        dt = np.linalg.norm(cam.pos - cam.target)
        render_mesh(canvas, self.mesh, cam, ss, fog=(hexc("#CDBDA6"), dt * 1.0, dt * 3.2, 0.7), colors=C)


class ABarca:
    """Aldea de 12 casas en la ladera del valle del Miño."""

    def __init__(self, seed=11):
        rs = np.random.RandomState(seed)

        def h(x, y):
            rx = x - (15 * np.sin(y / 90.0))
            d = np.abs(rx) - 55
            side = np.where(rx < 0, 1.0, 1.15)
            base = np.where(d < 0, d * 0.12, (d * 0.42 * side) * (1 - np.exp(-np.maximum(d, 0) / 200)) + 4 * (1 - np.exp(-np.maximum(d, 0) / 5)))
            return base + 10 * vnoise(x, y, 21) * np.clip(d / 80, 0, 1)

        vine, vine2, forest, grass, rock = hexc("#8FA06A"), hexc("#6E7E50"), hexc("#3A5240"), hexc("#7F9867"), hexc("#8C8780")

        def cf(X, Y, Z, N):
            n1 = vnoise(X * 1.7, Y * 1.7, 4)[..., None]
            c = grass * (0.5 + 0.5 * n1) + forest * (0.5 - 0.5 * n1)
            terr = (np.sin(Z * 1.6) * 0.5 + 0.5)[..., None]
            vm = np.clip((n1 + 0.2) * 3, 0, 1) * np.clip((Z[..., None] - 6) / 6, 0, 1) * np.clip((90 - Z[..., None]) / 20, 0, 1)
            vc = vine * terr + vine2 * (1 - terr)
            c = c * (1 - vm) + vc * vm
            hi = np.clip((Z[..., None] - 110) / 40, 0, 1)
            c = c * (1 - hi) + forest * hi
            slope = 1 - N[..., 2:3]
            rk = np.clip((slope - 0.35) * 3, 0, 1)
            return c * (1 - rk) + rock * rk

        self.h = h
        self.terrain = Terrain(-520, 520, -480, 560, 10.0, h, cf, sun=(-0.55, -0.35, 0.68))
        m = Mesh(sun=(-0.55, -0.35, 0.68))
        self.terrain.add_to(m)
        self.houses = []
        stone = [hexc(c) for c in ("#B6AA98", "#A99D8B", "#C0B4A0", "#9C907F")]
        roofs = [hexc(c) for c in ("#8A5946", "#5C6066", "#7A4C3C", "#6B6D6E")]
        cx, cy = -88.0, 30.0
        spots = [(-10, -26), (6, -18), (-22, -8), (12, -2), (-6, 2), (-26, 14), (4, 18), (20, 12), (-14, 30), (8, 36), (-30, 36), (24, 30)]
        for i, (dx, dy) in enumerate(spots):
            hx, hy = cx + dx * 1.15 + rs.uniform(-1.5, 1.5), cy + dy * 1.25 + rs.uniform(-1.5, 1.5)
            w, d = rs.uniform(7, 10), rs.uniform(5, 6.5)
            alx = rs.rand() < 0.6
            if not alx:
                w, d = d, w
            zb = float(min(h(np.array(hx - w / 2), np.array(hy)), h(np.array(hx + w / 2), np.array(hy)))) - 1.0
            hw = rs.uniform(3.8, 5.0)
            o = m.gable(hx - w / 2, hy - d / 2, hx + w / 2, hy + d / 2, zb, zb + 1 + hw, zb + 1 + hw + 2.6, stone[i % 4], roofs[i % 4], along_x=alx)
            self.houses.append((o, (hx, hy, zb + hw + 2.5)))
        # orden de encendido: de abajo arriba
        self.houses.sort(key=lambda t: t[1][1])
        for k in range(220):
            tx, ty = rs.uniform(-400, 400), rs.uniform(-360, 440)
            zz = float(h(np.array(tx), np.array(ty)))
            if zz < 3 or (tx - cx) ** 2 + (ty - cy) ** 2 < 55 ** 2:
                continue
            if rs.rand() < 0.45:
                m.cone((tx, ty, zz - 0.5), rs.uniform(2.5, 3.5), rs.uniform(10, 14), hexc("#3A5540") * rs.uniform(0.85, 1.1))
            else:
                m.blob((tx, ty, zz + 3.5), rs.uniform(3.5, 5), hexc("#566F4D") * rs.uniform(0.85, 1.1), rz=3.2, seed=k)
        self.mesh = m.finalize()
        self.center = np.array([cx, cy])

    def camera(self, t, vp=(0, 0, W, H), descend=0.0):
        """Bajada desde el cielo. descend: 0 (muy alto) -> 1 (cerca de la aldea)."""
        e = descend
        cx, cy = self.center
        alt = 560 * (1 - e) + 135 * e
        back = 120 * (1 - e) + 200 * e
        ang = math.radians(-70 + 20 * e + t * 0.8)
        pos = (cx + 30 + back * math.cos(ang), cy + back * math.sin(ang), alt)
        return Camera(pos, (cx - 4, cy + 6, 6), fov=55, vp=vp)

    def render(self, canvas, cam, ss, t, colors=None):
        sky_paint(canvas, cam, ss, top="#28324A", horizon="#D5C2AA")
        C = water_colors(self.mesh, self.terrain, t * 0.6, hexc("#2C4C58"), hexc("#4F7F86"), hexc("#D9D7CC")) if colors is None else colors
        dt = np.linalg.norm(cam.pos - cam.target)
        render_mesh(canvas, self.mesh, cam, ss, fog=(hexc("#CBBBA4"), dt * 1.0, dt * 3.2, 0.7), colors=C)

    def colors_with_glow(self, t, lit):
        """lit: lista de intensidades 0..1 por casa (en orden de encendido)."""
        C = water_colors(self.mesh, self.terrain, t * 0.6, hexc("#2C4C58"), hexc("#4F7F86"), hexc("#D9D7CC"))
        g = hexc("#8FC09C")
        for (o, _), a in zip(self.houses, lit):
            if a <= 0:
                continue
            msk = self.mesh.obj == o
            C[msk, :, :3] = C[msk, :, :3] * (1 - 0.5 * a) + C[msk, :, :3] * g * 1.25 * 0.5 * a + g * 0.12 * a
        return C


# --------------------------------------------------------------------------------------
def _submesh(m: Mesh, mask):
    s = Mesh()
    for k in ("T", "C", "N", "PN", "obj", "intra", "layer", "cull", "cen"):
        setattr(s, k, getattr(m, k)[mask])
    s.obj_cen, s.obj_rad, s.obj_count = m.obj_cen, m.obj_rad, m.obj_count
    return s


def _path(pts):
    p = skia.Path()
    p.moveTo(float(pts[0][0]), float(pts[0][1]))
    for q in pts[1:]:
        p.lineTo(float(q[0]), float(q[1]))
    p.close()
    return p


def convex_hull(pts):
    pts = sorted(map(tuple, np.asarray(pts)))
    if len(pts) <= 2:
        return np.array(pts)

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return np.array(lo[:-1] + up[:-1])


def sky_paint(canvas, cam: Camera, ss, top="#273041", horizon="#D9C3A8"):
    """Cielo en degradado con el horizonte en su sitio según la cámara."""
    vx, vy, vw, vh = cam.vp
    far = cam.pos + np.array([cam.f[0], cam.f[1], 0.0]) / max(1e-6, np.hypot(cam.f[0], cam.f[1])) * 5000
    far[2] = 0
    (hx, hy), z = cam.project(far)
    hy = hy if z > 0 else vy - 10
    t_, h_ = hexc(top), hexc(horizon)
    cols = [skia.Color4f(*t_, 1).toColor(), skia.Color4f(*(t_ * 0.4 + h_ * 0.6), 1).toColor(), skia.Color4f(*h_, 1).toColor()]
    shader = skia.GradientShader.MakeLinear([skia.Point(0, (hy - 900) * ss), skia.Point(0, hy * ss)], cols, [0.0, 0.78, 1.0])
    p = skia.Paint(Shader=shader)
    canvas.drawRect(skia.Rect.MakeXYWH(vx * ss, vy * ss, vw * ss, vh * ss), p)
