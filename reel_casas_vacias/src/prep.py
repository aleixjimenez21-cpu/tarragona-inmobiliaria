"""Prepara la geometría de LA MAQUETA.

Lee los contornos del IGN (paquete es-atlas, TopoJSON) y genera:
  - piezas de madera por provincia (polígonos proyectados en km)
  - casitas (posición, giro, altura, unidades, vacía sí/no)
  - parcelas rojas del déficit
  - pueblos «héroe» para el plano macro de la escena 6
Todo se guarda en data/maqueta.json para que lo lea build_blend.py.

Cada casita representa ~1.500 viviendas (Censo 2021: 26,6 M). Las tasas de
vacío por provincia son una aproximación visual coherente con los datos
verificados del guion (14,4 % nacional, Ourense >40 %, Madrid ~6 %).
"""
import json, math, os, random, unicodedata
import numpy as np
from shapely.geometry import Polygon, MultiPolygon, Point, box
from shapely.ops import unary_union
from shapely.prepared import prep
from shapely import affinity

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOPO = os.path.join(ROOT, 'data', 'es_municipalities.topo.json')
OUT = os.path.join(ROOT, 'data', 'maqueta.json')
rng = random.Random(7)
nrng = np.random.default_rng(7)

LON0, LAT0 = -3.7, 40.0
KX = 111.32 * math.cos(math.radians(LAT0))
KY = 110.57
CANARIAS_SHIFT = (7.3, 6.3)  # grados: recuadro de Canarias bajo el golfo de Cádiz


def proj(lon, lat):
    return ((lon - LON0) * KX, (lat - LAT0) * KY)

# ---------------------------------------------------------------- topojson
T = json.load(open(TOPO))
sc, tr = T['transform']['scale'], T['transform']['translate']
ARCS = []
for arc in T['arcs']:
    x = y = 0
    pts = []
    for dx, dy in arc:
        x += dx; y += dy
        pts.append((x * sc[0] + tr[0], y * sc[1] + tr[1]))
    ARCS.append(pts)


def ring(idx):
    pts = []
    for i in idx:
        a = ARCS[i] if i >= 0 else ARCS[~i][::-1]
        pts.extend(a if not pts else a[1:])
    return pts


def geom(g, canarias=False):
    polys = [g['arcs']] if g['type'] == 'Polygon' else g['arcs']
    out = []
    for p in polys:
        rings = []
        for r in p:
            pts = ring(r)
            if canarias:
                pts = [(x + CANARIAS_SHIFT[0], y + CANARIAS_SHIFT[1]) for x, y in pts]
            rings.append([proj(x, y) for x, y in pts])
        rings = [r for r in rings if len(r) >= 4]
        if rings:
            out.append(Polygon(rings[0], rings[1:]).buffer(0))
    return unary_union(out)

CAN = {'35', '38'}
provs = {}
for g in T['objects']['provinces']['geometries']:
    provs[g['id']] = dict(name=g['properties']['name'], geom=geom(g, g['id'] in CAN))
munis = []
for g in T['objects']['municipalities']['geometries']:
    pid = g['id'][:2]
    if pid not in provs:
        continue
    gg = geom(g, pid in CAN)
    if gg.is_empty:
        continue
    munis.append(dict(id=g['id'], name=g['properties']['name'], prov=pid, geom=gg))

