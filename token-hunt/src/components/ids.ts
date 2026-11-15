import { useId } from 'react';
/** id seguro para url(#...) en SVG */
export const useSvgId = (prefix: string) => prefix + useId().replace(/[^a-zA-Z0-9]/g, '');
