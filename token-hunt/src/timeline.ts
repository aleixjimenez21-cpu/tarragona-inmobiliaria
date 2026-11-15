// ⚠️ ARCHIVO GENERADO por scripts/build_timeline.mjs — no editar a mano.
// Fuente de audio: public/audio.mp3 · 119.968 BPM · offset 0.00246s
export const FPS = 30;
export const WIDTH = 1080;
export const HEIGHT = 1920;
export const TOTAL_FRAMES = 975;
export const BPM = 119.968;
export const BEAT_FRAMES = 15.0039;
export const BEATS: number[] = [0,15,30,45,60,75,90,105,120,135,150,165,180,195,210,225,240,255,270,285,300,315,330,345,360,375,390,405,420,435,450,465,480,495,510,525,540,555,570,585,600,615,630,645,660,675,690,705,720,735,750,765,780,795,810,825,840,855,870,885,900,915,930,945,960,975];

export type Bg = 'black' | 'gray';
export type TransitionKind = 'cut' | 'flash' | 'glitch' | 'whip';
export interface SceneTiming {
  id: string;
  bg: Bg;
  transition: TransitionKind;
  /** frames absolutos */
  start: number;
  end: number;
  duration: number;
  /** cues en frames ABSOLUTOS */
  cues: Record<string, number>;
  /** golpes (zoom-punch + shake), frames absolutos */
  hits: number[];
}

