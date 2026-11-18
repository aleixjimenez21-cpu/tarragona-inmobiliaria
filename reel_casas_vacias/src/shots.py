"""Los 8 planos de LA MAQUETA. Cada función monta la escena completa con su
animación en tiempo absoluto (segundos del reel), a partir de output/timings.json.
"""
import bpy, bmesh, json, math, os, random, re, unicodedata
import numpy as np
from mathutils import Vector
import maqueta as M
from maqueta import key, TOP, DATA

ROOT = M.ROOT
TM = json.load(open(os.path.join(ROOT, 'output', 'timings.json')))
SHOTS = {s['name']: s for s in TM['shots']}
W_, H_ = 1080, 1920


def _n(w):
    w = unicodedata.normalize('NFD', w.lower())
    w = ''.join(c for c in w if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9]', '', w)


def _word(word, n, k_):
    k = 0
    for w in TM['words']:
        if _n(w['w']) == _n(word):
            k += 1
            if k == n:
                return w[k_]
    raise KeyError(word)


def W(word, n=1):
    return _word(word, n, 's')


def WE(word, n=1):
    return _word(word, n, 'e')

# ======================================================== geometría de cámara

def cam_basis(loc, tgt):
    f = (Vector(tgt) - Vector(loc)).normalized()
    r = f.cross(Vector((0, 0, 1)))
    if r.length < 1e-6:
        r = Vector((1, 0, 0))
    r.normalize()
    u = r.cross(f)
    return f, r, u


def screen_ray(loc, tgt, lens, px, py):
    f, r, u = cam_basis(loc, tgt)
    tv = 18.0 / lens
    th = tv * W_ / H_
    sx = (px / W_ - .5) * 2
    sy = (.5 - py / H_) * 2
    return (f + r * sx * th + u * sy * tv).normalized()


def board_hit(loc, tgt, lens, px, py, z=TOP):
    d = screen_ray(loc, tgt, lens, px, py)
    t = (z - loc[2]) / d.z
    return Vector(loc) + d * t


def project(pose, Q):
    loc, tgt, lens = pose
    f, r, u = cam_basis(loc, tgt)
    v = Vector(Q) - Vector(loc)
    z = v.dot(f)
    if z <= 1e-6:
        return None
    tv = 18.0 / lens; th = tv * W_ / H_
    sx = v.dot(r) / z / th; sy = v.dot(u) / z / tv
    return ((sx / 2 + .5) * W_, (.5 - sy / 2) * H_, z)


def world_width_at(loc, tgt, lens, P, px_width):
    f, r, u = cam_basis(loc, tgt)
    depth = (Vector(P) - Vector(loc)).dot(f)
    th = 18.0 / lens * W_ / H_
    return px_width / W_ * 2 * depth * th


def yaw_facing(P, loc):
    d = Vector(loc) - Vector(P)
    return math.atan2(d.x, -d.y)


def pose_eval(sc, cam, tgt, t):
    sc.frame_set(cut_frame(t))
    return (cam.matrix_world.translation.copy(), tgt.matrix_world.translation.copy(), cam.data.lens)

# ======================================================== texto de cartón

CARDS = []  # (Card, pose) para retirar casitas que tapan


class Card:
    """Palabra de cartón: un empty con letras hijas."""

    def __init__(self, txt, mat, P, yaw, height, standing=True, name=None, track=0.05, extrude=0.07):
        self.txt = txt
        self.letters, self.w, self.h = M.letters(txt, mat, track=track, extrude=extrude)
        self.scale = height / self.h
        self.root = bpy.data.objects.new(name or ('card_' + txt), None)
        bpy.context.scene.collection.objects.link(self.root)
        self.root.location = P
        self.root.rotation_euler = (0, 0, yaw)
        self.root.scale = (self.scale,) * 3
        self.standing = standing
        self.yaw = yaw
        for ob, x, w in self.letters:
            ob.parent = self.root
            ob.location = (x, 0, 0)
            ob.rotation_euler = (math.pi / 2 if standing else 0, 0, 0)
        self.width_world = self.w * self.scale
        self.height_world = self.h * self.scale

    def corners(self):
        P = Vector(self.root.location)
        R = Vector((math.cos(self.yaw), math.sin(self.yaw), 0))
        U = Vector((0, 0, 1)) if self.standing else Vector((-math.sin(self.yaw), math.cos(self.yaw), 0))
        w, h = self.width_world / 2, self.height_world
        return [P - R * w, P + R * w, P - R * w + U * h, P + R * w + U * h, P + U * h / 2]

    def drop(self, t_land, h=None, stagger=0.05, fall=0.38, wobble=True):
        h = h if h is not None else 1.6 * self.h
        rnd = random.Random(len(self.letters))
        times = []
        for k, (ob, _, _) in enumerate(self.letters):
            tl = t_land + k * stagger
            t0 = tl - fall
            z0 = ob.location.z
            rx0 = ob.rotation_euler.x
            ob.location.z = z0 + h * rnd.uniform(.9, 1.2)
            key(ob, 'location', t0, ob.location.copy(), 'QUAD', 'EASE_IN')
            ob.location.z = z0
            key(ob, 'location', tl, ob.location.copy(), 'QUAD', 'EASE_OUT')
            ob.location.z = z0 + 0.05 * self.h
            key(ob, 'location', tl + 0.07, ob.location.copy(), 'QUAD', 'EASE_IN')
            ob.location.z = z0
            key(ob, 'location', tl + 0.14, ob.location.copy(), 'BEZIER')
            if wobble:
                ry = rnd.uniform(-.25, .25)
                ob.rotation_euler = (rx0 + rnd.uniform(-.15, .15), ry, 0)
                key(ob, 'rotation_euler', t0, ob.rotation_euler.copy())
                ob.rotation_euler = (rx0, -ry * .15, 0)
                key(ob, 'rotation_euler', tl, ob.rotation_euler.copy())
                ob.rotation_euler = (rx0, 0, 0)
                key(ob, 'rotation_euler', tl + 0.2, ob.rotation_euler.copy())
            hide_before(ob, t0)
            times.append(tl)
        return times

    def rise(self, t0, stagger=0.06, dur=0.32):
        times = []
        for k, (ob, _, _) in enumerate(self.letters):
            a = t0 + k * stagger
            for t, deg in ((a, 0), (a + dur, 98), (a + dur + .1, 88), (a + dur + .22, 90)):
                ob.rotation_euler = (math.radians(deg), 0, 0)
                key(ob, 'rotation_euler', t, ob.rotation_euler.copy(), 'QUAD' if deg == 0 else 'BEZIER',
                    'EASE_IN' if deg == 0 else 'AUTO')
            times.append(a + dur)
        return times

    def pop(self, t0, stagger=0.04, dur=0.22):
        times = []
        for k, (ob, _, _) in enumerate(self.letters):
            a = t0 + k * stagger
            for t, s in ((a, .001), (a + dur * .7, 1.1), (a + dur, 1.0)):
                ob.scale = (s,) * 3
                key(ob, 'scale', t, ob.scale.copy())
            hide_before(ob, a)
            times.append(a)
        return times


