"""Convierte clips de apoyo (b-roll) a 1080x1920, 30 fps, recorte centrado tipo "cover", con enfoque suave,
y genera una hoja de contactos para elegirlos.
Uso: python3 <skill>/scripts/prep_broll.py [carpeta_origen=input/broll]   ->  work/clips/<nombre>.mp4 + work/clips/hoja_contactos.jpg"""
import sys, os, glob, subprocess
from PIL import Image, ImageDraw
src = sys.argv[1] if len(sys.argv) > 1 else "input/broll"
os.makedirs("work/clips", exist_ok=True)
files = sorted(f for f in glob.glob(os.path.join(src, "*")) if f.lower().endswith((".mp4", ".mov", ".m4v", ".webm", ".mkv")))
vf = "fps=30,scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,unsharp=5:5:0.3:5:5:0"
for f in files:
    out = os.path.join("work/clips", os.path.splitext(os.path.basename(f))[0] + ".mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f, "-vf", vf, "-an", "-c:v", "libx264", "-crf", "14", "-preset", "slow", "-pix_fmt", "yuv420p", out], check=True)
    print(out)
clips = sorted(glob.glob("work/clips/*.mp4"))
if clips:
    W, H = 270, 480; cols = 6; rows = (len(clips) + cols - 1) // cols
    sheet = Image.new("RGB", (W * cols, (H + 34) * rows), (15, 15, 15))
    for i, c in enumerate(clips):
        d = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", c]))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(d / 2), "-i", c, "-frames:v", "1", "/tmp/_cs.png"])
        x, y = (i % cols) * W, (i // cols) * (H + 34)
        sheet.paste(Image.open("/tmp/_cs.png").convert("RGB").resize((W, H)), (x, y + 34))
        ImageDraw.Draw(sheet).text((x + 6, y + 8), f"{os.path.basename(c)[:-4]} {d:.1f}s", fill=(240, 240, 240))
    sheet.save("work/clips/hoja_contactos.jpg", quality=88)
    print("hoja de contactos: work/clips/hoja_contactos.jpg")