export const SCENES: SceneTiming[] = [
 {
  "id": "intro",
  "bg": "black",
  "transition": "cut",
  "start": 0,
  "cues": {
   "in": 0
  },
  "hits": [],
  "end": 15,
  "duration": 15
 },
 {
  "id": "giveUp",
  "bg": "black",
  "transition": "flash",
  "start": 15,
  "cues": {
   "giveUp": 15,
   "q": 45
  },
  "hits": [
   15,
   45
  ],
  "end": 60,
  "duration": 45
 },
 {
  "id": "chests",
  "bg": "black",
  "transition": "flash",
  "start": 60,
  "cues": {
   "c1": 60,
   "c2": 75,
   "c3": 90,
   "c4": 105
  },
  "hits": [],
  "end": 120,
  "duration": 60
 },
 {
  "id": "stillNo",
  "bg": "gray",
  "transition": "glitch",
  "start": 120,
  "cues": {
   "title": 120,
   "sub": 135
  },
  "hits": [],
  "end": 150,
  "duration": 30
 },
 {
  "id": "oneMore",
  "bg": "black",
  "transition": "glitch",
  "start": 150,
  "cues": {
   "one": 150,
   "more": 165,
   "chest": 173
  },
  "hits": [
   173
  ],
  "end": 180,
  "duration": 30
 },
 {
  "id": "dontGiveUp",
  "bg": "black",
  "transition": "flash",
  "start": 180,
  "cues": {
   "light": 180,
   "man": 195,
   "title": 210,
   "sub": 225
  },
  "hits": [],
  "end": 240,
  "duration": 60
 },
 {
  "id": "days",
  "bg": "black",
  "transition": "flash",
  "start": 240,
  "cues": {
   "d1": 240,
   "d2": 255,
   "d3": 270,
   "d4": 285
  },
  "hits": [
   240
  ],
  "end": 300,
  "duration": 60
 },
 {
  "id": "am347",
  "bg": "gray",
  "transition": "whip",
  "start": 300,
  "cues": {
   "time": 300,
   "bubble": 315,
   "sub": 330
  },
  "hits": [],
  "end": 360,
  "duration": 60
 },
 {
  "id": "am349",
  "bg": "gray",
  "transition": "cut",
  "start": 360,
  "cues": {
   "time": 360,
   "sub": 375
  },
  "hits": [],
  "end": 390,
  "duration": 30
 },
 {
  "id": "odds",
  "bg": "black",
  "transition": "glitch",
  "start": 390,
  "cues": {
   "a": 390,
   "label": 405,
   "b": 420
  },
  "hits": [
   420
  ],
  "end": 435,
  "duration": 45
 },
 {
  "id": "onlyNeed",
  "bg": "gray",
  "transition": "whip",
  "start": 435,
  "cues": {
   "need": 435,
   "one": 450
  },
  "hits": [
   450
  ],
  "end": 465,
  "duration": 30
 },
 {
  "id": "giveUpQ",
  "bg": "black",
  "transition": "glitch",
  "start": 465,
  "cues": {
   "q": 465
  },
  "hits": [
   465
  ],
  "end": 480,
  "duration": 15
 },
 {
  "id": "nah",
  "bg": "black",
  "transition": "flash",
  "start": 480,
  "cues": {
   "nah": 480
  },
  "hits": [
   480
  ],
  "end": 510,
  "duration": 30
 },
 {
  "id": "illFind",
  "bg": "black",
  "transition": "cut",
  "start": 510,
  "cues": {
   "ill": 510,
   "find": 525,
   "coin": 533
  },
  "hits": [
   525
  ],
  "end": 540,
  "duration": 30
 },
 {
  "id": "never",
  "bg": "gray",
  "transition": "glitch",
  "start": 540,
  "cues": {
   "never": 540,
   "giving": 555,
   "up": 570
  },
  "hits": [
   540,
   570
  ],
  "end": 600,
  "duration": 60
 },
 {
  "id": "empty",
  "bg": "gray",
  "transition": "cut",
  "start": 600,
  "cues": {
   "c1": 600,
   "s1": 608,
   "c2": 615,
   "s2": 623,
   "c3": 630,
   "s3": 638,
   "c4": 645,
   "s4": 653
  },
  "hits": [
   608,
   623,
   638,
   653
  ],
  "end": 660,
  "duration": 60
 },
 {
  "id": "now",
  "bg": "black",
  "transition": "glitch",
  "start": 660,
  "cues": {
   "now": 660
  },
  "hits": [
   660
  ],
  "end": 675,
  "duration": 15
 },
 {
  "id": "list",
  "bg": "black",
  "transition": "cut",
  "start": 675,
  "cues": {
   "m": 675,
   "d": 690,
   "o": 705
  },
  "hits": [
   705
  ],
  "end": 720,
  "duration": 45
 },
 {
  "id": "outThere",
  "bg": "black",
  "transition": "flash",
  "start": 720,
  "cues": {
   "coin": 720,
   "its": 735,
   "out": 750
  },
  "hits": [
   720
  ],
  "end": 780,
  "duration": 60
 },
 {
  "id": "climb",
  "bg": "black",
  "transition": "flash",
  "start": 780,
  "cues": {
   "stairs": 780,
   "keep": 795,
   "climbing": 810
  },
  "hits": [
   810
  ],
  "end": 840,
  "duration": 60
 },
 {
  "id": "iCan",
  "bg": "gray",
  "transition": "whip",
  "start": 840,
  "cues": {
   "can": 840,
   "will": 855,
   "must": 870,
   "mustPunch": 885
  },
  "hits": [
   840,
   855,
   870,
   885
  ],
  "end": 900,
  "duration": 60
 },
 {
  "id": "again",
  "bg": "gray",
  "transition": "flash",
  "start": 900,
  "cues": {
   "coin": 900,
   "again1": 915,
   "again2": 930,
   "fade": 945,
   "loop": 960
  },
  "hits": [
   900
  ],
  "end": 975,
  "duration": 75
 }
];

export const sceneById = (id: string): SceneTiming => {
  const s = SCENES.find((x) => x.id === id);
  if (!s) throw new Error('Escena desconocida: ' + id);
  return s;
};
/** cues relativos al inicio de la escena (para usar dentro de <Sequence>) */
export const rel = (id: string): Record<string, number> => {
  const s = sceneById(id);
  return Object.fromEntries(Object.entries(s.cues).map(([k, v]) => [k, v - s.start]));
};
export const ALL_HITS: number[] = SCENES.flatMap((s) => s.hits);