def hide_before(ob, t):
    ob.hide_render = True
    ob.keyframe_insert('hide_render', frame=max(1, 1 + t * 30 - 1))
    ob.hide_render = False
    ob.keyframe_insert('hide_render', frame=1 + t * 30)
    for fc in M.iter_fcurves(ob.animation_data.action):
        if fc.data_path == 'hide_render':
            for kp in fc.keyframe_points:
                kp.interpolation = 'CONSTANT'


def card_on_screen(txt, mat, pose, px, py_base, px_width, standing=True, lift=0.0, **kw):
    loc, tgt, lens = pose
    P = board_hit(loc, tgt, lens, px, py_base, z=TOP + lift)
    tmp, w, h = M.letters(txt, None)
    for ob, _, _ in tmp:
        bpy.data.objects.remove(ob)
    ww = world_width_at(loc, tgt, lens, P, px_width)
    height = ww / w * h
    if standing:
        yaw = yaw_facing(P, loc)
    else:
        f, r, u = cam_basis(loc, tgt)
        yaw = math.atan2(r.y, r.x)
    c = Card(txt, mat, P, yaw, height, standing=standing, **kw)
    CARDS.append((c, pose))
    return c


def card_at(txt, mat, P, pose, px_width, **kw):
    loc, tgt, lens = pose
    tmp, w, h = M.letters(txt, None)
    for ob, _, _ in tmp:
        bpy.data.objects.remove(ob)
    ww = world_width_at(loc, tgt, lens, P, px_width)
    c = Card(txt, mat, P, yaw_facing(P, loc), ww / w * h, **kw)
    CARDS.append((c, pose))
    return c

# ======================================================== escena común

STREET = DATA['street']
SP = Vector((STREET['x'], STREET['y'], TOP))
SU = Vector((math.cos(STREET['th']), math.sin(STREET['th']), 0))
SV = Vector((-SU.y, SU.x, 0))


def wave_tw(i, h):
    d = math.hypot(h[0] - SP.x, h[1] - SP.y)
    r = random.Random(i).random()
    return W('España') + 0.1 + d * 0.0062 + r * 0.12


_PC = None


def parcel_center():
    global _PC
    if _PC is None:
        ps = [p for p in DATA['parcels'] if p[3] == 28]
        P = np.array([(p[0], p[1]) for p in ps])
        best, bc = 0, None
        for c in P:
            n = (np.linalg.norm(P - c, axis=1) < 14).sum()
            if n > best:
                best, bc = n, c
        _PC = Vector((bc[0], bc[1], TOP))
    return _PC


def parcel_t0(p, i):
    c = parcel_center()
    d = math.hypot(p[0] - c.x, p[1] - c.y)
    r = random.Random(1000 + i).random()
    return W('faltan') - 0.2 + d * 0.0045 + r * 0.45 + (0.0 if d < 30 else 0.3)


def build_parcels(mat, width, select=None, t0_fn=parcel_t0, rect=(1.55, 1.25), name='parcelas'):
    rnd = random.Random(5)
    lines = []
    for i, p in enumerate(DATA['parcels']):
        segs = M.sketch_rect(p[0], p[1], rect[0], rect[1], p[2], rnd, over=0.28)
        if select and not select(i, p):
            continue
        t0 = t0_fn(p, i)
        for k, pts in enumerate(segs):
            lines.append(dict(pts=pts, t0=t0 + k * 0.07, dur=0.11, width=width))
    return M.stroke_mesh(name, lines, mat, width)


def common(sc, parcel_width=0.12, sun=(150, 22, 3.2)):
    pv = M.build_world()
    hm = M.mat_houses()
    pm = M.mat_pencil()
    pc = build_parcels(pm, parcel_width)
    s = add_sun_from(sc, *sun)
    CARDS.clear()
    return dict(prov=pv, hmat=hm, pmat=pm, parcels=pc, sun=s)


def occluders():
    """Índices de casitas que taparían algún rótulo de cartón."""
    ex = set()
    H = DATA['houses']
    for card, pose in CARDS:
        pts = [project(pose, q) for q in card.corners()]
        if any(p is None for p in pts):
            continue
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        x0, x1, y0, y1 = min(xs) - 30, max(xs) + 30, min(ys) - 40, max(ys) + 30
        dmax = max(p[2] for p in pts) + 3
        P = Vector(card.root.location)
        rr = card.width_world / 2 + 2.5
        for i, h in enumerate(H):
            if abs(h[0] - P.x) > 400 or abs(h[1] - P.y) > 400:
                continue
            if card.standing:
                # dentro de la huella de las letras
                d = Vector((h[0] - P.x, h[1] - P.y, 0))
                R = Vector((math.cos(card.yaw), math.sin(card.yaw), 0))
                if abs(d.dot(R)) < rr and abs(d.cross(R).z) < 2.0:
                    ex.add(i); continue
            for z in (TOP + 0.2, TOP + 2.2):
                q = project(pose, (h[0], h[1], z))
                if q and x0 < q[0] < x1 and y0 < q[1] < y1 and q[2] < dmax:
                    ex.add(i); break
    return ex


