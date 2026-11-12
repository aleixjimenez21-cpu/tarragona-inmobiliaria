// Renderiza la destacada «About».
//   node render.js stills [n...]   → fijos (estado final de cada historia)
//   node render.js video  [n...]   → MP4 1080×1920 30 fps + fijo
// Salida: ../ (carpeta highlight-about)
const { chromium } = require("playwright");
const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");

const MODE = process.argv[2] || "stills";
const ONLY = process.argv.slice(3).map(Number);
const FPS = 30;
const OUT = path.resolve(__dirname, "..");
const TMP = process.env.TMPDIR_RENDER || path.join(__dirname, ".tmp");
fs.mkdirSync(TMP, { recursive: true });

const NAMES = {
  1: "portada", 2: "origen", 3: "lo-que-vi", 4: "prospectus",
  5: "enfoque", 6: "hacia-donde", 7: "hablemos",
};

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  const list = ONLY.length ? ONLY : [1, 2, 3, 4, 5, 6, 7];
  for (const n of list) {
    const base = `${String(n).padStart(2, "0")}-${NAMES[n]}`;
    await page.goto("file://" + path.join(__dirname, "story.html") + "?n=" + n);
    await page.evaluate(() => window.ready);
    const dur = await page.evaluate(() => window.DURATION);

    // fijo: estado final, sin pulso del punto
    await page.evaluate((t) => window.render(t), dur - 0.5);
    const png = path.join(TMP, base + ".png");
    await page.screenshot({ path: png });
    await new Promise((res, rej) => {
      const p = spawn("ffmpeg", ["-y", "-loglevel", "error", "-i", png, "-q:v", "1", "-qmin", "1", path.join(OUT, base + ".jpg")]);
      p.on("close", (c) => (c ? rej(new Error("ffmpeg jpg")) : res()));
    });
    console.log("still", base);

    if (MODE !== "video") continue;
    const ff = spawn("ffmpeg", [
      "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(FPS), "-i", "-",
      "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
      "-shortest", "-map", "0:v", "-map", "1:a",
      "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-maxrate", "14M", "-bufsize", "28M", "-pix_fmt", "yuv420p",
      "-profile:v", "high", "-level", "4.2", "-r", String(FPS), "-g", String(FPS),
      "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
      path.join(OUT, base + ".mp4"),
    ], { stdio: ["pipe", "inherit", "inherit"] });
    const frames = Math.round(dur * FPS);
    for (let f = 0; f < frames; f++) {
      await page.evaluate((t) => window.render(t), f / FPS);
      const buf = await page.screenshot({ type: "png" });
      if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once("drain", r));
    }
    ff.stdin.end();
    await new Promise((res) => ff.on("close", res));
    console.log("video", base, frames, "frames");
  }
  await browser.close();
})();
