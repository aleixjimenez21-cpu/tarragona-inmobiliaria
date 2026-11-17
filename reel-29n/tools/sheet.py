import sys
from PIL import Image
# uso: sheet.py out.jpg cols img1 img2 ...
out, cols, fs = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
ims = [Image.open(f).resize((360, 640)) for f in fs]
rows = (len(ims) + cols - 1) // cols
s = Image.new('RGB', (360 * cols, 640 * rows))
for i, im in enumerate(ims): s.paste(im, (360 * (i % cols), 640 * (i // cols)))
s.save(out, quality=90)
