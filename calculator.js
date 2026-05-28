// ─────────────────────────────────────────────────────────
//  Calculadora — Aleix Jiménez Real Estate Operator
//  Tarragona · 2025/26  (parámetros actualizados estudio 2026)
// ─────────────────────────────────────────────────────────

// Legacy standalone calculator (DOM IDs: calc-m2, calc-zone, etc.)
// The main quiz engine is in quiz.js — this file is kept for any
// standalone embed that still references the old calc-* IDs.

const ZONES = {
  eixample:  { base: 2125, min: 1850, max: 2450 },
  centre:    { base: 1950, min: 1650, max: 2250 },
  jaume:     { base: 2000, min: 1720, max: 2300 },
  llevant:   { base: 2000, min: 1720, max: 2300 },
  port:      { base: 1900, min: 1600, max: 2200 },
  bonavista: { base: 1480, min: 1250, max: 1750 },
};

const STATE_MULT  = { nueva: 1.22, reformado: 1.15, bueno: 1.00, reformar: 0.82, deteriorado: 0.68 };
const FLOOR_MULT  = { pb_interior: 0.85, pb_jardin: 0.98, entreplanta: 0.90, '1a3': 1.00, alta: 1.04, atico: 1.12, bajo: 0.88, '4a6': 1.04, '7mas': 1.07 };
const BATHS_BONUS = { '1': 0, '2': 0.03, '3': 0.05 };

const RECOMMENDATIONS = {
  'vender-pronto':  (data) =>
    `El mercado de ${data.zoneLabel} absorbe bien la oferta actual. Con un precio ajustado, un plazo de ${data.zone === 'bonavista' ? '60-90' : '35-55'} días es realista. ` +
    `El valor estimado de ${data.saleFormatted} requiere preparación mínima del inmueble. Podemos hablar de estrategia de precio.`,

  'vender-maximo':  (data) =>
    `Para maximizar el precio en ${data.zoneLabel}, considera una reforma selectiva (cocina/baño). ` +
    `El potencial de revalorización es de un +8–15% adicional sobre los ${data.saleFormatted} estimados. ` +
    `Requiere una inversión de 8.000–20.000€ y 2-3 meses. Puedo orientarte si merece la pena en tu caso.`,

  'alquilar':       (data) =>
    `La rentabilidad bruta estimada en ${data.zoneLabel} es del ${data.yieldStr}. ` +
    `Con ${data.rentFormatted}/mes de ingreso, el retorno anual es atractivo si tu horizonte es de más de 3 años. ` +
    `El alquiler de temporada puede mejorar un 30-40% los ingresos. Analizamos juntos qué modalidad te conviene.`,

  'no-se':          (data) =>
    `Con los datos que has introducido, tienes dos caminos claros: vender a ~${data.saleFormatted} en 30-60 días, ` +
    `o generar ${data.rentFormatted}/mes en alquiler (${data.yieldStr} de rentabilidad). ` +
    `La decisión depende de tu situación fiscal, necesidad de liquidez y horizonte temporal. ` +
    `Es exactamente para esto para lo que trabajo.`,

  'default':        (data) =>
    `Tu propiedad en ${data.zoneLabel} tiene un valor estimado de ${data.saleFormatted}. ` +
    `Si quieres una valoración oficial y un análisis completo de opciones, estoy a tu disposición.`,
};

// ─── Helpers ──────────────────────────────────────────────
function eur(n) {
  return new Intl.NumberFormat('es-ES', {
    style: 'currency', currency: 'EUR', maximumFractionDigits: 0,
  }).format(n);
}

function snap(n, step) {
  return Math.round(n / step) * step;
}