def houses_mesh(c, select=None, name='casas', tw_fn=wave_tw, rec_fn=None):
    ex = c.setdefault('exclude', occluders())
    sel = (lambda i, h: i not in ex and (select is None or select(i, h)))
    return M.build_houses(c['hmat'], select=sel, tw_fn=tw_fn, name=name, rec_fn=rec_fn,
                          house_scale=c.get('hscale', 1.0))


def add_sun_from(sc, phi, el, energy, angle=3.5):
    """Sol que llega DESDE el azimut phi (grados; 0=este, 90=norte)."""
    return M.add_sun(sc, az=phi + 90, el=el, energy=energy, angle=angle)


def cam_keys(cam, tgt, poses):
    for t, l, g, lens in poses:
        key(cam, 'location', t, Vector(l))
        key(tgt, 'location', t, Vector(g))
        cam.data.lens = lens
        cam.data.keyframe_insert('lens', frame=1 + t * 30)
    M.set_handles(cam, 'AUTO_CLAMPED'); M.set_handles(tgt, 'AUTO_CLAMPED')


def focus_empty(sc):
    f = bpy.data.objects.new('focus', None)
    sc.collection.objects.link(f)
    f['ts'] = 1.0
    return f


def cut_frame(t):
    return int(round(t * 30)) + 1


def set_dim(provs, t, value, except_=(), dur=0.5):
    for pid, ob in provs.items():
        if pid in except_:
            continue
        key(ob, '["dim"]', t, 0.0)
        key(ob, '["dim"]', t + dur, value)


def light_energy(ob, t, e0, e1, dur=0.25):
    ob.data.energy = e0
    ob.data.keyframe_insert('energy', frame=1 + t * 30)
    ob.data.energy = e1
    ob.data.keyframe_insert('energy', frame=1 + (t + dur) * 30)


def spot_for(sc, center, radius, height=None, power=3.0, name='foco', from_dir=(-.35, -.5)):
    height = height or radius * 3.2
    loc = (center[0] + from_dir[0] * height, center[1] + from_dir[1] * height, TOP + height)
    dist = (Vector(loc) - Vector((center[0], center[1], TOP))).length
    ang = 2 * math.degrees(math.atan(radius / dist)) * 1.25
    e = power * 4 * math.pi * dist ** 2
    return M.add_spot(sc, loc, (center[0], center[1], TOP), energy=e, size_deg=ang, blend=0.45,
                      radius=dist * 0.05, name=name), e


def fill_light(sc, loc, target, power=0.35, size_k=0.35):
    dist = (Vector(loc) - Vector(target)).length
    e = power * 4 * math.pi * dist ** 2
    return M.add_area(sc, loc, target, size=dist * size_k, energy=e, color=(1.0, 0.93, 0.85))


def overview_pose(lens=35):
    x0, y0, x1, y1 = DATA['land_bbox']
    cx = (x0 + x1) / 2 + 12; cy = (y0 + y1) / 2 - 10
    wid = (x1 - x0) * 1.06
    th = 18.0 / lens * W_ / H_
    D = wid / (2 * th)
    tilt = math.radians(16)
    return (Vector((cx, cy - D * math.sin(tilt), TOP + D * math.cos(tilt))), Vector((cx, cy, TOP)), lens)

# ======================================================== PLANOS

def shot_A(sc):
    """Hook: calle de casitas, ola de vidrio, cae 3.800.000."""
    c = common(sc, parcel_width=0.08, sun=(math.degrees(STREET['th']) + 120, 16, 3.0))
    cam, tgt = M.add_camera(sc, 50)
    fe = focus_empty(sc)
    t0, t1 = SHOTS['A_hook']['start'], SHOTS['A_hook']['end']
    L0 = SP - SU * 10.5 + SV * 2.6 + Vector((0, 0, 6.2))
    G0 = SP + SU * 3.5 + SV * 0.2 + Vector((0, 0, 0.0))
    L1 = SP - SU * 11.5 + SV * 2.0 + Vector((0, 0, 10.5))
    G1 = SP + SU * 14.0 + Vector((0, 0, 0.4))
    poses = [(t0, L0, G0, 50), (t1 + 0.15, L1, G1, 50)]
    cam_keys(cam, tgt, poses)
    land = W('cuatro') - 0.05
    pose = pose_eval(sc, cam, tgt, land + 0.45)
    card_mat = M.mat_card(M.C_WHITE)
    num = card_on_screen('3.800.000', card_mat, pose, 515, 640, 800)
    tl = num.drop(land, stagger=0.045)
    sub = card_on_screen('VACÍAS', card_mat, pose, 515, 790, 330)
    sub.pop(W('viviendas') + 0.05, stagger=0.03)
    houses_mesh(c)
    key(fe, 'location', t0, SP + SU * 1.0)
    key(fe, 'location', land - 0.3, SP + SU * 2.5)
    key(fe, 'location', land + 0.2, num.root.location.copy())
    fill_light(sc, L1 + SV * 8 + Vector((0, 0, 8)), SP, power=0.22)
    return cam, fe, (t0, t1), dict(glass=W('España') + 0.1, impacts=tl, pop=[W('viviendas') + 0.05])


def b_frame():
    P = parcel_center()
    yaw = math.radians(-58)
    D = Vector((math.cos(yaw), math.sin(yaw), 0))
    Rr = Vector((-D.y, D.x, 0))
    return P, D, Rr


