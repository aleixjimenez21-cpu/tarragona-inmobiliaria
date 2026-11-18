"""LA MAQUETA: construcción de la escena en Blender (bpy).

Unidades: 1 unidad = 1 km del mapa. Las piezas de madera miden 6 de grosor.
"""
import bpy, bmesh, json, math, os, random
import numpy as np
from mathutils import Vector, Matrix
from mathutils.geometry import tessellate_polygon

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = json.load(open(os.path.join(ROOT, 'data', 'maqueta.json')))
FONT_DIR = os.path.join(ROOT, 'fonts')
FPS = 30
BASE_H = 6.0       # grosor de la madera
TOP = BASE_H       # cota de la superficie

C_WHITE = (0.905, 0.879, 0.823)   # #F4F1EA en lineal
C_WOOD = (0.584, 0.397, 0.195)    # #C9A97A en lineal
C_GLASS = (0.521, 0.686, 1.0)     # #BFD8FF lineal
C_RED = (0.680, 0.019, 0.027)     # #D7262E lineal


def srgb(h):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple((x / 12.92 if x <= 0.04045 else ((x + .055) / 1.055) ** 2.4) for x in c)

# ======================================================================= util

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = FPS
    sc.unit_settings.system = 'NONE'
    w = bpy.data.worlds.new('W')
    w.use_nodes = True
    bg = w.node_tree.nodes['Background']
    bg.inputs[0].default_value = (0.0018, 0.0016, 0.0015, 1)
    bg.inputs[1].default_value = 1.0
    sc.world = w
    return sc


def new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m, m.node_tree.nodes, m.node_tree.links


def clock_node(nodes, name='clock'):
    """Nodo Value cuyo valor = segundos del plano (driver sobre el frame)."""
    v = nodes.new('ShaderNodeValue')
    v.name = name
    d = v.outputs[0].driver_add('default_value').driver
    d.type = 'SCRIPTED'
    d.expression = '(frame - 1) / %d' % FPS
    return v


def smoothstep_nodes(nodes, links, x_socket, e0, e1):
    mr = nodes.new('ShaderNodeMapRange')
    mr.interpolation_type = 'SMOOTHSTEP'
    mr.inputs['From Min'].default_value = e0
    mr.inputs['From Max'].default_value = e1
    links.new(x_socket, mr.inputs['Value'])
    return mr.outputs['Result']


def math_node(nodes, links, op, a, b=None, val=None):
    n = nodes.new('ShaderNodeMath')
    n.operation = op
    for i, s in enumerate((a, b)):
        if s is None:
            continue
        if isinstance(s, (int, float)):
            n.inputs[i].default_value = s
        else:
            links.new(s, n.inputs[i])
    return n.outputs[0]

# ===================================================================== materials

def prop_node(N, name, default=0.0):
    """Nodo Value enlazado a una propiedad de la escena (animable): scene[name]."""
    sc = bpy.context.scene
    if name not in sc.keys():
        sc[name] = default
    v = N.new('ShaderNodeValue'); v.name = name
    d = v.outputs[0].driver_add('default_value').driver
    d.type = 'AVERAGE'
    var = d.variables.new(); var.name = 'v'; var.type = 'SINGLE_PROP'
    var.targets[0].id_type = 'SCENE'; var.targets[0].id = sc
    var.targets[0].data_path = '["%s"]' % name
    return v.outputs[0]