// ─── Main calculation ─────────────────────────────────────
function calculatePrice() {
  const m2    = parseFloat(document.getElementById('calc-m2').value);
  const zone  = document.getElementById('calc-zone').value;
  const state = document.getElementById('calc-state').value;
  const floor = document.getElementById('calc-floor').value;
  const baths = document.getElementById('calc-baths').value;

  const hasTerrace  = document.getElementById('calc-terrace').checked;
  const hasParking  = document.getElementById('calc-parking').checked;
  const hasPool     = document.getElementById('calc-pool').checked;
  const hasElevator = document.getElementById('calc-elevator').checked;

  const intent = (typeof currentIntent !== 'undefined') ? currentIntent : 'no-se';

  const errEl = document.getElementById('calc-error');
  if (!zone) { return showErr(errEl, 'Selecciona la zona de la propiedad.'); }
  if (!m2 || m2 < 20 || m2 > 600) { return showErr(errEl, 'Introduce una superficie válida (20–600 m²).'); }
  errEl.classList.add('hidden');

  const z      = ZONES[zone];
  const smult  = STATE_MULT[state]  || 1;
  const fmult  = FLOOR_MULT[floor]  || 1;
  const bbonus = BATHS_BONUS[baths] || 0;

  // Percentage-based extras (100%/85%/70% diminishing)
  const extraPcts = [];
  if (hasTerrace)  extraPcts.push(0.14);
  if (hasPool)     extraPcts.push(0.04);
  if (hasElevator) extraPcts.push(0.03);
  extraPcts.sort((a, b) => b - a);
  const extrasMult = 1 + extraPcts.reduce((acc, p, i) => acc + p * (i === 0 ? 1 : i === 1 ? 0.85 : 0.70), 0);

  let base = snap(m2 * z.base * smult * fmult * (1 + bbonus) * extrasMult, 500);
  let lo   = snap(m2 * z.min  * smult * fmult, 500);
  let hi   = snap(m2 * z.max  * smult * fmult * (1 + bbonus) * extrasMult, 500);

  if (hasParking) { base += 12000; lo += 8000; hi += 16000; }

  // Rental (5.2% gross yield)
  const rent    = snap((base * 0.052) / 12, 25);
  const rentLo  = snap((lo   * 0.048) / 12, 25);
  const rentHi  = snap((hi   * 0.056) / 12, 25);
  const yieldPc = ((rent * 12) / base * 100).toFixed(1);

  const ZONE_LABELS = {
    eixample: 'Eixample / Rambla Nova', centre: 'Centre / Part Alta', jaume: 'Sant Pere i Sant Pau',
    llevant: 'Llevant', port: 'Barris Marítims / Port', bonavista: 'Bonavista',
  };

  const recData = {
    zone, zoneLabel: ZONE_LABELS[zone] || zone,
    saleFormatted: eur(base), rentFormatted: eur(rent),
    yieldStr: yieldPc + '%',
  };

  const recFn = RECOMMENDATIONS[intent] || RECOMMENDATIONS['default'];
  const recommendation = recFn(recData);

  renderResults({ base, lo, hi, rent, rentLo, rentHi, yieldPc, recommendation });
}

function showErr(el, msg) {
  el.textContent = msg;
  el.classList.remove('hidden');
}

function renderResults({ base, lo, hi, rent, rentLo, rentHi, yieldPc, recommendation }) {
  document.getElementById('calc-placeholder').classList.add('hidden');

  const panel = document.getElementById('calc-results');
  panel.classList.remove('hidden');
  panel.style.display = 'flex';

  document.getElementById('result-sale').textContent       = eur(base);
  document.getElementById('result-sale-range').textContent = `Horquilla: ${eur(lo)} – ${eur(hi)}`;
  document.getElementById('result-rent').textContent       = eur(rent) + '/mes';
  document.getElementById('result-rent-range').textContent = `Horquilla: ${eur(rentLo)} – ${eur(rentHi)}/mes`;
  document.getElementById('result-yield').textContent      = yieldPc + '%';
  document.getElementById('result-recommendation').textContent = recommendation;

  panel.style.opacity = '0';
  panel.style.transform = 'translateY(12px)';
  panel.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      panel.style.opacity = '1';
      panel.style.transform = 'none';
    });
  });

  if (window.innerWidth < 1024) {
    setTimeout(() => {
      document.getElementById('calc-results-panel').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 120);
  }
}
