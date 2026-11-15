// Paleta fija + zonas seguras de TikTok
export const C = {
  black: '#0A0A0A',
  gray: '#E6E6E6',
  gold: '#FFC93C',
  goldDeep: '#FF9F1C',
  red: '#E10600',
  white: '#FFFFFF',
  ink: '#0A0A0A',
  mute: '#6E6E6E',
} as const;

/**
 * Zona segura: nada importante en los 250 px de abajo ni en los 180 px de la derecha.
 * Dejamos además margen arriba/izquierda para la UI de TikTok.
 */
export const SAFE = { left: 60, right: 1080 - 180, top: 170, bottom: 1920 - 250 } as const;
export const SAFE_W = SAFE.right - SAFE.left; // 840
export const CX = (SAFE.left + SAFE.right) / 2; // 480 — centro óptico de la zona segura
export const CY = (SAFE.top + SAFE.bottom) / 2; // 920

/** El MISMO glow para todos los textos sobre negro (se tiñe del color del texto). */
export const glowFor = (color: string, k = 1) =>
  `0 0 ${14 * k}px ${color}AA, 0 0 ${42 * k}px ${color}55, 0 0 ${90 * k}px ${color}22`;

export const GOLD_GLOW_FILTER =
  'drop-shadow(0 0 18px rgba(255,201,60,0.75)) drop-shadow(0 0 60px rgba(255,159,28,0.45))';