def mat_wood():
    """Madera clara lisa (sin veta granulosa), 20 % más oscura que antes."""
    m, N, L = new_mat('madera')
    bsdf = N['Principled BSDF']
    tc = N.new('ShaderNodeTexCoord')
    noise = N.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = 0.012
    noise.inputs['Detail'].default_value = 1.0
    L.new(tc.outputs['Object'], noise.inputs['Vector'])
    ramp = N.new('ShaderNodeValToRGB')
    c0 = tuple(x * 0.8 for x in srgb('#C2A170')); c1 = tuple(x * 0.8 for x in srgb('#CCAD80'))
    ramp.color_ramp.elements[0].color = (*c0, 1)
    ramp.color_ramp.elements[1].color = (*c1, 1)
    L.new(noise.outputs['Fac'], ramp.inputs['Fac'])
    dim = N.new('ShaderNodeAttribute'); dim.attribute_type = 'OBJECT'; dim.attribute_name = 'dim'
    dimv = math_node(N, L, 'SUBTRACT', 1.0, dim.outputs['Fac'])
    mul = N.new('ShaderNodeMixRGB'); mul.blend_type = 'MULTIPLY'; mul.inputs['Fac'].default_value = 1
    L.new(ramp.outputs['Color'], mul.inputs[1])
    cc = N.new('ShaderNodeCombineColor')
    for k in ('Red', 'Green', 'Blue'):
        L.new(dimv, cc.inputs[k])
    L.new(cc.outputs[0], mul.inputs[2])
    L.new(mul.outputs[0], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.55
    return m


def mat_velvet():
    m, N, L = new_mat('terciopelo')
    b = N['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.0025, 0.0025, 0.0025, 1)
    b.inputs['Roughness'].default_value = 1.0
    b.inputs['Sheen Weight'].default_value = 0.25
    b.inputs['Sheen Roughness'].default_value = 0.4
    b.inputs['Sheen Tint'].default_value = (0.06, 0.056, 0.052, 1)
    return m


def mat_flat(name, color, rough=0.7):
    m, N, L = new_mat(name)
    b = N['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = rough
    return m


def _house_logic(N, L):
    """f = factor de vidrio (0 habitada, 1 vacía); dm = oscurecimiento (0..1)."""
    clk = clock_node(N)
    a_vac = N.new('ShaderNodeAttribute'); a_vac.attribute_name = 'vac'
    a_tw = N.new('ShaderNodeAttribute'); a_tw.attribute_name = 'tw'
    a_rec = N.new('ShaderNodeAttribute'); a_rec.attribute_name = 'rec'
    a_hl = N.new('ShaderNodeAttribute'); a_hl.attribute_name = 'hlt'
    rec_t = prop_node(N, 'recover_t', 1e6)
    dimrest = prop_node(N, 'dimrest', 0.0)
    dt = math_node(N, L, 'SUBTRACT', clk.outputs[0], a_tw.outputs['Fac'])
    s = smoothstep_nodes(N, L, dt, 0.0, 0.16)
    f = math_node(N, L, 'MULTIPLY', s, a_vac.outputs['Fac'])
    dtr = math_node(N, L, 'SUBTRACT', clk.outputs[0], rec_t)
    sr = smoothstep_nodes(N, L, dtr, 0.0, 0.9)
    srm = math_node(N, L, 'MULTIPLY', sr, a_rec.outputs['Fac'])
    f = math_node(N, L, 'MULTIPLY', f, math_node(N, L, 'SUBTRACT', 1.0, srm))
    # casas resaltadas (hlt <= reloj) no se oscurecen
    lit = smoothstep_nodes(N, L, math_node(N, L, 'SUBTRACT', clk.outputs[0], a_hl.outputs['Fac']), 0.0, 0.25)
    dm = math_node(N, L, 'MULTIPLY', dimrest, math_node(N, L, 'SUBTRACT', 1.0, lit))
    flash = math_node(N, L, 'SUBTRACT', smoothstep_nodes(N, L, dt, -0.02, 0.04), smoothstep_nodes(N, L, dt, 0.04, 0.45))
    flash = math_node(N, L, 'MULTIPLY', flash, a_vac.outputs['Fac'])
    return f, dm, flash


def mat_houses():
    """Slot 0: casa. Habitada = blanco sólido; vacía = vidrio casi invisible."""
    m, N, L = new_mat('casas')
    out = N['Material Output']; white = N['Principled BSDF']
    f, dm, flash = _house_logic(N, L)
    col = N.new('ShaderNodeMixRGB'); col.blend_type = 'MULTIPLY'; col.inputs['Fac'].default_value = 1
    col.inputs[1].default_value = (*C_WHITE, 1)
    k = math_node(N, L, 'SUBTRACT', 1.0, math_node(N, L, 'MULTIPLY', dm, 0.8))
    cc = N.new('ShaderNodeCombineColor')
    for ch in ('Red', 'Green', 'Blue'):
        L.new(k, cc.inputs[ch])
    L.new(cc.outputs[0], col.inputs[2])
    L.new(col.outputs[0], white.inputs['Base Color'])
    white.inputs['Roughness'].default_value = 0.8
    white.inputs['Emission Color'].default_value = (*C_GLASS, 1)
    L.new(math_node(N, L, 'MULTIPLY', flash, 3.0), white.inputs['Emission Strength'])
    # vidrio casi invisible: transparente + reflejo frío débil en ángulo rasante
    tr = N.new('ShaderNodeBsdfTransparent'); tr.inputs[0].default_value = (0.97, 0.98, 1.0, 1)
    gl = N.new('ShaderNodeBsdfGlossy'); gl.inputs['Roughness'].default_value = 0.05
    gl.inputs['Color'].default_value = (*C_GLASS, 1)
    fr = N.new('ShaderNodeLayerWeight'); fr.inputs['Blend'].default_value = 0.2
    gmix = N.new('ShaderNodeMixShader')
    L.new(math_node(N, L, 'MULTIPLY', fr.outputs['Fresnel'], 0.55), gmix.inputs['Fac'])
    L.new(tr.outputs[0], gmix.inputs[1]); L.new(gl.outputs[0], gmix.inputs[2])
    lp = N.new('ShaderNodeLightPath')
    sh = N.new('ShaderNodeMixShader')
    L.new(lp.outputs['Is Shadow Ray'], sh.inputs['Fac'])
    L.new(gmix.outputs[0], sh.inputs[1]); L.new(tr.outputs[0], sh.inputs[2])
    mix = N.new('ShaderNodeMixShader')
    L.new(f, mix.inputs['Fac'])
    L.new(white.outputs[0], mix.inputs[1]); L.new(sh.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], out.inputs['Surface'])
    return m


def mat_window():
    """Slot 1: ventana encendida cálida (#FFC27A) solo en casas habitadas."""
    m, N, L = new_mat('ventana')
    out = N['Material Output']
    N.remove(N['Principled BSDF'])
    f, dm, flash = _house_logic(N, L)
    em = N.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (*srgb('#FFC27A'), 1)
    win = prop_node(N, 'win', 9.0)
    L.new(math_node(N, L, 'MULTIPLY', win, math_node(N, L, 'SUBTRACT', 1.0, math_node(N, L, 'MULTIPLY', dm, 0.85))),
          em.inputs['Strength'])
    tr = N.new('ShaderNodeBsdfTransparent')
    mix = N.new('ShaderNodeMixShader')
    L.new(f, mix.inputs['Fac'])
    L.new(em.outputs[0], mix.inputs[1]); L.new(tr.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], out.inputs['Surface'])
    return m


def mat_edges():
    """Slot 2: aristas iluminadas en azul frío (#BFD8FF) de las casas vacías."""
    m, N, L = new_mat('aristas')
    out = N['Material Output']
    N.remove(N['Principled BSDF'])
    f, dm, flash = _house_logic(N, L)
    em = N.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (0.30, 0.52, 1.0, 1)
    rim = prop_node(N, 'rim', 1.4)
    L.new(math_node(N, L, 'MULTIPLY', rim, math_node(N, L, 'SUBTRACT', 1.0, math_node(N, L, 'MULTIPLY', dm, 0.6))),
          em.inputs['Strength'])
    tr = N.new('ShaderNodeBsdfTransparent')
    mix = N.new('ShaderNodeMixShader')
    L.new(f, mix.inputs['Fac'])
    L.new(tr.outputs[0], mix.inputs[1]); L.new(em.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], out.inputs['Surface'])
    return m