# ---------------------------------------------------------------- datos
# población 2021 (miles) y tasa de vivienda vacía aproximada (visual)
P = {
 '01': (333, .09), '02': (386, .17), '03': (1882, .14), '04': (731, .17), '05': (158, .29),
 '06': (669, .19), '07': (1173, .09), '08': (5715, .08), '09': (357, .23), '10': (391, .23),
 '11': (1245, .11), '12': (587, .18), '13': (492, .21), '14': (777, .15), '15': (1120, .18),
 '16': (196, .28), '17': (786, .14), '18': (921, .17), '19': (265, .19), '20': (727, .07),
 '21': (525, .16), '22': (223, .23), '23': (627, .19), '24': (452, .26), '25': (438, .18),
 '26': (320, .18), '27': (327, .33), '28': (6751, .06), '29': (1695, .11), '30': (1518, .14),
 '31': (661, .13), '32': (306, .47), '33': (1011, .18), '34': (160, .26), '35': (1128, .11),
 '36': (945, .19), '37': (328, .23), '38': (1044, .13), '39': (584, .15), '40': (153, .23),
 '41': (1950, .10), '42': (89, .29), '43': (816, .15), '44': (134, .31), '45': (703, .17),
 '46': (2589, .13), '47': (520, .14), '48': (1154, .08), '49': (168, .32), '50': (967, .15),
 '51': (83, .10), '52': (86, .10),
}
# ciudades: (nombre, provincia, población miles)
CITIES = [
 ('Madrid','28',3305),('Móstoles','28',210),('Alcalá de Henares','28',196),('Fuenlabrada','28',193),
 ('Leganés','28',189),('Getafe','28',185),('Alcorcón','28',170),('Torrejón de Ardoz','28',133),
 ('Parla','28',131),('Alcobendas','28',117),('Las Rozas de Madrid','28',96),('Rivas-Vaciamadrid','28',95),
 ('San Sebastián de los Reyes','28',89),('Pozuelo de Alarcón','28',87),('Coslada','28',81),('Valdemoro','28',78),
 ('Majadahonda','28',72),('Collado Villalba','28',64),('Aranjuez','28',60),('Arganda del Rey','28',56),
 ('Boadilla del Monte','28',58),('Pinto','28',53),('Colmenar Viejo','28',51),('Tres Cantos','28',48),
 ('Barcelona','08',1636),("Hospitalet de Llobregat",'08',265),('Badalona','08',223),('Terrassa','08',224),
 ('Sabadell','08',216),('Mataró','08',129),('Santa Coloma de Gramenet','08',120),('Cornellà de Llobregat','08',89),
 ('Sant Boi de Llobregat','08',84),('Sant Cugat del Vallès','08',92),('Rubí','08',78),('Manresa','08',78),
 ('Vilanova i la Geltrú','08',67),('Viladecans','08',67),('Prat de Llobregat','08',65),('Granollers','08',62),
 ('Castelldefels','08',67),('Cerdanyola del Vallès','08',58),('Mollet del Vallès','08',51),('Vic','08',47),('Igualada','08',40),
 ('Valencia','46',790),('Torrent','46',84),('Gandia','46',75),('Paterna','46',71),('Sagunto','46',67),
 ('Mislata','46',44),('Burjassot','46',38),('Alzira','46',45),('Ontinyent','46',35),
 ('Alicante','03',337),('Elche','03',234),('Torrevieja','03',83),('Orihuela','03',78),('Benidorm','03',70),
 ('Alcoy','03',59),('San Vicente del Raspeig','03',59),('Elda','03',52),('Dénia','03',42),('Petrer','03',35),
 ('Villena','03',34),('Santa Pola','03',33),('Xàbia','03',28),
 ('Murcia','30',460),('Cartagena','30',216),('Lorca','30',97),('Molina de Segura','30',73),('Alcantarilla','30',42),
 ('Mazarrón','30',33),('Cieza','30',35),('Yecla','30',35),('Águilas','30',36),('Torre-Pacheco','30',37),('San Javier','30',33),
 ('Málaga','29',579),('Marbella','29',148),('Mijas','29',85),('Vélez-Málaga','29',82),('Fuengirola','29',83),
 ('Torremolinos','29',69),('Benalmádena','29',69),('Estepona','29',71),('Rincón de la Victoria','29',49),
 ('Antequera','29',41),('Alhaurín de la Torre','29',42),('Ronda','29',34),
 ('Sevilla','41',684),('Dos Hermanas','41',135),('Alcalá de Guadaíra','41',76),('Utrera','41',50),('Écija','41',39),
 ('Jerez de la Frontera','11',213),('Algeciras','11',123),('Cádiz','11',114),('San Fernando','11',95),
 ('Puerto de Santa María','11',89),('Chiclana de la Frontera','11',86),('Sanlúcar de Barrameda','11',69),('Línea de la Concepción','11',63),
 ('Zaragoza','50',675),('Calatayud','50',20),('Bilbao','48',345),('Barakaldo','48',101),('Getxo','48',78),
 ('Donostia','20',187),('Irun','20',62),('Vitoria','01',254),('Pamplona','31',203),('Tudela','31',37),
 ('Gijón','33',268),('Oviedo','33',219),('Avilés','33',76),('Santander','39',172),('Torrelavega','39',51),
 ('Coruña','15',247),('Santiago de Compostela','15',98),('Ferrol','15',64),('Vigo','36',296),('Pontevedra','36',83),
 ('Lugo','27',98),('Ourense','32',104),('León','24',122),('Ponferrada','24',63),('Valladolid','47',297),
 ('Burgos','09',174),('Miranda de Ebro','09',35),('Aranda de Duero','09',33),('Salamanca','37',143),
 ('Palencia','34',78),('Zamora','49',61),('Segovia','40',51),('Ávila','05',58),('Soria','42',40),
 ('Logroño','26',151),('Huesca','22',53),('Teruel','44',36),('Lleida','25',140),('Tarragona','43',135),('Reus','43',106),
 ('Girona','17',103),('Figueres','17',47),('Castelló de la Plana','12',172),('Vila-real','12',51),
 ('Albacete','02',174),('Cuenca','16',54),('Guadalajara','19',87),('Toledo','45',85),('Talavera de la Reina','45',83),
 ('Ciudad Real','13',75),('Puertollano','13',47),('Badajoz','06',150),('Mérida','06',60),('Cáceres','10',96),('Plasencia','10',40),
 ('Córdoba','14',322),('Jaén','23',111),('Linares','23',57),('Granada','18',230),('Motril','18',59),
 ('Almería','04',200),('Roquetas de Mar','04',100),('Ejido','04',84),('Huelva','21',143),
 ('Palma','07',419),('Calvià','07',51),('Eivissa','07',50),('Manacor','07',44),
 ('Palmas de Gran Canaria','35',378),('Telde','35',102),('Arrecife','35',64),
 ('Santa Cruz de Tenerife','38',208),('Laguna','38',158),('Arona','38',82),
 ('Ceuta','51',83),('Melilla','52',86),
]
# déficit 2021-2025 (~750.000). 52,5 % en las 6 provincias (Banco de España)
SIX = ['28', '08', '46', '03', '30', '29']
SIX_SHARE = {'28': .17, '08': .135, '46': .06, '03': .065, '30': .035, '29': .06}  # suma .525
OTHER_DEF = {'07': .07, '35': .045, '38': .04, '41': .045, '11': .03, '17': .025, '43': .025, '12': .02,
             '04': .02, '18': .02, '45': .02, '19': .015, '50': .02, '48': .015, '01': .01, '20': .01,
             '31': .01, '39': .01, '47': .005}

