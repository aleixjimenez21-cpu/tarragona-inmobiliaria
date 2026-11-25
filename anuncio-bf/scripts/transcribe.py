import sys, json
from faster_whisper import WhisperModel
import soundfile as sf, numpy as np
m = WhisperModel(sys.argv[1], device="cpu", compute_type="int8", cpu_threads=4)
out = {}
for t in ["43493248","9ba76478","a54f3308","eb7c3ce3"]:
    segs, info = m.transcribe(sf.read(f"audio/w16_{t}.wav",dtype="float32")[0], language="es", word_timestamps=True, beam_size=5, vad_filter=False,
        initial_prompt="Prospectus, tour virtual, promotora, promoción, Black Friday, inmobiliarias, sobre plano.")
    words=[]; text=""
    for s in segs:
        text += s.text
        for w in s.words: words.append({"w":w.word,"s":round(w.start,3),"e":round(w.end,3),"p":round(w.probability,3)})
    out[t]={"text":text.strip(),"words":words}
    print(t, "|", text.strip(), flush=True)
json.dump(out, open(f"transcript_{sys.argv[1].replace('/','_')}.json","w"), ensure_ascii=False, indent=1)
