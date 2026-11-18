"""Renderiza un plano.

uso: python render.py PLANO [--q preview|final] [--step N] [--times t1,t2,...] [--out DIR]
"""
import sys, os, json, time, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import maqueta as M
import shots as S

QUAL = {
    'still':   dict(res=(540, 960), spp=24),
    'preview': dict(res=(270, 480), spp=6),
    'final':   dict(res=(720, 1280), spp=10),
    'cover':   dict(res=(1080, 1920), spp=40),
}


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument('shot')
    ap.add_argument('--q', default='preview')
    ap.add_argument('--step', type=int, default=1)
    ap.add_argument('--times', default='')
    ap.add_argument('--out', default='')
    ap.add_argument('--save-blend', action='store_true')
    ap.add_argument('--meta-only', action='store_true')
    a = ap.parse_args(argv)
    q = QUAL[a.q]
    sc = M.reset()
    M.setup_render(sc, res=q['res'], samples=q['spp'], pct=100)
    cam, fe, (t0, t1), events = S.SHOT_FUNCS[a.shot](sc)
    f0 = S.cut_frame(t0); f1 = S.cut_frame(t1) - 1
    out = a.out or os.path.join(M.ROOT, 'renders', a.shot, a.q)
    os.makedirs(out, exist_ok=True)
    # foco por fotograma
    focus = {}
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        cm = cam.matrix_world
        fwd = -(cm.to_3x3().col[2]).normalized()
        d = (fe.matrix_world.translation - cm.translation).dot(fwd)
        from bpy_extras.object_utils import world_to_camera_view
        v = world_to_camera_view(sc, cam, fe.matrix_world.translation)
        focus[f] = dict(d=d, ts=float(fe.get('ts', 1.0)), lens=cam.data.lens, fx=v.x, fy=1 - v.y)
    json.dump(dict(shot=a.shot, f0=f0, f1=f1, t0=t0, t1=t1, focus=focus, events=events),
              open(os.path.join(out, 'meta.json'), 'w'), indent=0, default=float)
    if a.meta_only:
        return
    if a.save_blend:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, a.shot + '.blend'))
    sc.render.use_overwrite = False
    sc.render.use_placeholder = True
    if a.times:
        sc.render.use_overwrite = True
        sc.render.use_placeholder = False
        for t in [float(x) for x in a.times.split(',')]:
            f = S.cut_frame(t)
            sc.frame_set(f)
            sc.render.filepath = os.path.join(out, 'f_%04d.exr' % f)
            tt = time.time()
            bpy.ops.render.render(write_still=True)
            print('frame', f, 't=%.2f' % t, '%.1fs' % (time.time() - tt), flush=True)
        return
    sc.frame_start, sc.frame_end, sc.frame_step = f0, f1, a.step
    sc.render.filepath = os.path.join(out, 'f_####')
    tt = time.time()
    bpy.ops.render.render(animation=True)
    print('render total %.1fs' % (time.time() - tt))


main()