def house_mats():
    return [mat_houses(), mat_window(), mat_edges()]


def mat_card(color=C_WHITE, name='carton'):
    m, N, L = new_mat(name)
    b = N['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.85
    geo = N.new('ShaderNodeNewGeometry')
    sep = N.new('ShaderNodeSeparateXYZ')
    # canto ligeramente más oscuro
    L.new(N.new('ShaderNodeTexCoord').outputs['Normal'], sep.inputs[0])
    edge = math_node(N, L, 'ABSOLUTE', sep.outputs['Z'])
    mix = N.new('ShaderNodeMixRGB')
    L.new(edge, mix.inputs['Fac'])
    mix.inputs[1].default_value = (color[0] * .62, color[1] * .6, color[2] * .58, 1)
    mix.inputs[2].default_value = (*color, 1)
    L.new(mix.outputs[0], b.inputs['Base Color'])
    noise = N.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = 40
    bump = N.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.05
    L.new(noise.outputs['Fac'], bump.inputs['Height']); L.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def mat_pencil(name='lapiz'):
    """Trazo de lápiz rojo que se dibuja: atributos u (0-1 a lo largo), t0 y dur."""
    m, N, L = new_mat(name)
    out = N['Material Output']; b = N['Principled BSDF']
    b.inputs['Base Color'].default_value = (*C_RED, 1)
    b.inputs['Roughness'].default_value = 0.55
    b.inputs['Emission Color'].default_value = (*C_RED, 1)
    b.inputs['Emission Strength'].default_value = 0.15
    clk = clock_node(N)
    au = N.new('ShaderNodeAttribute'); au.attribute_name = 'u'
    at = N.new('ShaderNodeAttribute'); at.attribute_name = 't0'
    ad = N.new('ShaderNodeAttribute'); ad.attribute_name = 'dur'
    ac = N.new('ShaderNodeAttribute'); ac.attribute_name = 'cut'  # fracción máxima (líneas que no llegan)
    prog = math_node(N, L, 'DIVIDE', math_node(N, L, 'SUBTRACT', clk.outputs[0], at.outputs['Fac']), ad.outputs['Fac'])
    prog = math_node(N, L, 'MINIMUM', prog, ac.outputs['Fac'])
    vis = math_node(N, L, 'LESS_THAN', au.outputs['Fac'], prog)
    # textura de grafito
    tc = N.new('ShaderNodeTexCoord')
    nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 6.0; nz.inputs['Detail'].default_value = 8
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    grain = smoothstep_nodes(N, L, nz.outputs['Fac'], 0.32, 0.5)
    alpha = math_node(N, L, 'MULTIPLY', vis, grain)
    fade = N.new('ShaderNodeValue'); fade.name = 'fade'; fade.outputs[0].default_value = 1.0
    alpha = math_node(N, L, 'MULTIPLY', alpha, fade.outputs[0])
    tr = N.new('ShaderNodeBsdfTransparent')
    mix = N.new('ShaderNodeMixShader')
    L.new(alpha, mix.inputs['Fac'])
    L.new(tr.outputs[0], mix.inputs[1]); L.new(b.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], out.inputs['Surface'])
    return m