UNIT = 1500.0  # viviendas por casita
PARCEL_UNIT = 2000.0  # viviendas por parcela roja


def norm(s):
    s = unicodedata.normalize('NFD', s.lower())
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn')

# localizar ciudades
by_prov = {}
for m in munis:
    by_prov.setdefault(m['prov'], []).append(m)
city_rec = []
for name, pid, pop in CITIES:
    cand = [m for m in by_prov.get(pid, []) if norm(name) in norm(m['name'])]
    if not cand:
        cand = [m for m in by_prov.get(pid, []) if norm(m['name']).split('/')[0].strip() in norm(name)]
    if not cand:
        print('!! sin municipio:', name)
        continue
    m = min(cand, key=lambda m: len(m['name']))
    m['city'] = True
    c = m['geom'].representative_point() if name not in ('Madrid',) else m['geom'].centroid
    if name == 'Madrid':
        c = Point(*proj(-3.7038, 40.4168))
    city_rec.append(dict(name=name, prov=pid, pop=pop, x=c.x, y=c.y, muni=m))

# ---------------------------------------------------------------- casa a casa
land = unary_union([p['geom'] for p in provs.values()])
land_in = prep(land.buffer(-0.9))
prov_in = {k: prep(v['geom'].buffer(-1.3)) for k, v in provs.items()}
CELL = 2.0
occ = set()

