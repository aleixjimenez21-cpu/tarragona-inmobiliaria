# Audio: voz de estudio sin eco

## Cadena (prep_audio.py + build_audio.py)
1. **WPE multicanal** (nara_wpe: 20 taps, retardo 3, 3 iteraciones, STFT 1536/384 a 48 kHz) sobre el **estéreo
   original** del móvil (los iPhone graban con 2 micrófonos): quita las reflexiones de la sala.
2. **DeepFilterNet 3** sin límite de atenuación y con post-filtro (`deep-filter -D -a 100 --pf`); `-D` compensa
   la latencia (sin él el audio se desplaza 30 ms del vídeo).
3. Paso alto 80 Hz (24 dB/oct), EQ −3 dB a 320 Hz (caja), +1 dB a 140 Hz, +3 dB a 3,6 kHz (presencia),
   +1,5 dB shelf a 9,5 kHz.
4. Etapa de ganancia a −20 LUFS → de-esser → compresión 2,5:1 (≈3 dB de reducción) → limitador.
5. Mezcla con música (−23 dB bajo la voz, ducking) y efectos → loudnorm lineal en dos pasadas a **−14 LUFS,
   true peak −1,5 dBTP**.

## Análisis (`reverb_analysis.py`)
Mide en cada final de frase seguido de pausa la cola de reverberación (dB 40-200 ms después) y un RT60 equivalente,
y la confianza de Whisper (detecta artefactos). Uso:
`python3 <skill>/scripts/reverb_analysis.py original=work/audio/re_in final=work/audio/df_wpe20_pf`
Resultados típicos en una oficina vacía: original RT60 ≈ 1,0 s y cola −13 dB → final 0,2-0,3 s y −43/−48 dB, con el
mismo texto reconocido. Si la confianza de Whisper baja mucho o cambia el texto, hay artefactos: vuelve a una
opción más suave (DeepFilterNet `-a 40` sin WPE).

## Qué NO usar
- **resemble-enhance** (modo enhance) en CPU: alucina (Whisper oía "Gracias por ver este vídeo" donde se decía otra
  cosa). Su modo denoise es aceptable pero peor que DeepFilterNet.
- Mucha compresión: con umbral bajo la voz suena aplastada (LRA < 2). Apunta a ~3 dB de reducción.

## Antes / después para el cliente
```bash
ffmpeg -i work/audio/voice_cut_raw.wav -t 10 -af "loudnorm=I=-14:TP=-1.5" -ac 2 work/antes.wav
ffmpeg -i work/audio/final_audio.wav -t 10 work/despues.wav
ffmpeg -i work/antes.wav -i work/despues.wav -filter_complex "anullsrc=r=48000:cl=stereo,atrim=0:0.8[s];[0:a][s][1:a]concat=n=3:v=0:a=1" output/antes_despues_10s.wav
```
