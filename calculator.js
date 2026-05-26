// ─────────────────────────────────────────────────────────
//  Calculadora — Aleix Jiménez Real Estate Operator
//  Tarragona · 2024/25
// ─────────────────────────────────────────────────────────

const ZONES = {
  eixample:  { base: 2050, min: 1850, max: 2300 },
  centre:    { base: 1750, min: 1550, max: 2000 },
  jaume:     { base: 1900, min: 1700, max: 2100 },
  llevant:   { base: 1420, min: 1200, max: 1650 },
  port:      { base: 1600, min: 1400, max: 1850 },
  bonavista: { base: 1050, min: 850,  max: 1280 },
};

const STATE_MULT  = { reformado: 1.15, bueno: 1.00, reformar: 0.80 };
const FLOOR_MULT  = { bajo: 0.90, medio: 1.00, alto: 1.05, atico: 1.13 };
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

  // Validation
  const errEl = document.getElementById('calc-error');
  if (!zone) { return showErr(errEl, 'Selecciona la zona de la propiedad.'); }
  if (!m2 || m2 < 20 || m2 > 600) { return showErr(errEl, 'Introduce una superficie válida (20–600 m²).'); }
  errEl.classList.add('hidden');

  // Base price
  const z      = ZONES[zone];
  const smult  = STATE_MULT[state]  || 1;
  const fmult  = FLOOR_MULT[floor]  || 1;
  const bbonus = BATHS_BONUS[baths] || 0;

  let base = m2 * z.base * smult * fmult * (1 + bbonus);
  let lo   = m2 * z.min  * smult * fmult;
  let hi   = m2 * z.max  * smult * fmult * (1 + bbonus);

  // Percentage extras
  let em = 1;
  if (hasTerrace)  em += 0.05;
  if (hasPool)     em += 0.03;
  if (hasElevator) em += 0.03;
  base *= em; lo *= em; hi *= em;

  // Fixed parking
  if (hasParking) { base += 12000; lo += 8000; hi += 16000; }

  base = snap(base, 500);
  lo   = snap(lo,   500);
  hi   = snap(hi,   500);

  // Rental (5.2% gross yield)
  const rent    = snap((base * 0.052) / 12, 25);
  const rentLo  = snap((lo   * 0.048) / 12, 25);
  const rentHi  = snap((hi   * 0.056) / 12, 25);
  const yieldPc = ((rent * 12) / base * 100).toFixed(1);

  const ZONE_LABELS = {
    eixample: 'Eixample', centre: 'Part Alta/Centre', jaume: 'Jaume I',
    llevant: 'Llevant', port: 'Port/Salut', bonavista: 'Bonavista',
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

  // Fade-in animation
  panel.style.opacity = '0';
  panel.style.transform = 'translateY(12px)';
  panel.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      panel.style.opacity = '1';
      panel.style.transform = 'none';
    });
  });

  // Mobile scroll
  if (window.innerWidth < 1024) {
    setTimeout(() => {
      document.getElementById('calc-results-panel').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 120);
  }
}