def cell_of(x, y):
    return (int(math.floor(x / CELL)), int(math.floor(y / CELL)))

houses = []  # dict(x,y,rot,units,h,kind,prov,vac,city,village)


def place_cluster(cx, cy, pid, n_units, core, rot, tag, max_r=60, dens_pow=1.0, block=True, village=None):
    """Coloca n_units casitas alrededor de (cx,cy) sobre celdas libres."""
    placed = 0
    r = 0
    cc = cell_of(cx, cy)
    tries = 0
    ring_cells = []
    R = 1
    while placed < n_units and R < max_r / CELL:
        cand = []
        for i in range(cc[0] - R, cc[0] + R + 1):
            for j in range(cc[1] - R, cc[1] + R + 1):
                if max(abs(i - cc[0]), abs(j - cc[1])) != R and R > 1:
                    continue
                cand.append((i, j))
        rng.shuffle(cand)
        for (i, j) in cand:
            if placed >= n_units:
                break
            if (i, j) in occ:
                continue
            x = (i + .5) * CELL + rng.uniform(-.06, .06)
            y = (j + .5) * CELL + rng.uniform(-.06, .06)
            d = math.hypot(x - cx, y - cy)
            # densidad decreciente: probabilidad de saltar la celda
            if R > 2 and rng.random() < min(.85, (d / (core * 2.2)) ** 2 * .5):
                continue
            if not prov_in[pid].contains(Point(x, y)):
                continue
            occ.add((i, j))
            # bloques altos en el centro de las ciudades grandes
            u = 1
            if block and d < core:
                u = 1 + int(rng.random() * 3.2 * (1 - d / core) + (1.5 if d < core * .35 else 0))
                u = min(u, n_units - placed)
            houses.append(dict(x=x, y=y, rot=rot + rng.choice([0, 0, 0, math.pi / 2]) + rng.uniform(-.05, .05),
                               units=u, prov=pid, tag=tag, d=d, village=village))
            placed += u
        R += 1
    return placed

dw = {}
for pid, (pop, vac) in P.items():
    dw[pid] = pop * 1000 * 0.47 / (1 - vac)
scale = 26.6e6 / sum(dw.values())
for k in dw:
    dw[k] *= scale

city_units = {}
for c in sorted(city_rec, key=lambda c: -c['pop']):
    pop, vac = P[c['prov']]
    u = int(round(c['pop'] * 1000 * .47 / (1 - vac * .55) * scale / UNIT))
    core = math.sqrt(u) * CELL * .55
    rot = rng.uniform(0, math.pi / 2)
    got = place_cluster(c['x'], c['y'], c['prov'], u, core, rot, 'city:' + c['name'], max_r=70)
    city_units[c['prov']] = city_units.get(c['prov'], 0) + got
    c['units'] = got

