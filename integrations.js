// ═══════════════════════════════════════════════════════════
//  INTEGRATIONS — Aleix Jiménez Real Estate Operator
//  Connect to Webhook · Google Sheets · Make.com · Email · CRM
//
//  HOW TO USE:
//  1. Set enabled: true for each integration you want to activate
//  2. Fill in the corresponding URL / key / ID
//  3. Everything runs automatically on quiz submission (Step 5)
// ═══════════════════════════════════════════════════════════

const INTEGRATIONS = {

  // ── Webhook genérico (Make.com, Zapier, n8n, etc.) ────────
  webhook: {
    enabled: false,
    url: '',  // Ej: 'https://hook.eu1.make.com/xxxxxxxx'
    // Make.com: crea un scenario con trigger "Custom Webhook"
    // Zapier: usa "Webhooks by Zapier" como trigger
  },

  // ── Google Sheets via Apps Script ────────────────────────
  googleSheets: {
    enabled: false,
    url: '',  // URL de tu Google Apps Script Web App (Deploy → Execute as: Me)
    // Guía: crea un Apps Script con doPost(e) que escribe en una hoja
  },

  // ── EmailJS (email directo desde el navegador) ────────────
  emailjs: {
    enabled: false,
    publicKey:  '',  // Account → API Keys
    serviceId:  '',  // Email Services → Service ID
    templateId: '',  // Email Templates → Template ID
    // Documentación: https://www.emailjs.com/docs/
  },

  // ── Formspree (alternativa a EmailJS sin cuenta) ──────────
  formspree: {
    enabled: false,
    endpoint: '',  // Ej: 'https://formspree.io/f/xxxxxxxx'
  },

  // ── CRM custom via REST API ───────────────────────────────
  crm: {
    enabled: false,
    url:     '',    // Endpoint de tu CRM
    apiKey:  '',    // Header: Authorization: Bearer <apiKey>
    // Compatible con HubSpot, Pipedrive, etc. mediante webhook
  },

};

// ─── MAIN DISPATCHER ───────────────────────────────────────
async function sendToIntegrations(quizData, result) {
  const payload = buildPayload(quizData, result);

  const jobs = [];

  if (INTEGRATIONS.webhook.enabled && INTEGRATIONS.webhook.url) {
    jobs.push(toWebhook(payload));
  }
  if (INTEGRATIONS.googleSheets.enabled && INTEGRATIONS.googleSheets.url) {
    jobs.push(toGoogleSheets(payload));
  }
  if (INTEGRATIONS.emailjs.enabled && INTEGRATIONS.emailjs.serviceId) {
    jobs.push(toEmailJS(payload));
  }
  if (INTEGRATIONS.formspree.enabled && INTEGRATIONS.formspree.endpoint) {
    jobs.push(toFormspree(payload));
  }
  if (INTEGRATIONS.crm.enabled && INTEGRATIONS.crm.url) {
    jobs.push(toCRM(payload));
  }

  // Fire all, ignore individual failures silently
  const results = await Promise.allSettled(jobs);
  results.forEach((r, i) => {
    if (r.status === 'rejected') console.warn('[Integration ' + i + '] failed:', r.reason);
  });
}

// ─── PAYLOAD BUILDER ───────────────────────────────────────
function buildPayload(d, r) {
  return {
    // Meta
    timestamp:     new Date().toISOString(),
    source:        'calculadora-quiz',
    url:           window.location.href,

    // Lead contact
    nombre:        d.nombre       || '',
    email:         d.email        || '',
    telefono:      d.telefono     || '',
    preferencia:   d.preferenciaContacto || '',
    relacion:      d.relacion     || '',
    comentarios:   d.comentarios  || '',

    // Property
    municipio:     d.municipio    || '',
    zona:          d.zona         || '',
    codigoPostal:  d.codigoPostal || '',
    tipo:          d.tipo         || '',
    m2:            d.m2           || '',
    habitaciones:  d.habitaciones || '',
    banos:         d.banos        || '',
    anio:          d.anio         || '',
    planta:        d.planta       || '',
    ascensor:      d.ascensor     || '',
    estado:        d.estado       || '',
    extras:        (d.extras || []).join(', '),

    // Owner situation
    intencion:     d.intencion    || '',
    plazo:         d.plazo        || '',
    motivo:        d.motivo       || '',
    precioDeseado: d.precioDeseado || '',
    hipoteca:      d.hipoteca     || '',
    inmobiliaria:  d.inmobiliaria || '',

    // Calculated result
    estimacion:    r.base         || '',
    rango_min:     r.lo           || '',
    rango_max:     r.hi           || '',
    euros_m2:      r.ppm2         || '',
    alquiler_mes:  r.rent         || '',
    confianza:     r.confidence   || '',
    recomendacion: r.recLabel     || '',
    lead_score:    r.score        || '',
    lead_tier:     r.tier         || '',
    sobreprecio:   r.overpriced   ? 'Sí' : 'No',
  };
}

// ─── ADAPTERS ──────────────────────────────────────────────
async function toWebhook(payload) {
  return fetch(INTEGRATIONS.webhook.url, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(payload),
    mode:    'no-cors',
  });
}

async function toGoogleSheets(payload) {
  // Google Apps Script expects form-encoded or JSON
  return fetch(INTEGRATIONS.googleSheets.url, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(payload),
    mode:    'no-cors',
  });
}

async function toEmailJS(payload) {
  if (typeof emailjs === 'undefined') {
    console.warn('[EmailJS] Library not loaded. Add the emailjs CDN script to index.html.');
    return;
  }
  const cfg = INTEGRATIONS.emailjs;
  return emailjs.send(cfg.serviceId, cfg.templateId, {
    lead_name:     payload.nombre,
    lead_email:    payload.email,
    lead_phone:    payload.telefono,
    municipio:     payload.municipio,
    tipo:          payload.tipo,
    m2:            payload.m2,
    estado:        payload.estado,
    intencion:     payload.intencion,
    plazo:         payload.plazo,
    estimacion:    payload.estimacion,
    lead_tier:     payload.lead_tier,
    lead_score:    payload.lead_score,
    comentarios:   payload.comentarios,
    recomendacion: payload.recomendacion,
  }, cfg.publicKey);
}

async function toFormspree(payload) {
  return fetch(INTEGRATIONS.formspree.endpoint, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
    body:    JSON.stringify(payload),
  });
}

async function toCRM(payload) {
  const cfg = INTEGRATIONS.crm;
  return fetch(cfg.url, {
    method:  'POST',
    headers: {
      'Content-Type':  'application/json',
      'Authorization': cfg.apiKey ? 'Bearer ' + cfg.apiKey : '',
    },
    body: JSON.stringify(payload),
  });
}

// ─── CONVENIENCE: manual test ──────────────────────────────
// Run in browser console: testIntegrations()
function testIntegrations() {
  const mockData = {
    nombre: 'Test Lead', email: 'test@test.com', telefono: '+34600000000',
    municipio: 'tarragona', tipo: 'piso', m2: '90', estado: 'bueno',
    intencion: 'vender', plazo: 'inmediato', motivo: 'herencia',
    extras: ['terraza'], habitaciones: 3, banos: 1,
  };
  const mockResult = {
    base: 185000, lo: 160000, hi: 210000, ppm2: 2050, rent: 800,
    rentLo: 700, rentHi: 900, confidence: 88, score: 82, tier: 'caliente',
    recLabel: 'Vender', overpriced: false, underpriced: false,
  };
  console.log('[Integrations test] Payload:', buildPayload(mockData, mockResult));
  sendToIntegrations(mockData, mockResult);
}