def shot_B(sc):
    """Contraste: parcelas rojas a lápiz, se levanta 750.000."""
    c = common(sc, parcel_width=0.085, sun=(205, 20, 3.0))
    cam, tgt = M.add_camera(sc, 55)
    fe = focus_empty(sc)
    t0, t1 = SHOTS['B_contraste']['start'], SHOTS['B_contraste']['end']
    P, D, Rr = b_frame()
    L0 = P - D * 18 + Rr * 2.5 + Vector((0, 0, 10.5))
    L1 = P - D * 17 + Rr * -1.5 + Vector((0, 0, 10.0))
    poses = [(t0, L0, P + Rr * 1.5, 55), (t1 + 0.6, L1, P - Rr * 1.0, 55)]
    cam_keys(cam, tgt, poses)
    red = M.mat_card(M.C_RED, 'carton_rojo')
    white = M.mat_card(M.C_WHITE)
    tr = W('setecientas') - 0.1
    pose = pose_eval(sc, cam, tgt, tr + 0.6)
    num = card_on_screen('750.000', red, pose, 510, 860, 780)
    times = num.rise(tr, stagger=0.07)
    lab = card_on_screen('FALTAN', white, pose, 510, 1040, 330)
    lab.rise(W('faltan') - 0.05, stagger=0.05, dur=0.25)
    houses_mesh(c)
    key(fe, 'location', t0, P)
    key(fe, 'location', tr, num.root.location.copy())
    fill_light(sc, L1 + Vector((0, 0, 10)) - Rr * 10, P, power=0.22)
    return cam, fe, (t0, t1), dict(rise=times, pencil=(W('faltan') - 0.2, t1))


def shot_C(sc):
    """Grúa rápida a cenital de toda la maqueta. ¿CÓMO?"""
    c = common(sc, parcel_width=0.9, sun=(200, 30, 3.2))
    c['hscale'] = 1.9
    cam, tgt = M.add_camera(sc, 55)
    fe = focus_empty(sc)
    t0, t1 = SHOTS['C_pregunta']['start'], SHOTS['C_pregunta']['end']
    P, D, Rr = b_frame()
    Lb = P - D * 17 + Rr * -1.6 + Vector((0, 0, 10.0))
    ov = overview_pose(35)
    t_land = W('Cómo') + 0.12
    poses = [(t0, Lb, P - Rr * 1.1, 55),
             (t0 + 0.3, Lb + Vector((0, 0, 14)) - D * 6, P + D * 4, 52),
             (t_land - 0.1, ov[0] + Vector((0, -50, -600)), ov[1] + Vector((0, 10, 0)), 38),
             (t_land + 0.6, ov[0], ov[1], 35),
             (t1 + 0.1, ov[0] + Vector((0, 0, 70)), ov[1] + Vector((0, 4, 0)), 35)]
    cam_keys(cam, tgt, poses)
    white = M.mat_card(M.C_WHITE)
    pose = pose_eval(sc, cam, tgt, t_land + 0.7)
    q = card_on_screen('¿CÓMO?', white, pose, 510, 1010, 600, standing=False, extrude=0.05)
    q.root.location.z = TOP + 0.4
    tl = q.drop(t_land, h=90 / q.scale, stagger=0.035, fall=0.32, wobble=False)
    houses_mesh(c)
    key(fe, 'location', t0, P)
    key(fe, 'location', t_land, ov[1])
    fe['ts'] = 0.7
    return cam, fe, (t0, t1), dict(impacts=tl, whoosh=t0 + 0.05)


def shot_D(sc):
    """Picado sobre Galicia. Ourense iluminada, cota roja, +40 %."""
    c = common(sc, parcel_width=0.5, sun=(210, 26, 3.2))
    pv = c['prov']
    c['hscale'] = 1.9
    cam, tgt = M.add_camera(sc, 35)
    fe = focus_empty(sc)
    t0, t1 = SHOTS['D_ourense']['start'], SHOTS['D_ourense']['end']
    O = DATA['provinces']['32']
    oc = Vector((O['c'][0], O['c'][1], TOP))
    ov = overview_pose(35)
    look = Vector((0.45, 0.89, 0)).normalized()
    L_end = oc - look * 150 + Vector((0, 0, 135))
    G_end = oc + look * 25
    poses = [(t0, ov[0] + Vector((0, 0, 70)), ov[1] + Vector((0, 4, 0)), 35),
             (t0 + 1.3, L_end + Vector((-10, -30, 90)), G_end + Vector((0, 8, 0)), 40),
             (W('cuarenta') - 0.2, L_end, G_end, 45),
             (t1 + 0.1, L_end - look * 6 + Vector((8, 0, -8)), G_end, 46)]
    cam_keys(cam, tgt, poses)
    t_on = W('Ourense') - 0.05
    set_dim(pv, t_on - 0.2, 0.72, except_=('32',), dur=0.6)
    sp, e = spot_for(sc, oc, 60, power=6.0, name='foco_ourense')
    light_energy(sp, t0, 0, 0, 0.01)
    light_energy(sp, t_on - 0.1, 0, e, 0.25)
    light_energy(c['sun'], t_on - 0.2, 3.2, 1.0, 0.6)
    ob = pv['32']
    key(ob, 'location', t_on - 0.1, Vector((0, 0, 0)))
    key(ob, 'location', t_on + 0.5, Vector((0, 0, 1.6)))
    from shapely.geometry import Polygon
    poly = max(O['polys'], key=lambda p: len(p['ext']))
    pg = Polygon(poly['ext']).buffer(2.2).simplify(0.4)
    pts = list(pg.exterior.coords)
    k0 = int(np.argmax([p[1] for p in pts]))
    pts = pts[k0:] + pts[1:k0 + 1]
    tc = WE('Ourense') + 0.05
    stroke = M.stroke_mesh('cota', [dict(pts=pts, t0=tc, dur=1.0, width=0.9)], M.mat_pencil('lapiz_cota'),
                           z=TOP + 0.04)
    stroke.parent = ob
    rim = c['hmat'].node_tree.nodes['rim'].outputs[0]
    for t, v in ((t0, 1.6), (W('viviendas', 3) - 0.2, 1.6), (W('vacías', 2), 4.5)):
        rim.default_value = v
        rim.keyframe_insert('default_value', frame=1 + t * 30)
    white = M.mat_card(M.C_WHITE)
    pose = pose_eval(sc, cam, tgt, W('cuarenta') + 0.4)
    card = card_on_screen('+40 %', white, pose, 520, 700, 560)
    tl = card.drop(W('cuarenta') - 0.02, stagger=0.05)
    houses_mesh(c, select=lambda i, h: h[4] != 32, name='casas_resto')
    ho = houses_mesh(c, select=lambda i, h: h[4] == 32, name='casas_ourense')
    ho.parent = ob
    key(fe, 'location', t0, ov[1])
    key(fe, 'location', t0 + 1.3, oc)
    key(fe, 'location', W('cuarenta'), card.root.location.copy() * .5 + oc * .5)
    return cam, fe, (t0, t1), dict(impacts=tl, spot=t_on, pencil=(tc, tc + 1.0))