# ======================================================================= geometry

def mesh_obj(name, verts, faces, mat=None, attrs=None, smooth=False, coll=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.update()
    if attrs:
        for k, vals in attrs.items():
            a = me.attributes.new(k, 'FLOAT', 'POINT')
            a.data.foreach_set('value', np.asarray(vals, dtype=np.float32))
    ob = bpy.data.objects.new(name, me)
    (coll or bpy.context.scene.collection).objects.link(ob)
    if mat:
        me.materials.append(mat)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    return ob


def build_province(pid, wood):
    p = DATA['provinces'][pid]
    verts, faces = [], []
    for poly in p['polys']:
        rings = [poly['ext']] + poly['holes']
        rings3 = [[Vector((x, y, 0)) for x, y in r] for r in rings]
        tris = tessellate_polygon(rings3)
        flat = [v for r in rings for v in r]
        base = len(verts)
        n = len(flat)
        for x, y in flat:
            verts.append((x, y, TOP))
        for x, y in flat:
            verts.append((x, y, 0.0))
        for t in tris:
            faces.append((base + t[0], base + t[1], base + t[2]))
            faces.append((base + n + t[2], base + n + t[1], base + n + t[0]))
        off = 0
        for r in rings:
            k = len(r)
            for i in range(k):
                a = base + off + i; b = base + off + (i + 1) % k
                faces.append((a + n, b + n, b, a))
            off += k
    ob = mesh_obj('prov_' + pid, verts, faces, wood)
    me = ob.data
    # normales coherentes
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    bev = ob.modifiers.new('bev', 'BEVEL')
    bev.width = 0.35; bev.segments = 2; bev.limit_method = 'ANGLE'
    bev.angle_limit = math.radians(50)
    ob['glow'] = 1.0
    ob['dim'] = 0.0
    return ob


# casita tipo: 1.3 x 1.0, paredes 0.85, cumbrera +0.5
def house_template(w=1.3, d=1.0, h=0.85, r=0.5, ov=0.07):
    hw, hd = w / 2, d / 2
    V = [(-hw, -hd, 0), (hw, -hd, 0), (hw, hd, 0), (-hw, hd, 0),
         (-hw, -hd, h), (hw, -hd, h), (hw, hd, h), (-hw, hd, h),
         (-hw, 0, h + r), (hw, 0, h + r)]
    F = [(0, 1, 5, 4), (2, 3, 7, 6), (1, 2, 6, 9, 5), (3, 0, 4, 8, 7), (3, 2, 1, 0)]
    # tejado con alero: dos planos algo mayores
    rv = len(V)
    hw2, hd2 = hw + ov, hd + ov
    zl = h - ov * r / hd
    V += [(-hw2, -hd2, zl), (hw2, -hd2, zl), (hw2, 0, h + r + 0.02), (-hw2, 0, h + r + 0.02),
          (-hw2, hd2, zl), (hw2, hd2, zl)]
    F += [(rv + 0, rv + 1, rv + 2, rv + 3), (rv + 3, rv + 2, rv + 5, rv + 4)]
    # grosor del tejado (cantos)
    t = 0.05
    rv2 = len(V)
    V += [(x, y, z - t) for (x, y, z) in V[rv:rv + 6]]
    F += [(rv2 + 3, rv2 + 2, rv2 + 1, rv2 + 0), (rv2 + 4, rv2 + 5, rv2 + 2, rv2 + 3)]
    F += [(rv + 0, rv2 + 0, rv2 + 1, rv + 1), (rv + 5, rv2 + 5, rv2 + 4, rv + 4),
          (rv + 1, rv2 + 1, rv2 + 2, rv + 2), (rv + 2, rv2 + 2, rv2 + 5, rv + 5),
          (rv + 3, rv2 + 3, rv2 + 0, rv + 0), (rv + 4, rv2 + 4, rv2 + 3, rv + 3)]
    return np.array(V, float), F


def block_template(w=1.4, d=1.1, h=2.0):
    hw, hd = w / 2, d / 2
    V = [(-hw, -hd, 0), (hw, -hd, 0), (hw, hd, 0), (-hw, hd, 0),
         (-hw, -hd, h), (hw, -hd, h), (hw, hd, h), (-hw, hd, h)]
    # pretil
    p = 0.08; hp = 0.12
    V += [(-hw + p, -hd + p, h), (hw - p, -hd + p, h), (hw - p, hd - p, h), (-hw + p, hd - p, h),
          (-hw + p, -hd + p, h - hp), (hw - p, -hd + p, h - hp), (hw - p, hd - p, h - hp), (-hw + p, hd - p, h - hp)]
    F = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (3, 2, 1, 0),
         (4, 5, 9, 8), (5, 6, 10, 9), (6, 7, 11, 10), (7, 4, 8, 11),
         (8, 9, 13, 12), (9, 10, 14, 13), (10, 11, 15, 14), (11, 8, 12, 15), (12, 13, 14, 15)]
    # invertir orientación del interior del pretil
    F[9:13] = [tuple(reversed(f)) for f in F[9:13]]
    return np.array(V, float), F


