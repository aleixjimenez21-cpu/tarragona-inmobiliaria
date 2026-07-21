/* ═══════════════════════════════════════════════════════════
   ALEIX JIMÉNEZ — CONTENIDO EDITABLE DE LA LANDING
   Edita SOLO este archivo para cambiar cualquier texto,
   imagen o enlace. No toques promotoras.html ni promotoras.js.
═══════════════════════════════════════════════════════════ */

window.PCONTENT = {

  /* ── META / SEO ──────────────────────────────────────── */
  meta: {
    title:       'Aleix Jiménez — Estrategia digital para promotoras inmobiliarias',
    description: 'Sistemas de captación y comercialización digital para promotoras inmobiliarias. Estrategia, contenido, campañas y conversión en un único sistema.',
    ogUrl:       'https://aleixjimenez.com/promotoras',  // ← actualizar con dominio real
    ogImage:     'aleix/og-image.jpg',                   // ← añadir imagen en esa ruta
  },

  /* ── HEADER ──────────────────────────────────────────── */
  header: {
    brand: 'ALEIX JIMÉNEZ',
    links: [
      { label: 'Enfoque',   href: '#enfoque'  },
      { label: 'Sistema',   href: '#sistema'  },
      { label: 'Sobre mí', href: '#sobre-mi' },
      { label: 'Contacto', href: '#contacto' },
    ],
    cta: { label: 'Hablemos', href: '#contacto' },
  },

  /* ── HERO ────────────────────────────────────────────── */
  hero: {
    label: 'ESTRATEGIA DIGITAL · SECTOR INMOBILIARIO',

    /* Titular en 3 líneas. La última termina con la palabra de acento serif */
    headlineLines: ['Las promotoras', 'construyen espacios.', 'Yo construyo'],
    headlineAccent: 'demanda.',   /* ← se renderiza en Instrument Serif italic */

    body: 'Trabajo con un número limitado de promotoras para acelerar la comercialización de sus promociones mediante estrategia, captación y sistemas digitales.',

    cta1: { label: 'Solicitar una conversación', href: '#contacto' },
    cta2: { label: 'Descubrir el enfoque ↓',    href: '#enfoque'  },
    tags: ['Estrategia', 'Captación', 'Contenido', 'Automatización'],

    /* Columna retrato — sustituir por foto de Aleix cuando esté disponible.
       El CSS aplica grayscale(1) automáticamente: cualquier foto quedará B&N. */
    portrait:    'aleix/retrato.jpg',
    portraitAlt: 'Detalle arquitectónico — placeholder hasta sesión fotográfica',
    portraitLabel: 'ALEIX JIMÉNEZ — ESTRATEGIA DIGITAL',
  },

  /* ── MANIFIESTO ──────────────────────────────────────── */
  manifesto: {
    label: 'EL PRINCIPIO',
    index: '01 / 05',

    /* Las tres tesis — edita el texto de cada una aquí */
    theses: [
      { num: '01', text: 'Construir una promoción lleva años.' },
      { num: '02', text: 'Generar demanda no debería empezar al final.' },
      { num: '03', text: 'Mientras avanza la obra, también debería avanzar la venta.' },
    ],

    /* Frase final — edita aquí el texto y la palabra de acento */
    climax:       'La demanda también se construye.',
    climaxAccent: 'construye.',    /* ← se renderiza en Instrument Serif italic */
  },

  /* ── POSICIONAMIENTO ─────────────────────────────────── */
  positioning: {
    label: 'EL ENFOQUE',
    index: '02 / 05',

    /* Las tesis del enfoque — edita el texto aquí */
    theses: [
      { num: '01', text: 'No ejecuto acciones digitales aisladas.' },
      { num: '02', text: 'Diseño sistemas conectados para que cada promoción genere atención, capte compradores y convierta esa demanda en oportunidades comerciales.' },
      { num: '03', text: 'Se trata de construir una presencia digital capaz de acompañar toda la comercialización de una promoción.' },
    ],

    /* Frase de cierre */
    climax:       'Un solo sistema. Un solo objetivo: acelerar la venta.',
    climaxAccent: 'venta.',
  },

  /* ── SISTEMA ─────────────────────────────────────────── */
  /* Imágenes: añade los archivos en aleix/sistema-0X.jpg
     Sugerencia de contenido por ítem:
     01 → plano / mesa de trabajo / maqueta
     02 → render de promoción o pantalla con campaña
     03 → detalle de material, textura o cámara
     04 → interfaz de landing o firma de contrato
     05 → gráfico sobrio o panel de métricas                */
  system: {
    sectionLabel: 'QUÉ INTEGRA EL SISTEMA',
    index: '04 / 05',
    items: [
      {
        num: '01', title: 'Estrategia',
        body:  'Analizamos la promoción, el comprador, la ubicación, el posicionamiento y el proceso comercial antes de activar cualquier canal.',
        image: 'aleix/sistema-01.jpg',
      },
      {
        num: '02', title: 'Captación',
        body:  'Diseñamos campañas y activos digitales orientados a atraer compradores con una intención real.',
        image: 'aleix/sistema-02.jpg',
      },
      {
        num: '03', title: 'Contenido',
        body:  'Convertimos la promoción en una historia capaz de generar atención, confianza y deseo antes de su finalización.',
        image: 'aleix/sistema-03.jpg',
      },
      {
        num: '04', title: 'Conversión',
        body:  'Creamos landings, automatizaciones, procesos de cualificación y seguimiento para que las oportunidades no se pierdan.',
        image: 'aleix/sistema-04.jpg',
      },
      {
        num: '05', title: 'Optimización',
        body:  'Medimos el rendimiento, detectamos fricciones y mejoramos el sistema durante toda la comercialización.',
        image: 'aleix/sistema-05.jpg',
      },
    ],
  },

  /* ── IMPACTO ─────────────────────────────────────────── */
  impact: {
    label:          'EL SISTEMA',
    /* Las líneas ANTES del acento van en headlineLines;
       headlineAccent aparece solo en la última línea en serif itálica */
    headlineLines:  ['No más acciones'],
    headlineAccent: 'desconectadas.',
    support: 'Estrategia, medios, contenido y tecnología trabajando como un único sistema comercial.',
  },

  /* ── PARA QUIÉN ──────────────────────────────────────── */
  forWhom: {
    label:       'PARA QUIÉN',
    title:       'Trabajo con empresas que no quieren dejar la demanda al azar.',
    titleAccent: 'azar.',   /* ← palabra que se renderiza en Instrument Serif italic */
    items: [
      {
        role: 'FOCO',
        name: 'Promotoras inmobiliarias',
        body: 'Lanzamiento y comercialización de obra nueva.',
        featured: true,
      },
      {
        role: 'TAMBIÉN',
        name: 'Constructoras con promociones propias',
        body: 'Posicionamiento y captación directa de compradores.',
        featured: false,
      },
      {
        role: 'TAMBIÉN',
        name: 'Firmas inmobiliarias seleccionadas',
        body: 'Sistemas digitales para proyectos y activos de alto valor.',
        featured: false,
      },
    ],
  },

  /* ── PROCESO ─────────────────────────────────────────── */
  process: {
    title: 'De proyecto a demanda.',
    steps: [
      { num: '01', title: 'Diagnóstico',  body: 'Entender la promoción, el mercado y el proceso comercial.' },
      { num: '02', title: 'Arquitectura', body: 'Diseñar la estrategia, los canales y el sistema de conversión.' },
      { num: '03', title: 'Activación',   body: 'Lanzar campañas, contenido, activos y automatizaciones.' },
      { num: '04', title: 'Evolución',    body: 'Optimizar el sistema según la respuesta real del mercado.' },
    ],
  },

  /* ── SOBRE ALEIX ─────────────────────────────────────── */
  about: {
    /* Sustituir por foto editorial de Aleix cuando esté disponible */
    image:    'aleix/hero-2.jpg',
    imageAlt: 'Aleix Jiménez, estrategia digital para promotoras inmobiliarias',
    label:    'ALEIX JIMÉNEZ',
    headline: 'La parte digital detrás de cada promoción debería ser tan sólida como el propio proyecto.',
    body:     'Trabajo en la intersección entre estrategia, captación, contenido y tecnología aplicada al sector inmobiliario. Mi objetivo es ayudar a las promotoras a construir demanda antes de finalizar la obra, evitando depender únicamente de portales, acciones aisladas o procesos comerciales lentos. Cada colaboración parte del proyecto, de su comprador y de sus objetivos. No de una solución cerrada.',
    closing:  'No trabajo como un proveedor externo. Me involucro como parte del crecimiento del proyecto.',
  },

  /* ── COLABORACIÓN ────────────────────────────────────── */
  collaboration: {
    label:    'COLABORACIÓN PRIVADA',
    headline: 'Pocos proyectos. Implicación real.',
    body:     'Trabajo de forma personalizada con un número limitado de empresas para poder involucrarme de verdad en la estrategia, la ejecución y la evolución de cada promoción. No ofrezco paquetes genéricos. La colaboración se diseña alrededor del proyecto, su fase comercial y sus necesidades reales.',
    cta:      { label: 'Hablar sobre una promoción', href: '#contacto' },
  },

  /* ── CTA FINAL ───────────────────────────────────────── */
  finalCta: {
    label:    'PRÓXIMO PROYECTO',
    headline: 'La obra ya está\nen marcha.\n¿Y la demanda?',
    body:     'Si estás desarrollando o comercializando una promoción, podemos analizar su posicionamiento digital y detectar oportunidades de crecimiento.',
    cta:      { label: 'Solicitar una conversación', href: '#contacto' },
    note:     'Conversaciones privadas con promotoras y empresas del sector inmobiliario.',
  },

  /* ── CONTACTO ────────────────────────────────────────── */
  contact: {
    headline:  'Hablemos.',
    note:      'Revisaré personalmente la información y responderé si considero que puedo aportar valor al proyecto.',
    submitBtn: 'Enviar solicitud',
    links: {
      email:     'hola@aleixjimenez.com',   // ← sustituir
      instagram: 'https://instagram.com/',  // ← sustituir con perfil real
      linkedin:  'https://linkedin.com/',   // ← sustituir con perfil real
    },
  },

  /* ── FOOTER ──────────────────────────────────────────── */
  footer: {
    brand:   'ALEIX JIMÉNEZ',
    tagline: 'Estrategia digital para promotoras inmobiliarias.',
    closing: 'La demanda también se construye.',
    legal: [
      { label: 'Aviso legal', href: 'aviso-legal.html' },
      { label: 'Privacidad',  href: 'privacidad.html'  },
      { label: 'Cookies',     href: 'cookies.html'     },
    ],
  },
};