SIX = [('28', 'Madrid'), ('08', 'Barcelona'), ('46', 'Valencia'), ('03', 'Alicante'), ('30', 'Murcia'), ('29', 'Málaga')]


def shot_E(sc):
    """Travelling por las 6 provincias del déficit."""
    c = common(sc, parcel_width=0.55, sun=(220, 24, 3.0))
    pv = c['prov']
    c['hscale'] = 1.9
    cam, tgt = M.add_camera(sc, 40)
    fe = focus_empty(sc)
    t0, t1 = SHOTS['E_provincias']['start'], SHOTS['E_provincias']['end']
    pts = [Vector((DATA['cities'][n][0], DATA['cities'][n][1], TOP)) for _, n in SIX]
    look = Vector((0.15, 1.0, 0)).normalized()
    side = Vector((look.y, -look.x, 0))
    tt = np.linspace(W('seis') - 0.05, W('mitad') - 0.15, 6)

    def P(g, t, back=170, alt=150):
        return (t, g - look * back + Vector((0, 0, alt)), g, 40)
    mb = (pts[0] + pts[1]) / 2
    ov = overview_pose(35)
    ovE = (ov[0] + Vector((0, 240, 0)), ov[1] + Vector((0, 240, 0)), 35)
    poses = [P(pts[0] - look * 30, t0, 200, 170),
             P(pts[0], tt[0] + 0.15, 210, 190),
             P(mb + Vector((0, 20, 0)), tt[1] + 0.2, 380, 340),
             P(pts[2], tt[2] + 0.2, 240, 210),
             P((pts[3] + pts[4]) / 2, tt[3] + 0.3, 230, 200),
             P((pts[4] + pts[5]) / 2 + Vector((30, 0, 0)), tt[5] + 0.15, 300, 260),
             (W('mitad') - 0.1, ovE[0], ovE[1], 35),
             (t1 + 0.1, ovE[0] + Vector((0, -20, 60)), ovE[1] + Vector((0, 4, 0)), 35)]
    cam_keys(cam, tgt, poses)
    set_dim(pv, t0 + 0.1, 0.42, except_=tuple(p for p, _ in SIX), dur=0.6)
    light_energy(c['sun'], t0 + 0.1, 3.0, 1.6, 0.6)
    white = M.mat_card(M.C_WHITE)
    red = M.mat_card(M.C_RED, 'carton_rojo')
    impacts = []
    for k, (pid, name) in enumerate(SIX):
        pr = DATA['provinces'][pid]
        bb = pr['bbox']
        r = max(bb[2] - bb[0], bb[3] - bb[1]) / 2
        cc = pts[k]
        sp, e = spot_for(sc, cc, r * 0.8 + 20, power=5.0, name='foco_' + pid)
        light_energy(sp, t0, 0, 0, 0.01)
        light_energy(sp, tt[k], 0, e, 0.12)
        pose = pose_eval(sc, cam, tgt, tt[k] + 0.3)
        Pn = cc + side * (-(r * 0.2 + 25)) + look * 8
        Pn.z = TOP
        card = Card(str(k + 1), red, Pn, yaw_facing(Pn, pose[0]), 34.0)
        CARDS.append((card, pose))
        impacts += card.drop(tt[k] + 0.06, stagger=0, fall=0.3)
    pose = pose_eval(sc, cam, tgt, W('déficit') + 0.3)
    a = card_on_screen('+50 %', red, pose, 510, 545, 520, standing=False, extrude=0.05, lift=0.3 - TOP)
    a.root.location.z = TOP * 0 + 0.3
    ta = a.drop(W('mitad') + 0.05, h=80 / a.scale, stagger=0.04, fall=0.3, wobble=False)
    b = card_on_screen('DEL DÉFICIT', white, pose, 510, 690, 540, standing=False, extrude=0.05, lift=0.3 - TOP)
    b.root.location.z = 0.3
    b.drop(W('déficit') - 0.1, h=80 / b.scale, stagger=0.025, fall=0.28, wobble=False)
    houses_mesh(c)
    key(fe, 'location', t0, pts[0])
    for k in range(6):
        key(fe, 'location', tt[k], pts[k])
    key(fe, 'location', W('mitad') + 0.1, a.root.location.copy())
    return cam, fe, (t0, t1), dict(impacts=impacts + ta, spots=list(tt))


def shot_F(sc):
    """Pueblos del interior casi vacíos (Zamora)."""
    c = common(sc, parcel_width=0.08, sun=(222, 15, 3.0))
    cam, tgt = M.add_camera(sc, 55)
    fe = focus_empty(sc)
    t0, t1 = SHOTS['F_pueblos']['start'], SHOTS['F_pueblos']['end']
    hv = {v['name']: v for v in DATA['hero_villages']}
    A = Vector((hv['Muelas del Pan']['x'], hv['Muelas del Pan']['y'], TOP))
    look = Vector((0.2, 1.0, 0)).normalized()
    side = Vector((look.y, -look.x, 0))
    poses = [(t0, A - look * 17 + side * 5 + Vector((0, 0, 4.2)), A + Vector((0, 0, .6)), 55),
             (W('mitad', 2) + 0.4, A - look * 15 - side * 1 + Vector((0, 0, 5.4)), A + look * 3 + Vector((0, 0, 1.0)), 55),
             (t1 + 0.1, A - look * 14 - side * 6 + Vector((0, 0, 6.2)), A + look * 4 - side * 2 + Vector((0, 0, 1.0)), 55)]
    cam_keys(cam, tgt, poses)
    white = M.mat_card(M.C_WHITE)
    pose = pose_eval(sc, cam, tgt, W('mitad', 2) + 0.6)
    num = card_on_screen('45 %', white, pose, 520, 700, 430)
    tl = num.drop(W('mitad', 2) - 0.02, stagger=0.06)
    pose2 = pose_eval(sc, cam, tgt, W('menos') + 0.5)
    l1 = card_on_screen('EN PUEBLOS DE', white, pose2, 510, 860, 500, extrude=0.05)
    l1.pop(W('municipios'), stagger=0.03)
    l2 = card_on_screen('MENOS DE 10.000 HAB.', white, pose2, 510, 975, 620, extrude=0.05)
    l2.pop(W('menos'), stagger=0.025)
    houses_mesh(c)
    key(fe, 'location', t0, A)
    key(fe, 'location', W('mitad', 2), num.root.location.copy() * 0.6 + A * 0.4)
    fill_light(sc, A - look * 10 + side * 14 + Vector((0, 0, 8)), A, power=0.2)
    return cam, fe, (t0, t1), dict(impacts=tl, pops=[W('municipios'), W('menos')])