def church_template():
    """Iglesia de maqueta: nave + torre con chapitel."""
    Vn, Fn = house_template(w=2.6, d=1.3, h=1.1, r=0.6)
    Vt, Ft = block_template(w=0.8, d=0.8, h=2.6)
    Vt = Vt + np.array([1.55, 0, 0])
    # chapitel
    Vs = np.array([(1.15, -.4, 2.6), (1.95, -.4, 2.6), (1.95, .4, 2.6), (1.15, .4, 2.6), (1.55, 0, 3.6)])
    Fs = [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)]
    V = np.vstack([Vn, Vt, Vs])
    F = [tuple(f) for f in Fn] + [tuple(i + len(Vn) for i in f) for f in Ft] + \
        [tuple(i + len(Vn) + len(Vt) for i in f) for f in Fs]
    return V, F


def house_parts(w, d, h, r, windows=True, ov=0.07):
    """Casa con tejado a dos aguas (cumbrera según x). Devuelve V, F, ventanas (lista de quads) y aristas."""
    V, F = house_template(w, d, h, r, ov)
    hw, hd = w / 2, d / 2
    wins = []
    if windows:
        ws = min(0.3, h * 0.34)
        rows = max(1, int(h / 0.9))
        for row in range(rows):
            zc = h * (row + 0.55) / rows
            for xc in (-hw * 0.45, hw * 0.45):
                for sgn in (-1, 1):
                    y = sgn * (hd + 0.012)
                    q = [(xc - ws / 2, y, zc - ws / 2), (xc + ws / 2, y, zc - ws / 2),
                         (xc + ws / 2, y, zc + ws / 2), (xc - ws / 2, y, zc + ws / 2)]
                    wins.append(q if sgn > 0 else q[::-1])
            for sgn in (-1, 1):
                x = sgn * (hw + 0.012)
                q = [(x, -ws / 2, zc - ws / 2), (x, ws / 2, zc - ws / 2), (x, ws / 2, zc + ws / 2), (x, -ws / 2, zc + ws / 2)]
                wins.append(q[::-1] if sgn > 0 else q)
    c = [(-hw, -hd, 0), (hw, -hd, 0), (hw, hd, 0), (-hw, hd, 0),
         (-hw, -hd, h), (hw, -hd, h), (hw, hd, h), (-hw, hd, h), (-hw, 0, h + r), (hw, 0, h + r)]
    E = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 4), (1, 5), (2, 6), (3, 7), (4, 5), (6, 7),
         (4, 8), (7, 8), (5, 9), (6, 9), (8, 9)]
    edges = [(c[a], c[b]) for a, b in E]
    return V, F, wins, edges


