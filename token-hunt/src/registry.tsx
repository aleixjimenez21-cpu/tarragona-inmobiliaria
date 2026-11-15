import React from 'react';
import { S01Intro } from './scenes/S01Intro';
import { S02GiveUp } from './scenes/S02GiveUp';
import { S03Chests } from './scenes/S03Chests';
import { S04StillNo } from './scenes/S04StillNo';
import { S05OneMore } from './scenes/S05OneMore';
import { S06DontGiveUp } from './scenes/S06DontGiveUp';
import { S07Days } from './scenes/S07Days';
import { S08Am347 } from './scenes/S08Am347';
import { S09Am349 } from './scenes/S09Am349';
import { S10Odds } from './scenes/S10Odds';
import { S11OnlyNeed } from './scenes/S11OnlyNeed';
import { S12GiveUpQ } from './scenes/S12GiveUpQ';
import { S13Nah } from './scenes/S13Nah';
import { S14IllFind } from './scenes/S14IllFind';
import { S15Never } from './scenes/S15Never';
import { S16Empty } from './scenes/S16Empty';
import { S17Now } from './scenes/S17Now';
import { S18List } from './scenes/S18List';
import { S19OutThere } from './scenes/S19OutThere';
import { S20Climb } from './scenes/S20Climb';
import { S21ICan } from './scenes/S21ICan';
import { S22Again } from './scenes/S22Again';

/** id de escena (timeline) → componente + intensidad del shake */
export const REGISTRY: Record<string, { C: React.FC; shake?: number; leak?: boolean; drift?: number }> = {
  intro: { C: S01Intro, drift: 0 },
  giveUp: { C: S02GiveUp },
  chests: { C: S03Chests },
  stillNo: { C: S04StillNo },
  oneMore: { C: S05OneMore },
  dontGiveUp: { C: S06DontGiveUp, leak: true },
  days: { C: S07Days, shake: 0.6 },
  am347: { C: S08Am347 },
  am349: { C: S09Am349 },
  odds: { C: S10Odds },
  onlyNeed: { C: S11OnlyNeed, shake: 1.2 },
  giveUpQ: { C: S12GiveUpQ, shake: 1.5 },
  nah: { C: S13Nah, shake: 2.4 },
  illFind: { C: S14IllFind },
  never: { C: S15Never, shake: 1.2 },
  empty: { C: S16Empty, shake: 1.3 },
  now: { C: S17Now, shake: 1.6, leak: true },
  list: { C: S18List },
  outThere: { C: S19OutThere, leak: true },
  climb: { C: S20Climb, shake: 0.7, leak: true },
  iCan: { C: S21ICan, shake: 0.8 },
  again: { C: S22Again, shake: 0.6, drift: 0 },
};
