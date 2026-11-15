import { loadFont as loadBebas } from '@remotion/google-fonts/BebasNeue';
import { loadFont as loadMontserrat } from '@remotion/google-fonts/Montserrat';

const bebas = loadBebas('normal', { weights: ['400'], subsets: ['latin'] });
const mont = loadMontserrat('normal', { weights: ['600', '900'], subsets: ['latin'] });

export const BEBAS = bebas.fontFamily;
export const MONT = mont.fontFamily;