def edge_box(p0, p1, t):
    p0 = np.array(p0, float); p1 = np.array(p1, float)
    u = p1 - p0; L_ = np.linalg.norm(u); u /= L_
    a = np.cross(u, [0, 0, 1.0])
    if np.linalg.norm(a) < 1e-6:
        a = np.array([1.0, 0, 0])
    a /= np.linalg.norm(a); b = np.cross(u, a)
    p0 = p0 - u * t / 2; p1 = p1 + u * t / 2
    V = []
    for p in (p0, p1):
        for sa, sb in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            V.append(p + a * sa * t / 2 + b * sb * t / 2)
    F = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return V, F


def build_houses(mats, select=None, tw_fn=None, name='casas', house_scale=1.0, rec_fn=None, hlt_fn=None,
                 edge_t=0.045):
    """Todas las casitas en un mesh: slot 0 casa, 1 ventanas, 2 aristas (solo vacías)."""
    if not isinstance(mats, (list, tuple)):
        mats = [mats]
    CV, CF = church_template()
    verts, faces, fmat = [], [], []
    A = {'vac': [], 'tw': [], 'rec': [], 'hlt': [], 'seed': []}
    rnd = random.Random(3)
    hero_first = {v['i0'] for v in DATA['hero_villages']}
    s_ = house_scale
    zs = 1 + (s_ - 1) * 0.6
    for idx, h in enumerate(DATA['houses']):
        x, y, rot, units, pid, vac, kind, vil = h
        r1, r2, r3, r4 = rnd.random(), rnd.random(), rnd.random(), rnd.random()
        if select and not select(idx, h):
            continue
        wins, edges = [], []
        if idx in hero_first:
            V, F = CV * np.array([s_, s_, zs]), CF
        else:
            if units > 1:
                hz = 0.95 + 0.38 * units + (r1 - .4) * 0.35
                w, d, hh, rr = 1.45, 1.12, hz, 0.62
            else:
                s = 0.88 + r1 * 0.24
                w, d, hh, rr = 1.3 * s * (0.92 + r2 * 0.2), 1.0 * s, 0.85 * s * (0.92 + r3 * 0.25), 0.55 * s
            V, F, wins, edges = house_parts(w * s_, d * s_, hh * zs, rr * zs, windows=True)
        c, si = math.cos(rot), math.sin(rot)
        R = np.array([[c, -si, 0], [si, c, 0], [0, 0, 1]])
        off = np.array([x, y, TOP])
        tw = tw_fn(idx, h) if tw_fn else -10.0
        rec = rec_fn(idx, h) if rec_fn else 0.0
        hlt = hlt_fn(idx, h) if hlt_fn else 1e6
        attrs = (vac, tw, rec, hlt, r4)

        def add(Vl, Fl, mi):
            Vw = np.asarray(Vl, float) @ R.T + off
            base = len(verts)
            verts.extend(Vw.tolist())
            faces.extend([tuple(base + i for i in f) for f in Fl])
            fmat.extend([mi] * len(Fl))
            for k, v in zip(('vac', 'tw', 'rec', 'hlt', 'seed'), attrs):
                A[k].extend([v] * len(Vl))
        add(V, F, 0)
        # ventana encendida: una por fachada visible (algunas apagadas al azar)
        if wins:
            lit = [q for j, q in enumerate(wins) if (j + int(r4 * 7)) % 3 != 0]
            WV = [p for q in lit for p in q]
            WF = [(4 * j, 4 * j + 1, 4 * j + 2, 4 * j + 3) for j in range(len(lit))]
            add(WV, WF, 1)
        if vac and edges and len(mats) > 2:
            EV, EF = [], []
            for p0, p1 in edges:
                bv, bf = edge_box(p0, p1, edge_t * s_)
                b0 = len(EV); EV.extend(bv); EF.extend([tuple(b0 + i for i in f) for f in bf])
            add(EV, EF, 2)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    for k, vals in A.items():
        a = me.attributes.new(k, 'FLOAT', 'POINT')
        a.data.foreach_set('value', np.asarray(vals, dtype=np.float32))
    for m in mats:
        me.materials.append(m)
    me.polygons.foreach_set('material_index', np.asarray(fmat, dtype=np.int32))
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def text_obj(txt, size, extrude=0.18, font='Anton-Regular.ttf', mat=None, align='CENTER', spacing=1.0):
    cu = bpy.data.curves.new('t_' + txt, 'FONT')
    cu.body = txt
    cu.font = bpy.data.fonts.load(os.path.join(FONT_DIR, font), check_existing=True)
    cu.size = size
    cu.extrude = extrude
    cu.bevel_depth = 0.0
    cu.align_x = align
    cu.align_y = 'BOTTOM'
    cu.space_character = spacing
    cu.resolution_u = 4
    ob = bpy.data.objects.new('t_' + txt, cu)
    ob.pass_index = 1   # máscara de rótulos: sin desenfoque en post
    bpy.context.scene.collection.objects.link(ob)
    if mat:
        cu.materials.append(mat)
    return ob


