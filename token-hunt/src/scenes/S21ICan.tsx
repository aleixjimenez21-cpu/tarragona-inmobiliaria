import React from 'react';
import { Stack, Txt } from '../components/Txt';
import { rel } from '../timeline';

// 28,0–30,0 · "I CAN" → "I WILL" → "I MUST" (cada línea más oscura y más grande)
export const S21ICan: React.FC = () => {
  const c = rel('iCan');
  return (
    <Stack gap={46}>
      <Txt at={c.can} size={110} font="mont" color="#A3A3A3" lineHeight={1}>I CAN</Txt>
      <Txt at={c.will} size={142} font="mont" color="#5C5C5C" lineHeight={1}>I WILL</Txt>
      <Txt at={c.must} size={180} font="mont" color="#0A0A0A" lineHeight={1} from={1.8}>I MUST</Txt>
    </Stack>
  );
};