# calle protagonista (plano 0): dos hileras de casitas en Arévalo (Ávila)
street = None
cand = [m for m in by_prov['05'] if norm(m['name']) == 'arevalo']
if cand:
    m = cand[0]; m['hero'] = True
    p = m['geom'].representative_point()
    th = 0.62  # dirección de la calle
    ux, uy = math.cos(th), math.sin(th)
    vx, vy = -uy, ux
    # liberar celdas alrededor
    cc = cell_of(p.x, p.y)
    for i in range(cc[0] - 10, cc[0] + 11):
        for j in range(cc[1] - 10, cc[1] + 11):
            occ.add((i, j))
    i0 = len(houses)
    srng = random.Random(11)
    pattern = [0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1]
    for k in range(-4, 10):
        for side in (-1, 1):
            along = k * 2.05 + (0.5 if side > 0 else 0)
            off = side * 2.25
            x = p.x + ux * along + vx * off
            y = p.y + uy * along + vy * off
            rot = th + math.pi / 2 + srng.uniform(-.04, .04)
            houses.append(dict(x=x, y=y, rot=rot, units=1, prov='05', tag='street', d=0, village=None))
    street = dict(x=p.x, y=p.y, th=th, i0=i0, i1=len(houses))

# pueblos héroe (escena 6) en Zamora: 4 pueblos de 12-18 casas con iglesia
HERO = ['Fermoselle', 'Puebla de Sanabria', 'Villalpando', 'Alcañices', 'Muelas del Pan', 'Tábara']
hero_villages = []
for name in HERO:
    cand = [m for m in by_prov['49'] if norm(name) == norm(m['name'])]
    if not cand:
        print('!! héroe no encontrado', name); continue
    m = cand[0]; m['hero'] = True
    p = m['geom'].representative_point()
    n = rng.randint(13, 18)
    vid = len(hero_villages)
    before = len(houses)
    place_cluster(p.x, p.y, '49', n, 1.0, rng.uniform(0, 1.5), 'hero:' + name, max_r=9, block=False, village=vid)
    for h in houses[before:]:
        h['x'] = p.x + (h['x'] - p.x) * 0.8
        h['y'] = p.y + (h['y'] - p.y) * 0.8
    hero_villages.append(dict(name=name, x=p.x, y=p.y, i0=before, i1=len(houses)))

# resto rural: pueblos de 2-12 casas en municipios
for pid in P:
    total_u = int(round(dw[pid] / UNIT))
    rest = total_u - city_units.get(pid, 0) - sum(h['units'] for h in houses if h['prov'] == pid and h['tag'].startswith('hero'))
    ms = [m for m in by_prov.get(pid, []) if not m.get('city') and not m.get('hero')]
    if rest <= 0 or not ms:
        continue
    rng.shuffle(ms)
    w = nrng.lognormal(0, .8, len(ms))
    w = w / w.sum() * rest
    carry = 0.0
    for m, wi in zip(ms, w):
        carry += wi
        n = int(carry)
        if n < 1:
            continue
        carry -= n
        p = m['geom'].representative_point()
        place_cluster(p.x, p.y, pid, n, 1.2, rng.uniform(0, 1.5), 'rural', max_r=14, block=n > 25)

# ---------------------------------------------------------------- vacías
# en cada provincia: tasa rural ≈ 2,3× la urbana; resolver para la tasa provincial
for pid, (pop, vac) in P.items():
    hs = [h for h in houses if h['prov'] == pid]
    if not hs:
        continue
    U = sum(h['units'] for h in hs)
    Ur = sum(h['units'] for h in hs if not h['tag'].startswith('city'))
    Uc = U - Ur
    k = 1.35
    rc = vac * U / (Uc + k * Ur)
    for h in hs:
        rate = rc * (k if not h['tag'].startswith('city') else 1)
        if h['tag'].startswith('hero'):
            rate = .78
        if h['tag'] == 'street':
            rate = .45
        if h['units'] > 1:
            rate *= .7
        h['vac'] = 1 if rng.random() < min(rate, .92) else 0