def letters(txt, mat, font='Anton-Regular.ttf', track=0.05, extrude=0.07):
    """Cada carácter es un objeto (tamaño 1). Devuelve [(obj, x_centro, ancho)], ancho_total, alto."""
    out = []
    x = 0.0
    hmax = 0.0
    dg = None
    for ch in txt:
        if ch == ' ':
            x += 0.24
            continue
        t = text_obj(ch, 1.0, extrude, font, mat, 'LEFT')
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        ev = t.evaluated_get(dg)
        me = ev.to_mesh()
        xs = [v.co.x for v in me.vertices]; ys = [v.co.y for v in me.vertices]
        ev.to_mesh_clear()
        x0, x1 = min(xs), max(xs)
        hmax = max(hmax, max(ys))
        t.data.offset_x = -(x0 + x1) / 2
        w = x1 - x0
        out.append([t, x + w / 2, w])
        x += w + track
    total = x - track
    for o in out:
        o[1] -= total / 2
    return out, total, hmax


def stroke_mesh(name, polylines, mat, width=0.35, z=TOP + 0.03):
    """Cintas planas sobre la madera. polylines: lista de dict(pts, t0, dur, cut)."""
    verts, faces, A = [], [], {'u': [], 't0': [], 'dur': [], 'cut': []}
    for pl in polylines:
        P = np.asarray(pl['pts'], float)
        if len(P) < 2:
            continue
        seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
        s = np.concatenate([[0], np.cumsum(seg)])
        L = s[-1] if s[-1] > 0 else 1
        w = pl.get('width', width)
        base = len(verts)
        for i, p in enumerate(P):
            if i == 0:
                t = P[1] - P[0]
            elif i == len(P) - 1:
                t = P[-1] - P[-2]
            else:
                t = P[i + 1] - P[i - 1]
            t = t / (np.linalg.norm(t) + 1e-9)
            n = np.array([-t[1], t[0]])
            # grosor variable de lápiz
            ww = w * (0.85 + 0.15 * math.sin(s[i] * 3.1 + base))
            for sg in (-1, 1):
                q = p + n * ww / 2 * sg
                verts.append((q[0], q[1], z + pl.get('dz', 0)))
                A['u'].append(s[i] / L); A['t0'].append(pl['t0']); A['dur'].append(pl['dur'])
                A['cut'].append(pl.get('cut', 1.01))
        for i in range(len(P) - 1):
            a = base + 2 * i
            faces.append((a, a + 2, a + 3, a + 1))
    return mesh_obj(name, verts, faces, mat, A)


def sketch_rect(cx, cy, w, h, rot, rnd, over=0.25):
    """Rectángulo a lápiz de arquitecto: cuatro trazos que se pasan de las esquinas."""
    c, s = math.cos(rot), math.sin(rot)
    def tf(px, py):
        return (cx + px * c - py * s, cy + px * s + py * c)
    corners = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    lines = []
    for i in range(4):
        a = np.array(corners[i]); b = np.array(corners[(i + 1) % 4])
        d = (b - a) / np.linalg.norm(b - a)
        a2 = a - d * over * rnd.uniform(.3, 1.0) + rnd.uniform(-.03, .03)
        b2 = b + d * over * rnd.uniform(.3, 1.0) + rnd.uniform(-.03, .03)
        pts = [tf(*(a2 + (b2 - a2) * k / 6 + np.array([-d[1], d[0]]) * rnd.uniform(-.015, .015))) for k in range(7)]
        lines.append(pts)
    return lines

# ======================================================================= scene

def setup_render(sc, res=(1080, 1920), samples=48, pct=100):
    sc.render.engine = 'CYCLES'
    cy = sc.cycles
    cy.device = 'CPU'
    cy.samples = samples
    cy.use_adaptive_sampling = True
    cy.adaptive_threshold = 0.03
    cy.use_denoising = True
    cy.denoiser = 'OPENIMAGEDENOISE'
    cy.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
    cy.max_bounces = 6
    cy.diffuse_bounces = 2
    cy.glossy_bounces = 2
    cy.transmission_bounces = 6
    cy.transparent_max_bounces = 8
    cy.caustics_reflective = False
    cy.caustics_refractive = False
    cy.blur_glossy = 1.0
    cy.sample_clamp_indirect = 5.0
    cy.use_auto_tile = False
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = pct
    sc.render.film_transparent = False
    sc.view_settings.view_transform = 'Standard'
    sc.render.use_persistent_data = True
    vl = sc.view_layers[0]
    vl.use_pass_z = True
    vl.use_pass_object_index = True
    try:
        sc.render.image_settings.media_type = 'MULTI_LAYER_IMAGE'
        sc.render.image_settings.file_format = 'OPEN_EXR'
    except Exception:
        sc.render.image_settings.file_format = 'OPEN_EXR_MULTILAYER'
    sc.render.image_settings.color_depth = '16'
    sc.render.image_settings.exr_codec = 'DWAA'
    sc.render.threads_mode = 'AUTO'


