import React from 'react';
import { Stack, Txt } from '../components/Txt';
import { C } from '../theme';
import { rel } from '../timeline';

// 5,0–6,0 · "ONE" / "MORE" / "CHEST." palabra a palabra; "CHEST." en amarillo
export const S05OneMore: React.FC = () => {
  const c = rel('oneMore');
  return (
    <Stack>
      <Txt at={c.one} size={380}>ONE</Txt>
      <Txt at={c.more} size={380}>MORE</Txt>
      <Txt at={c.chest} size={380} color={C.gold} from={1.8}>CHEST.</Txt>
    </Stack>
  );
};