def shot_G(sc):
    """Síntesis cenital con time-lapse de luz y líneas rojas que no llegan."""
    c = common(sc, parcel_width=1.1, sun=(160, 30, 3.0))
    c['hscale'] = 1.9
    cam, tgt = M.add_camera(sc, 35)
    fe = focus_empty(sc)
    t0, t1 = SHOTS['G_sintesis']['start'], SHOTS['G_sintesis']['end']
    ov = overview_pose(35)
    poses = [(t0, ov[0] + Vector((0, 0, 40)), ov[1], 35),
             (t1 + 0.1, ov[0] - Vector((0, 0, 40)), ov[1] + Vector((0, 3, 0)), 35)]
    cam_keys(cam, tgt, poses)
    s = c['sun']
    for t, phi, el in ((t0, 120, 20), (t0 + 2.5, 200, 34), (t1, 290, 18)):
        s.rotation_euler = (math.radians(90 - el), 0, math.radians(phi + 90))
        key(s, 'rotation_euler', t, s.rotation_euler.copy())
    rim = c['hmat'].node_tree.nodes['rim'].outputs[0]
    rim.default_value = 5.0
    srcs = [(-354, 259), (-300, 300), (-190, 190), (-90, 230), (-130, 30), (-250, -60), (90, 240), (40, -60),
            (-40, 150), (150, 120)]
    dsts = ['Madrid', 'Barcelona', 'Valencia', 'Málaga', 'Alicante', 'Murcia', 'Sevilla', 'Palma']
    rnd = random.Random(4)
    lines = []
    tl0 = W('pero') - 0.3
    for k, s0 in enumerate(srcs):
        dn = dsts[k % len(dsts)] if k < 8 else dsts[(k * 3) % len(dsts)]
        d = DATA['cities'][dn]
        a = np.array(s0, float); b = np.array(d[:2], float)
        m = (a + b) / 2 + np.array([-(b - a)[1], (b - a)[0]]) * rnd.uniform(-.12, .12)
        pts = []
        for i in range(25):
            u = i / 24
            p = (1 - u) ** 2 * a + 2 * (1 - u) * u * m + u * u * b
            p += np.array([rnd.uniform(-.6, .6), rnd.uniform(-.6, .6)])
            pts.append(tuple(p))
        lines.append(dict(pts=pts, t0=tl0 + k * 0.12, dur=1.3, cut=rnd.uniform(.42, .62), width=3.6))
    M.stroke_mesh('lineas', lines, M.mat_pencil('lapiz_lineas'), z=TOP + 2.2)
    houses_mesh(c)
    key(fe, 'location', t0, ov[1])
    fe['ts'] = 0.35
    return cam, fe, (t0, t1), dict(pencil=(tl0, tl0 + 2.5), thud=WE('falta') + 0.1)

# ------------------------------------------------------------------ plano H

def hand_shape():
    """Silueta de mano abierta (palma + dedos), en unidades ~1 = largo de la mano."""
    import math as m
    pts = []
    # contorno a mano alzada: muñeca abajo, dedos arriba
    outline = [(-.22, -.55), (-.25, -.2), (-.42, -.02), (-.55, .12), (-.52, .2), (-.4, .14), (-.25, .05),
               (-.24, .32), (-.27, .62), (-.22, .66), (-.16, .62), (-.12, .36),
               (-.10, .72), (-.04, .76), (.02, .72), (.03, .38),
               (.07, .68), (.13, .71), (.18, .66), (.15, .34),
               (.22, .54), (.28, .56), (.31, .5), (.24, .2), (.22, -.1), (.2, -.55)]
    return outline