def build_world(provs_glow=None):
    wood = mat_wood()
    pv = {}
    for pid in DATA['provinces']:
        pv[pid] = build_province(pid, wood)
    # mesa de terciopelo
    vel = mat_velvet()
    bpy.ops.mesh.primitive_plane_add(size=6000, location=(0, 0, -0.01))
    floor = bpy.context.active_object; floor.name = 'mesa'
    floor.data.materials.append(vel)
    return pv


def add_sun(sc, az=200, el=24, energy=4.2, angle=4.0, color=(1.0, 0.86, 0.70)):
    ld = bpy.data.lights.new('sol', 'SUN')
    ld.energy = energy; ld.angle = math.radians(angle); ld.color = color
    ob = bpy.data.objects.new('sol', ld)
    sc.collection.objects.link(ob)
    ob.rotation_euler = (math.radians(90 - el), 0, math.radians(az))
    return ob


def add_area(sc, loc, target, size=200, energy=2e6, color=(1, .9, .78), name='softbox'):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.shape = 'RECTANGLE'; ld.size = size; ld.size_y = size * .6
    ld.energy = energy; ld.color = color
    ob = bpy.data.objects.new(name, ld)
    sc.collection.objects.link(ob)
    ob.location = loc
    look_at(ob, target)
    return ob


def add_spot(sc, loc, target, energy=1e6, size_deg=20, blend=0.6, color=(1, .93, .82), radius=3, name='foco'):
    ld = bpy.data.lights.new(name, 'SPOT')
    ld.energy = energy; ld.spot_size = math.radians(size_deg); ld.spot_blend = blend
    ld.color = color; ld.shadow_soft_size = radius
    ob = bpy.data.objects.new(name, ld)
    sc.collection.objects.link(ob)
    ob.location = loc
    look_at(ob, target)
    return ob


def look_at(ob, target):
    d = Vector(target) - Vector(ob.location)
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def add_camera(sc, lens=50, sensor=36):
    cd = bpy.data.cameras.new('cam')
    cd.lens = lens; cd.sensor_width = sensor; cd.sensor_height = sensor; cd.sensor_fit = 'VERTICAL'
    cd.clip_start = 0.05; cd.clip_end = 10000
    cam = bpy.data.objects.new('cam', cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    tgt = bpy.data.objects.new('cam_target', None)
    sc.collection.objects.link(tgt)
    tc = cam.constraints.new('TRACK_TO')
    tc.target = tgt; tc.track_axis = 'TRACK_NEGATIVE_Z'; tc.up_axis = 'UP_Y'
    return cam, tgt


def key(ob, path, t, value, interp='BEZIER', ease='AUTO'):
    """Inserta clave en el tiempo t (segundos, relativo al plano)."""
    f = 1 + t * FPS
    if isinstance(value, (list, tuple, Vector)):
        setattr(ob, path, value)
    else:
        if '[' in path or '"' in path:
            ob[path.strip('[]"')] = value
        else:
            setattr(ob, path, value)
    ob.keyframe_insert(data_path=path, frame=f)
    ad = ob.animation_data
    if ad and ad.action:
        for fc in iter_fcurves(ad.action):
            for kp in fc.keyframe_points:
                if abs(kp.co[0] - f) < 1e-3:
                    kp.interpolation = interp
                    kp.easing = ease


def iter_fcurves(action):
    if hasattr(action, 'fcurves') and action.fcurves is not None:
        try:
            for fc in action.fcurves:
                yield fc
            return
        except Exception:
            pass
    # Blender 5: acciones por capas
    for layer in action.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                for fc in cb.fcurves:
                    yield fc


def set_handles(ob, kind='AUTO_CLAMPED'):
    ad = ob.animation_data
    if ad and ad.action:
        for fc in iter_fcurves(ad.action):
            for kp in fc.keyframe_points:
                kp.handle_left_type = kind; kp.handle_right_type = kind


def node_value(mat, name):
    return mat.node_tree.nodes[name].outputs[0]