# ---------------------------------------------------------------- parcelas
parcels = []
DEF = dict(SIX_SHARE); DEF.update(OTHER_DEF)
tot_def = 750000
for pid, share in DEF.items():
    n = int(round(tot_def * share / PARCEL_UNIT))
    cs = sorted([c for c in city_rec if c['prov'] == pid], key=lambda c: -c['pop'])
    if not cs:
        continue
    wts = np.array([c['pop'] for c in cs], float) ** .8
    wts /= wts.sum()
    alloc = np.floor(wts * n).astype(int)
    alloc[0] += n - alloc.sum()
    for c, a in zip(cs, alloc):
        if a <= 0:
            continue
        # celdas libres en la periferia de la ciudad
        cc = cell_of(c['x'], c['y'])
        placed = 0
        for R in range(1, 90):
            if placed >= a:
                break
            cand = [(i, j) for i in range(cc[0] - R, cc[0] + R + 1) for j in range(cc[1] - R, cc[1] + R + 1)
                    if max(abs(i - cc[0]), abs(j - cc[1])) == R]
            rng.shuffle(cand)
            for (i, j) in cand:
                if placed >= a:
                    break
                if (i, j) in occ:
                    continue
                # pegada a lo construido
                near = sum(((i + di, j + dj) in occ) for di in (-1, 0, 1) for dj in (-1, 0, 1))
                if near < 2 or rng.random() < .35:
                    continue
                x = (i + .5) * CELL; y = (j + .5) * CELL
                if not prov_in[pid].contains(Point(x, y)):
                    continue
                occ.add((i, j))
                parcels.append(dict(x=x, y=y, rot=rng.uniform(-.08, .08), prov=pid, city=c['name'],
                                    d=math.hypot(x - c['x'], y - c['y'])))
                placed += 1

# ---------------------------------------------------------------- salida
def poly_out(g, inset=0.28):
    g = g.buffer(-inset, join_style=2).simplify(0.12)
    gs = [g] if isinstance(g, Polygon) else list(getattr(g, 'geoms', []))
    out = []
    for p in gs:
        if p.area < 1.0:
            continue
        out.append(dict(ext=[list(map(lambda v: round(v, 3), c)) for c in p.exterior.coords[:-1]],
                        holes=[[list(map(lambda v: round(v, 3), c)) for c in r.coords[:-1]] for r in p.interiors]))
    return out

data = dict(
    unit=UNIT,
    provinces={k: dict(name=v['name'], polys=poly_out(v['geom']),
                       c=[v['geom'].representative_point().x, v['geom'].representative_point().y],
                       bbox=list(v['geom'].bounds)) for k, v in provs.items()},
    houses=[[round(h['x'], 3), round(h['y'], 3), round(h['rot'], 3), h['units'], int(h['prov']), h['vac'],
             1 if h['tag'].startswith('city') else (2 if h['tag'].startswith('hero') else (3 if h['tag'] == 'street' else 0)),
             -1 if h['village'] is None else h['village']] for h in houses],
    parcels=[[round(p['x'], 3), round(p['y'], 3), round(p['rot'], 3), int(p['prov'])] for p in parcels],
    cities={c['name']: [round(c['x'], 2), round(c['y'], 2), c['prov'], c.get('units', 0)] for c in city_rec},
    hero_villages=hero_villages,
    street=street,
    land_bbox=list(land.bounds),
)
json.dump(data, open(OUT, 'w'))
U = sum(h['units'] for h in houses)
V = sum(h['units'] for h in houses if h['vac'])
print('casas', len(houses), 'unidades', U, 'vacías %.1f%%' % (100 * V / U), 'parcelas', len(parcels))
for pid in ['32', '27', '28', '08', '49']:
    hs = [h for h in houses if h['prov'] == pid]
    u = sum(h['units'] for h in hs); v = sum(h['units'] for h in hs if h['vac'])
    print(pid, provs[pid]['name'], len(hs), u, '%.1f%%' % (100 * v / max(u, 1)))
rur = [h for h in houses if not h['tag'].startswith('city')]
print('vacías en rural (pueblos) %.1f%%' % (100 * sum(h['units'] for h in rur if h['vac']) / V))
six = sum(1 for p in parcels if str(p['prov']).zfill(2) in SIX)
print('parcelas en las 6: %.1f%%' % (100 * six / len(parcels)))
print('bbox', land.bounds)