def shot_H(sc):
    """Dilema: el cúter parte la maqueta. CONSTRUIR / RECUPERAR."""
    c = common(sc, parcel_width=0.09, sun=(215, 24, 2.0))
    pv = c['prov']
    cam, tgt = M.add_camera(sc, 45)
    fe = focus_empty(sc)
    t0, t1 = SHOTS['H_dilema']['start'], SHOTS['H_dilema']['end']
    P = parcel_center() + Vector((0, -3, 0))
    look = Vector((0.25, 1.0, 0)).normalized()
    R = Vector((look.y, -look.x, 0))  # derecha de pantalla
    Lc = P - look * 17 + Vector((0, 0, 13.5))
    t_cut = t0 + 0.35
    t_open = t_cut + 0.45
    poses = [(t0, Lc + look * 2 - Vector((0, 0, 1.5)), P + look * 2, 50),
             (t_open + 0.4, Lc, P + look * 1.5, 48),
             (t1 + 0.1, Lc - look * 3 + Vector((0, 0, 2.5)), P + look * 1.5, 46)]
    cam_keys(cam, tgt, poses)
    # elementos protagonistas
    Hs = DATA['houses']
    side = lambda x, y: (Vector((x, y, 0)) - P).dot(R)
    # parcela y casa protagonistas, colocadas a cada lado del corte
    lpv = P - R * 2.7 - look * 0.4
    lp = [lpv.x, lpv.y, math.atan2(R.y, R.x) + 0.05, 28]
    rhv = P + R * 2.7 - look * 0.4
    Hs.append([rhv.x, rhv.y, math.atan2(R.y, R.x) + math.pi / 2, 1, 28, 1, 0, -1])
    rh_i = len(Hs) - 1
    clear = [i for i, h in enumerate(Hs[:-1]) if min((Vector((h[0], h[1], TOP)) - lpv).length,
                                                     (Vector((h[0], h[1], TOP)) - rhv).length * 0.75) < 2.2]
    DATA['parcels'][:] = [p for p in DATA['parcels'] if (Vector((p[0], p[1], TOP)) - lpv).length > 2.2]
    DATA['parcels'].append(lp)
    gap = 0.9
    gL = bpy.data.objects.new('mitad_izq', None); sc.collection.objects.link(gL)
    gR = bpy.data.objects.new('mitad_der', None); sc.collection.objects.link(gR)
    for g, sgn in ((gL, -1), (gR, 1)):
        key(g, 'location', t_open - 0.45, Vector((0, 0, 0)))
        key(g, 'location', t_open, R * gap * sgn)
    # partir las provincias cercanas
    for pid, ob in list(pv.items()):
        bb = DATA['provinces'][pid]['bbox']
        if not (bb[0] - 60 < P.x < bb[2] + 60 and bb[1] - 60 < P.y < bb[3] + 60):
            continue
        me = ob.data
        for g, sgn in ((gL, -1), (gR, 1)):
            nm = me.copy()
            bm = bmesh.new(); bm.from_mesh(nm)
            geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
            res = bmesh.ops.bisect_plane(bm, geom=geom, plane_co=P, plane_no=R * sgn * -1,
                                         clear_inner=False, clear_outer=True)
            cut = [e for e in res['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
            if cut:
                try:
                    bmesh.ops.holes_fill(bm, edges=cut, sides=0)
                except Exception:
                    pass
            bm.to_mesh(nm); bm.free()
            o2 = bpy.data.objects.new(ob.name + ('_L' if sgn < 0 else '_R'), nm)
            sc.collection.objects.link(o2)
            for mo in ob.modifiers:
                m2 = o2.modifiers.new(mo.name, mo.type)
                m2.width = mo.width; m2.segments = mo.segments; m2.limit_method = mo.limit_method
                m2.angle_limit = mo.angle_limit
            o2['glow'] = 1.0; o2['dim'] = 0.0
            o2.parent = g
        bpy.data.objects.remove(ob)
    # casas: la de la derecha se recupera
    hm = c['hmat']
    hm.node_tree.nodes['recover_t'].outputs[0].default_value = W('recuperar') + 0.35

    def tw(i, h):
        return -10.0
    white = M.mat_card(M.C_WHITE)
    pose = pose_eval(sc, cam, tgt, W('recuperar') + 0.5)
    lab_l = card_on_screen('CONSTRUIR', white, pose, 290, 560, 380)
    lab_r = card_on_screen('RECUPERAR', white, pose, 750, 560, 380)
    lab_l.root.parent = gL; lab_r.root.parent = gR
    lab_l.pop(W('construir'), stagger=0.03)
    lab_r.pop(W('recuperar'), stagger=0.03)
    ex = occluders() | set(clear)
    ex.discard(rh_i)
    c['exclude'] = ex
    # vacías alrededor de la casa a recuperar
    old = [list(h) for h in Hs]
    near_r = [i for i, h in enumerate(Hs) if (Vector((h[0], h[1], TOP)) - Vector((Hs[rh_i][0], Hs[rh_i][1], TOP))).length < 4.5]
    for i in near_r:
        if random.Random(i).random() < 0.55:
            Hs[i][5] = 1
    Hs[rh_i][5] = 1
    for gsel, g in ((lambda i, h: side(h[0], h[1]) < 0, gL), (lambda i, h: side(h[0], h[1]) >= 0, gR)):
        ob = houses_mesh(c, select=gsel, name='casas_' + g.name, tw_fn=tw,
                         rec_fn=lambda i, h: 1.0 if i == rh_i else 0.0)
        ob.parent = g
    for i, h in enumerate(old):
        Hs[i][5] = h[5]
    # parcelas partidas
    c['parcels'].parent = None
    bpy.data.objects.remove(c['parcels'])
    for gsel, g in ((lambda i, p: side(p[0], p[1]) < 0, gL), (lambda i, p: side(p[0], p[1]) >= 0, gR)):
        o = build_parcels(c['pmat'], 0.09, select=gsel, t0_fn=lambda p, i: -10, name='parc_' + g.name)
        o.parent = g
    # grúa de maqueta sobre la parcela izquierda
    crane_mat = M.mat_card(M.C_WHITE, 'grua')
    base = Vector((lp[0], lp[1], TOP)) - R * 1.9 + look * 1.6
    target = Vector((lp[0], lp[1], TOP))
    parts = []
    mast_h = 6.5

    def box(name, cx, cy, cz, sx, sy, sz):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy, cz))
        o = bpy.context.active_object; o.name = name
        o.scale = (sx, sy, sz)
        o.data.materials.append(crane_mat)
        o.parent = gL
        return o
    box('mastil', base.x, base.y, TOP + mast_h / 2, 0.42, 0.42, mast_h)
    jd = (target - base); jd.z = 0; jl = jd.length + 2.5; jd.normalize()
    jib_c = base + jd * (jl / 2 - 1.8)
    jib = box('pluma', jib_c.x, jib_c.y, TOP + mast_h + 0.2, jl + 2.5, 0.32, 0.32)
    jib.rotation_euler = (0, 0, math.atan2(jd.y, jd.x))
    box('cabina', base.x, base.y, TOP + mast_h - 0.3, 0.7, 0.7, 0.6)
    cw = base - jd * 1.7
    box('contrapeso', cw.x, cw.y, TOP + mast_h - 0.05, 0.9, 0.7, 0.5)
    blk = box('bloque', target.x, target.y, TOP + 1.3, 1.4, 1.1, 2.6)
    blk.rotation_euler = (0, 0, lp[2])
    cable_top = TOP + mast_h + 0.05
    bpy.ops.mesh.primitive_cylinder_add(radius=0.035, depth=1, location=(target.x, target.y, 0))
    cab = bpy.context.active_object; cab.name = 'cable'; cab.parent = gL
    cm, N, L = M.new_mat('cable'); N['Principled BSDF'].inputs['Base Color'].default_value = (0.02, 0.02, 0.02, 1)
    cab.data.materials.append(cm)
    tb = W('construir') + 0.1
    for t, z in ((t0, TOP + 4.6), (tb, TOP + 4.6), (tb + 1.4, TOP + 1.3), (t1, TOP + 1.3)):
        blk.location.z = z
        key(blk, 'location', t, blk.location.copy())
        top = z + 1.3
        ln = cable_top - top
        cab.location = (target.x, target.y, top + ln / 2)
        cab.scale = (1, 1, ln)
        key(cab, 'location', t, cab.location.copy())
        key(cab, 'scale', t, cab.scale.copy())
    # cúter: hoja que recorre la línea de corte
    blade_m, N, L = M.new_mat('hoja')
    b = N['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.75, 0.76, 0.78, 1)
    b.inputs['Metallic'].default_value = 1.0
    b.inputs['Roughness'].default_value = 0.18
    bv = [(0, 0, 0), (2.2, 0, 0), (2.2, 0, 1.2), (0.9, 0, 1.2)]
    blade = M.mesh_obj('cuter', [(x, -0.04, z) for x, _, z in bv] + [(x, 0.04, z) for x, _, z in bv],
                       [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], blade_m)
    bpy.ops.mesh.primitive_cube_add(size=1)
    handle = bpy.context.active_object; handle.name = 'mango'
    handle.scale = (6, 0.9, 1.1); handle.location = (5.0, 0, 1.6)
    hmat, N, L = M.new_mat('mango'); N['Principled BSDF'].inputs['Base Color'].default_value = (0.02, 0.02, 0.022, 1)
    N['Principled BSDF'].inputs['Roughness'].default_value = 0.4
    handle.data.materials.append(hmat); handle.parent = blade
    blade.rotation_euler = (0, math.radians(35), math.atan2(-look.y, -look.x))
    far = P + look * 40; near = P - look * 9
    for t, p, zz in ((t_cut - 0.25, far, TOP + 6), (t_cut - 0.1, far, TOP - 0.6),
                     (t_cut + 0.35, near, TOP - 0.6), (t_cut + 0.5, near - look * 6, TOP + 8)):
        blade.location = (p.x, p.y, zz)
        key(blade, 'location', t, blade.location.copy())
    hide_before(blade, t_cut - 0.26)
    blade.hide_render = True
    blade.keyframe_insert('hide_render', frame=cut_frame(t_cut + 0.55))
    # sombra de manos sobre la casa a recuperar
    rh = Hs[rh_i]
    hpos = Vector((rh[0], rh[1], TOP))
    outline = hand_shape()
    hand = M.mesh_obj('mano', [(x * 3.6, y * 3.6, 0) for x, y in outline], [tuple(range(len(outline)))])
    hand.visible_camera = False
    hand.visible_glossy = False
    hand.visible_transmission = False
    sp_loc = hpos + R * 6 - look * 10 + Vector((0, 0, 34))
    spot = M.add_spot(sc, sp_loc, hpos, energy=9.0 * 4 * math.pi * 36 ** 2, size_deg=24, blend=0.55, radius=0.25,
                      name='foco_mano')
    spot.parent = gR
    tr_ = W('recuperar')
    hand_p = hpos + (sp_loc - hpos) * 0.4
    for t, off in ((tr_ - 0.6, R * 7 + look * 1), (tr_ + 0.1, R * 0.3), (tr_ + 1.2, Vector((0, 0, 0))),
                   (tr_ + 2.0, R * 8 - look * 3)):
        hand.location = hand_p + off
        key(hand, 'location', t, hand.location.copy())
    hand.rotation_euler = (math.radians(15), 0, math.atan2(R.y, R.x) - math.radians(70))
    hand.parent = gR
    key(fe, 'location', t0, P)
    key(fe, 'location', W('construir'), (target + hpos) / 2)
    fill_light(sc, Lc + R * 10 + Vector((0, 0, 10)), P, power=0.22)
    return cam, fe, (t0, t1), dict(cut=t_cut, open=t_open, crane=tb, recover=W('recuperar') + 0.35)


def shot_P(sc):
    """Portada: maqueta de España, casas de vidrio y cifras recortadas."""
    c = common(sc, parcel_width=1.0, sun=(215, 26, 3.0))
    c['hscale'] = 1.9
    cam, tgt = M.add_camera(sc, 40)
    fe = focus_empty(sc)
    t0, t1 = 20.0, 20.1
    ctr = Vector((112, 20, TOP))
    look = Vector((0.08, 1.0, 0)).normalized()
    L = ctr - look * 1250 + Vector((0, 0, 1650))
    cam_keys(cam, tgt, [(t0, L, ctr, 40), (t1, L, ctr, 40)])
    rim = c['hmat'].node_tree.nodes['rim'].outputs[0]
    rim.default_value = 4.5
    white = M.mat_card(M.C_WHITE)
    red = M.mat_card(M.C_RED, 'carton_rojo')
    pose = pose_eval(sc, cam, tgt, t0)
    v = 0.3 - TOP
    a = card_on_screen('3.800.000', white, pose, 530, 480, 880, lift=v)
    b = card_on_screen('VACÍAS', white, pose, 530, 615, 400, lift=v)
    d = card_on_screen('FALTAN', white, pose, 530, 1395, 380, lift=v)
    e = card_on_screen('750.000', red, pose, 530, 1600, 760, lift=v)
    houses_mesh(c)
    key(fe, 'location', t0, ctr)
    fe['ts'] = 0.45
    fill_light(sc, L + Vector((300, 0, 200)), ctr, power=0.15)
    return cam, fe, (t0, t1), {}


SHOT_FUNCS = dict(P_portada=shot_P, A_hook=shot_A, B_contraste=shot_B, C_pregunta=shot_C, D_ourense=shot_D,
                  E_provincias=shot_E, F_pueblos=shot_F, G_sintesis=shot_G, H_dilema=shot_H)
