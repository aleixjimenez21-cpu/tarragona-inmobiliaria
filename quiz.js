// ═══════════════════════════════════════════════════════════
//  QUIZ ENGINE — Aleix Jiménez Real Estate Operator
//  Diagnóstico inmobiliario inteligente · Tarragona 2025
// ═══════════════════════════════════════════════════════════

// ─── 1. MUNICIPALITY DATA ──────────────────────────────────
// Source: BBDD_Municipios_Tarragona_2025.xlsx (40 municipios)
// Fields: base/min/max = €/m² venta | alqM2 = €/m²/mes alquiler
//         mPiso/mCasa/mAtico/mNueva/mReformar = multiplicadores locales
//         xTerraza…xVistas = valor añadido en € por extra
// alqM2=€/m²/mes · alqMin/alqMax=€/mes totales (referencia piso 80m²)
// Fuente: Estudio_Alquiler_Tarragona_2025.xlsx
const MUNI = {
  'altafulla':                   { label:'Altafulla',                   comarca:'Tarragonès',      zona:'Costa Premium',           base:2950, min:2200, max:3800, alqM2:14.0,  alqMin:900,  alqMax:2000, conf:0.90, tourist:true,  urban:false, mPiso:1.05, mCasa:0.95, mAtico:1.15, mNueva:1.22, mReformar:0.82 },
  'salou':                       { label:'Salou',                       comarca:'Tarragonès',      zona:'Costa Alta',              base:2450, min:1900, max:3200, alqM2:11.5,  alqMin:700,  alqMax:1800, conf:0.93, tourist:true,  urban:false, mPiso:1.05, mCasa:0.90, mAtico:1.15, mNueva:1.22, mReformar:0.82 },
  'cambrils':                    { label:'Cambrils',                    comarca:'Baix Camp',       zona:'Costa Alta',              base:2550, min:2000, max:3400, alqM2:12.0,  alqMin:750,  alqMax:1900, conf:0.93, tourist:true,  urban:false, mPiso:1.05, mCasa:0.92, mAtico:1.13, mNueva:1.22, mReformar:0.82 },
  'torredembarra':               { label:'Torredembarra',               comarca:'Tarragonès',      zona:'Costa Alta',              base:2150, min:1650, max:2900, alqM2:10.5,  alqMin:640,  alqMax:1500, conf:0.90, tourist:true,  urban:false, mPiso:1.04, mCasa:0.93, mAtico:1.12, mNueva:1.22, mReformar:0.82 },
  'tarragona':                   { label:'Tarragona',                   comarca:'Tarragonès',      zona:'Capital Provincial',      base:2150, min:1500, max:2900, alqM2:10.8,  alqMin:620,  alqMax:1550, conf:0.90, tourist:false, urban:true,  mPiso:1.00, mCasa:0.88, mAtico:1.10, mNueva:1.22, mReformar:0.82 },
  'roda-de-bera':                { label:'Roda de Berà',                comarca:'Tarragonès',      zona:'Costa Media-Alta',        base:2050, min:1550, max:2750, alqM2:10.0,  alqMin:580,  alqMax:1400, conf:0.87, tourist:true,  urban:false, mPiso:1.03, mCasa:0.92, mAtico:1.12, mNueva:1.22, mReformar:0.82 },
  'creixell':                    { label:'Creixell',                    comarca:'Tarragonès',      zona:'Costa Media-Alta',        base:1980, min:1500, max:2650, alqM2:9.5,   alqMin:530,  alqMax:1350, conf:0.87, tourist:true,  urban:false, mPiso:1.02, mCasa:0.93, mAtico:1.10, mNueva:1.22, mReformar:0.82 },
  'cunit':                       { label:'Cunit',                       comarca:'Baix Penedès',    zona:'Costa Media-Alta',        base:1820, min:1380, max:2450, alqM2:9.2,   alqMin:530,  alqMax:1280, conf:0.84, tourist:true,  urban:false, mPiso:1.02, mCasa:0.93, mAtico:1.10, mNueva:1.22, mReformar:0.82 },
  'calafell':                    { label:'Calafell',                    comarca:'Baix Penedès',    zona:'Costa Media-Alta',        base:1950, min:1500, max:2700, alqM2:10.0,  alqMin:580,  alqMax:1450, conf:0.90, tourist:true,  urban:false, mPiso:1.03, mCasa:0.92, mAtico:1.12, mNueva:1.22, mReformar:0.82 },
  'tarragona-parte-alta':        { label:'Tarragona - Parte Alta',      comarca:'Tarragonès',      zona:'Capital - Zona Premium',  base:2395, min:1850, max:3200, alqM2:12.5,  alqMin:1000, alqMax:1700, conf:0.90, tourist:false, urban:true,  mPiso:1.00, mCasa:0.88, mAtico:1.15, mNueva:1.22, mReformar:0.82 },
  'tarragona-eixample':          { label:'Tarragona - Eixample',        comarca:'Tarragonès',      zona:'Capital - Zona Buena',    base:2200, min:1700, max:2950, alqM2:11.5,  alqMin:920,  alqMax:1500, conf:0.90, tourist:false, urban:true,  mPiso:1.00, mCasa:0.88, mAtico:1.10, mNueva:1.22, mReformar:0.82 },
  'tarragona-bonavista':         { label:'Tarragona - Bonavista',       comarca:'Tarragonès',      zona:'Capital - Zona Media',    base:1480, min:1100, max:1980, alqM2:8.23,  alqMin:658,  alqMax:1050, conf:0.84, tourist:false, urban:true,  mPiso:0.96, mCasa:0.86, mAtico:1.04, mNueva:1.22, mReformar:0.82 },
  'vila-seca':                   { label:'Vila-seca',                   comarca:'Tarragonès',      zona:'Costa Media',             base:1680, min:1250, max:2250, alqM2:9.0,   alqMin:520,  alqMax:1200, conf:0.87, tourist:true,  urban:false, mPiso:1.02, mCasa:0.90, mAtico:1.10, mNueva:1.22, mReformar:0.82 },
  'la-pineda':                   { label:'La Pineda (Vila-seca)',        comarca:'Tarragonès',      zona:'Costa Media-Alta',        base:1900, min:1500, max:2500, alqM2:11.0,  alqMin:640,  alqMax:1500, conf:0.90, tourist:true,  urban:false, mPiso:1.05, mCasa:0.92, mAtico:1.13, mNueva:1.22, mReformar:0.82 },
  'vandellos':                   { label:'Vandellòs i L\'Hospitalet',   comarca:'Baix Camp',       zona:'Costa Media',             base:2050, min:1500, max:2900, alqM2:9.8,   alqMin:560,  alqMax:1400, conf:0.90, tourist:true,  urban:false, mPiso:1.03, mCasa:0.92, mAtico:1.12, mNueva:1.22, mReformar:0.82 },
  'ametlla-de-mar':              { label:'L\'Ametlla de Mar',           comarca:'Baix Ebre',       zona:'Costa Media',             base:1780, min:1300, max:2450, alqM2:9.2,   alqMin:510,  alqMax:1200, conf:0.84, tourist:true,  urban:false, mPiso:1.02, mCasa:0.92, mAtico:1.10, mNueva:1.22, mReformar:0.82 },
  'ampolla':                     { label:'L\'Ampolla',                  comarca:'Baix Ebre',       zona:'Costa Media',             base:1680, min:1250, max:2300, alqM2:9.0,   alqMin:490,  alqMax:1150, conf:0.84, tourist:true,  urban:false, mPiso:1.01, mCasa:0.92, mAtico:1.08, mNueva:1.22, mReformar:0.82 },
  'mont-roig':                   { label:'Mont-roig del Camp',          comarca:'Baix Camp',       zona:'Costa Media',             base:1720, min:1280, max:2400, alqM2:8.9,   alqMin:500,  alqMax:1150, conf:0.84, tourist:true,  urban:false, mPiso:1.02, mCasa:0.93, mAtico:1.10, mNueva:1.22, mReformar:0.82 },
  'el-vendrell':                 { label:'El Vendrell',                 comarca:'Baix Penedès',    zona:'Interior Bueno',          base:1620, min:1200, max:2200, alqM2:9.5,   alqMin:520,  alqMax:1200, conf:0.87, tourist:false, urban:false, mPiso:1.00, mCasa:0.90, mAtico:1.08, mNueva:1.22, mReformar:0.82 },
  'reus':                        { label:'Reus',                        comarca:'Baix Camp',       zona:'Interior Bueno',          base:1561, min:1100, max:2100, alqM2:10.2,  alqMin:540,  alqMax:1200, conf:0.84, tourist:false, urban:true,  mPiso:0.98, mCasa:0.88, mAtico:1.06, mNueva:1.22, mReformar:0.82 },
  'montblanc':                   { label:'Montblanc',                   comarca:'Conca de Barberà',zona:'Interior Bueno',          base:1380, min:1000, max:1900, alqM2:7.5,   alqMin:400,  alqMax:950,  conf:0.84, tourist:false, urban:false, mPiso:0.97, mCasa:0.90, mAtico:1.05, mNueva:1.22, mReformar:0.82 },
  'valls':                       { label:'Valls',                       comarca:'Alt Camp',        zona:'Interior Bueno',          base:1020, min:720,  max:1400, alqM2:7.0,   alqMin:370,  alqMax:860,  conf:0.84, tourist:false, urban:false, mPiso:0.96, mCasa:0.88, mAtico:1.04, mNueva:1.22, mReformar:0.82 },
  'alcover':                     { label:'Alcover',                     comarca:'Alt Camp',        zona:'Interior Bueno',          base:1050, min:750,  max:1400, alqM2:6.0,   alqMin:304,  alqMax:720,  conf:0.81, tourist:false, urban:false, mPiso:0.96, mCasa:0.90, mAtico:1.03, mNueva:1.22, mReformar:0.82 },
  'la-selva':                    { label:'La Selva del Camp',           comarca:'Baix Camp',       zona:'Interior Bueno',          base:1150, min:820,  max:1600, alqM2:7.0,   alqMin:370,  alqMax:860,  conf:0.84, tourist:false, urban:false, mPiso:0.97, mCasa:0.90, mAtico:1.04, mNueva:1.22, mReformar:0.82 },
  'riudoms':                     { label:'Riudoms',                     comarca:'Baix Camp',       zona:'Interior Bueno',          base:1000, min:700,  max:1350, alqM2:5.8,   alqMin:280,  alqMax:680,  conf:0.81, tourist:false, urban:false, mPiso:0.96, mCasa:0.90, mAtico:1.03, mNueva:1.22, mReformar:0.82 },
  'constanti':                   { label:'Constantí',                   comarca:'Tarragonès',      zona:'Interior Bueno',          base:1120, min:780,  max:1520, alqM2:6.8,   alqMin:355,  alqMax:840,  conf:0.84, tourist:false, urban:false, mPiso:0.96, mCasa:0.88, mAtico:1.04, mNueva:1.22, mReformar:0.82 },
  'el-catllar':                  { label:'El Catllar',                  comarca:'Tarragonès',      zona:'Interior Bueno',          base:1050, min:750,  max:1400, alqM2:6.0,   alqMin:304,  alqMax:680,  conf:0.81, tourist:false, urban:false, mPiso:0.96, mCasa:0.90, mAtico:1.03, mNueva:1.22, mReformar:0.82 },
  'tortosa':                     { label:'Tortosa',                     comarca:'Baix Ebre',       zona:'Terres de l\'Ebre',       base:1150, min:820,  max:1600, alqM2:6.8,   alqMin:360,  alqMax:860,  conf:0.84, tourist:false, urban:false, mPiso:0.97, mCasa:0.90, mAtico:1.04, mNueva:1.22, mReformar:0.82 },
  'amposta':                     { label:'Amposta',                     comarca:'Montsià',         zona:'Terres de l\'Ebre',       base:1060, min:740,  max:1450, alqM2:6.3,   alqMin:315,  alqMax:740,  conf:0.81, tourist:false, urban:false, mPiso:0.96, mCasa:0.89, mAtico:1.03, mNueva:1.22, mReformar:0.82 },
  'sant-carles':                 { label:'Sant Carles de la Ràpita',    comarca:'Montsià',         zona:'Terres de l\'Ebre - Costa',base:1320, min:940, max:1820, alqM2:7.5,   alqMin:400,  alqMax:950,  conf:0.84, tourist:true,  urban:false, mPiso:0.97, mCasa:0.91, mAtico:1.05, mNueva:1.22, mReformar:0.82 },
  'alcanar':                     { label:'Alcanar',                     comarca:'Montsià',         zona:'Terres de l\'Ebre - Costa',base:1150, min:800, max:1600, alqM2:6.5,   alqMin:330,  alqMax:800,  conf:0.81, tourist:true,  urban:false, mPiso:0.96, mCasa:0.90, mAtico:1.04, mNueva:1.22, mReformar:0.82 },
  'deltebre':                    { label:'Deltebre',                    comarca:'Baix Ebre',       zona:'Terres de l\'Ebre',       base:940,  min:640,  max:1280, alqM2:5.8,   alqMin:290,  alqMax:680,  conf:0.78, tourist:false, urban:false, mPiso:0.95, mCasa:0.90, mAtico:1.02, mNueva:1.22, mReformar:0.82 },
  'ulldecona':                   { label:'Ulldecona',                   comarca:'Montsià',         zona:'Interior Sur',            base:950,  min:650,  max:1300, alqM2:5.8,   alqMin:280,  alqMax:680,  conf:0.78, tourist:false, urban:false, mPiso:0.95, mCasa:0.90, mAtico:1.02, mNueva:1.22, mReformar:0.82 },
  'roquetes':                    { label:'Roquetes',                    comarca:'Baix Ebre',       zona:'Interior Sur',            base:900,  min:620,  max:1250, alqM2:5.5,   alqMin:256,  alqMax:640,  conf:0.78, tourist:false, urban:false, mPiso:0.95, mCasa:0.89, mAtico:1.02, mNueva:1.22, mReformar:0.82 },
  'santa-barbara':               { label:'Santa Bàrbara',               comarca:'Montsià',         zona:'Interior Bajo',           base:740,  min:500,  max:1020, alqM2:4.8,   alqMin:230,  alqMax:550,  conf:0.75, tourist:false, urban:false, mPiso:0.93, mCasa:0.90, mAtico:1.00, mNueva:1.22, mReformar:0.82 },
  'horta-de-sant-joan':          { label:'Horta de Sant Joan',          comarca:'Terra Alta',      zona:'Interior Bajo',           base:800,  min:550,  max:1100, alqM2:4.8,   alqMin:240,  alqMax:560,  conf:0.75, tourist:false, urban:false, mPiso:0.94, mCasa:0.91, mAtico:1.01, mNueva:1.22, mReformar:0.82 },
  'prades':                      { label:'Prades',                      comarca:'Baix Camp',       zona:'Interior Bajo',           base:850,  min:580,  max:1200, alqM2:5.0,   alqMin:240,  alqMax:600,  conf:0.75, tourist:false, urban:false, mPiso:0.94, mCasa:0.92, mAtico:1.01, mNueva:1.22, mReformar:0.82 },
  'gandesa':                     { label:'Gandesa',                     comarca:'Terra Alta',      zona:'Interior Bajo',           base:890,  min:600,  max:1250, alqM2:5.3,   alqMin:260,  alqMax:620,  conf:0.75, tourist:false, urban:false, mPiso:0.94, mCasa:0.91, mAtico:1.01, mNueva:1.22, mReformar:0.82 },
  'mora-d-ebre':                 { label:'Mora d\'Ebre',                comarca:'Ribera d\'Ebre',  zona:'Interior Bajo',           base:910,  min:620,  max:1260, alqM2:5.4,   alqMin:265,  alqMax:630,  conf:0.75, tourist:false, urban:false, mPiso:0.94, mCasa:0.91, mAtico:1.01, mNueva:1.22, mReformar:0.82 },
  'santa-coloma-de-queralt':     { label:'Santa Coloma de Queralt',     comarca:'Conca de Barberà',zona:'Interior Bajo',           base:800,  min:540,  max:1100, alqM2:4.8,   alqMin:224,  alqMax:560,  conf:0.75, tourist:false, urban:false, mPiso:0.94, mCasa:0.91, mAtico:1.01, mNueva:1.22, mReformar:0.82 },
};

// ─── 1b. BARRIOS POR MUNICIPIO ─────────────────────────────
// Fuente: BBDD_Zonas_Barrios_Tarragona_2025.xlsx
const BARRIOS = {
  'tarragona':              ['Parte Alta','Eixample Nord','Eixample Sud / Joan XXIII','Centre','Sant Pere i Sant Pau / Llevant','Urbanitzacions de Llevant','Bonavista','Torreforta / La Granja / Campclar','Sant Salvador / Ponent','La Canonja'],
  'tarragona-parte-alta':   ['Zona Catedral / Via Augusta','Resto Part Alta'],
  'tarragona-eixample':     ['Rambla Nova / Eje Central','Eixample Interior'],
  'tarragona-bonavista':    ['Bonavista Centre','Bonavista Periferia'],
  'salou':                  ['Centre / Primera Línea Mar','Cap Salou','Zona Residencial Interior','Urbanizaciones Periféricas'],
  'cambrils':               ['Port / Primera Línea','Centre Vila','Zona Residencial Norte','Vilafortuny / Zona Sur'],
  'altafulla':              ['Centre Històric / Barri Medieval','Primera Línea Playa','Zona Residencial Interior'],
  'calafell':               ['Calafell Platja / Primera Línea','Segur de Calafell','Centre Vila','Masllorenç / Interior'],
  'cunit':                  ['Cunit Platja','Centre','Zona Residencial Interior'],
  'torredembarra':          ['Centre / Playa','Sant Jordi / Urbanizaciones','La Mora / Creixell Mar'],
  'roda-de-bera':           ['Roda de Berà Platja','Centre / Urbanitzacions'],
  'creixell':               ['Creixell Platja / Costa','Centre / Interior'],
  'vila-seca':              ['La Pineda','Centre Vila-seca','La Plana'],
  'la-pineda':              ['La Pineda','Centre Vila-seca'],
  'reus':                   ['Centre + Eixample Premium','Eixample Exterior / Nou Eixample','Carrilet / Estació Bus','Ponent / Passeig Prim','Fortuny / Migjorn','Barri Centre Històric','Llevant / Zona Est','Mas Abelló / Barris Nord'],
  'el-vendrell':            ['Centre','Comarruga / El Francàs','Sant Salvador','Zona Residencial Periferia'],
  'valls':                  ['Centre Històric','Eixample / Zona Nova','Barris Perifèrics'],
  'vandellos':              ["L'Hospitalet de l'Infant Centro",'Urbanització Ametlla / Costa','Vandellòs / Interior'],
  'ametlla-de-mar':         ['Port Esportiu / Primera Línea','Centre','Urbanitzacions Disperses'],
  'ampolla':                ['Centre / Port','Urbanitzacions Delta'],
  'mont-roig':              ['Miami Platja','Mont-roig Centre','Mas Clariana / Residencial'],
  'sant-carles':            ['Port / Primera Línea','Centre',"Les Cases d'Alcanar (límite)"],
  'alcanar':                ["Les Cases d'Alcanar",'Alcanar Centre'],
  'amposta':                ['Centre','Barris Residencials','Delta / Rururbà'],
  'tortosa':                ['Centre Històric','Eixample / Zona Nova','Barris Perifèrics','Ferreries / Zona Industrial'],
  'deltebre':               ['La Cava / Zona Fluvial',"Deltebre Centre / L'Aldea"],
  'constanti':              ['Centre','Polígon Industrial / Límites'],
  'el-catllar':             ['Centre del Poble'],
  'montblanc':              ['Muralles / Centre Històric','Eixample / Zona Residencial'],
  'alcover':                ['Centre del Poble'],
  'la-selva':               ['Centre'],
  'riudoms':                ['Centre'],
  'santa-barbara':          ['Centre'],
  'horta-de-sant-joan':     ['Centre Històric / Pueblo Picasso','Diseminado Rural'],
  'prades':                 ['Centre del Poble Rosa','Diseminado / Bosc'],
  'gandesa':                ['Centre'],
  'mora-d-ebre':            ['Centre'],
  'santa-coloma-de-queralt':['Centre'],
  'ulldecona':              ['Centre Urbà','Diseminado / Rural'],
  'roquetes':               ['Centre','Urbanitzacions Perifèriques'],
};

// ─── 1c. ALQUILER POR ZONA / BARRIO ───────────────────────
// Fuente: Estudio_Alquiler_Tarragona_2025.xlsx — Alquiler_Zonas_Barrios
// Claves deben coincidir exactamente con las cadenas en BARRIOS[]
const ALQUILER_ZONAS = {
  'tarragona': {
    'Parte Alta':                          { alqM2:12.15, alqMin:680,  alqMax:1600 },
    'Eixample Nord':                       { alqM2:11.5,  alqMin:620,  alqMax:1500 },
    'Eixample Sud / Joan XXIII':           { alqM2:11.0,  alqMin:590,  alqMax:1420 },
    'Centre':                              { alqM2:10.0,  alqMin:540,  alqMax:1280 },
    'Sant Pere i Sant Pau / Llevant':      { alqM2:10.5,  alqMin:560,  alqMax:1350 },
    'Urbanitzacions de Llevant':           { alqM2:12.0,  alqMin:680,  alqMax:1800 },
    'Bonavista':                           { alqM2:8.23,  alqMin:420,  alqMax:1050 },
    'Torreforta / La Granja / Campclar':   { alqM2:6.5,   alqMin:300,  alqMax:820  },
    'Sant Salvador / Ponent':              { alqM2:4.86,  alqMin:250,  alqMax:620  },
    'La Canonja':                          { alqM2:7.5,   alqMin:380,  alqMax:950  },
  },
  'tarragona-parte-alta': {
    'Zona Catedral / Via Augusta':         { alqM2:12.5,  alqMin:700,  alqMax:1700 },
    'Resto Part Alta':                     { alqM2:11.8,  alqMin:660,  alqMax:1550 },
  },
  'tarragona-eixample': {
    'Rambla Nova / Eje Central':           { alqM2:11.5,  alqMin:620,  alqMax:1500 },
    'Eixample Interior':                   { alqM2:10.5,  alqMin:590,  alqMax:1420 },
  },
  'tarragona-bonavista': {
    'Bonavista Centre':                    { alqM2:8.5,   alqMin:440,  alqMax:1100 },
    'Bonavista Periferia':                 { alqM2:7.5,   alqMin:380,  alqMax:950  },
  },
  'salou': {
    'Centre / Primera Línea Mar':          { alqM2:14.5,  alqMin:750,  alqMax:2200 },
    'Cap Salou':                           { alqM2:16.0,  alqMin:900,  alqMax:2800 },
    'Zona Residencial Interior':           { alqM2:9.0,   alqMin:480,  alqMax:1150 },
    'Urbanizaciones Periféricas':          { alqM2:7.5,   alqMin:380,  alqMax:950  },
  },
  'cambrils': {
    'Port / Primera Línea':                { alqM2:14.0,  alqMin:780,  alqMax:2000 },
    'Centre Vila':                         { alqM2:11.5,  alqMin:620,  alqMax:1500 },
    'Vilafortuny / Zona Sur':              { alqM2:12.0,  alqMin:680,  alqMax:1650 },
    'Zona Residencial Norte':              { alqM2:9.0,   alqMin:480,  alqMax:1150 },
  },
  'altafulla': {
    'Centre Històric / Barri Medieval':    { alqM2:15.0,  alqMin:850,  alqMax:2200 },
    'Primera Línea Playa':                 { alqM2:14.5,  alqMin:820,  alqMax:2100 },
    'Zona Residencial Interior':           { alqM2:11.0,  alqMin:640,  alqMax:1500 },
  },
  'calafell': {
    'Calafell Platja / Primera Línea':     { alqM2:12.0,  alqMin:680,  alqMax:1650 },
    'Segur de Calafell':                   { alqM2:11.0,  alqMin:620,  alqMax:1500 },
    'Centre Vila':                         { alqM2:8.0,   alqMin:440,  alqMax:1020 },
    'Masllorenç / Interior':               { alqM2:5.5,   alqMin:280,  alqMax:700  },
  },
  'cunit': {
    'Cunit Platja':                        { alqM2:11.0,  alqMin:620,  alqMax:1450 },
    'Centre':                              { alqM2:9.0,   alqMin:500,  alqMax:1160 },
    'Zona Residencial Interior':           { alqM2:7.5,   alqMin:400,  alqMax:960  },
  },
  'torredembarra': {
    'Centre / Playa':                      { alqM2:12.0,  alqMin:680,  alqMax:1600 },
    'Sant Jordi / Urbanizaciones':         { alqM2:9.5,   alqMin:520,  alqMax:1250 },
    'La Mora / Creixell Mar':              { alqM2:10.5,  alqMin:580,  alqMax:1400 },
  },
  'roda-de-bera': {
    'Roda de Berà Platja':                 { alqM2:11.5,  alqMin:660,  alqMax:1550 },
    'Centre / Urbanitzacions':             { alqM2:8.0,   alqMin:440,  alqMax:1020 },
  },
  'creixell': {
    'Creixell Platja / Costa':             { alqM2:11.0,  alqMin:620,  alqMax:1450 },
    'Centre / Interior':                   { alqM2:7.5,   alqMin:400,  alqMax:960  },
  },
  'vila-seca': {
    'La Pineda':                           { alqM2:11.0,  alqMin:640,  alqMax:1500 },
    'Centre Vila-seca':                    { alqM2:8.0,   alqMin:440,  alqMax:1020 },
    'La Plana':                            { alqM2:9.0,   alqMin:500,  alqMax:1150 },
  },
  'la-pineda': {
    'La Pineda':                           { alqM2:11.0,  alqMin:640,  alqMax:1500 },
    'Centre Vila-seca':                    { alqM2:8.0,   alqMin:440,  alqMax:1020 },
  },
  'reus': {
    'Centre':                              { alqM2:9.5,   alqMin:480,  alqMax:1200 },
    'Eixample / zona centro ampliada':     { alqM2:10.2,  alqMin:520,  alqMax:1300 },
    'Passeig Prim / Mare Molas':           { alqM2:9.5,   alqMin:480,  alqMax:1200 },
    'Niloga':                              { alqM2:8.5,   alqMin:430,  alqMax:1080 },
    "Carrilet / Estació d'autobusos":      { alqM2:8.0,   alqMin:400,  alqMax:1020 },
    'Mas Esglésies':                       { alqM2:8.0,   alqMin:400,  alqMax:1020 },
    'Horts de Miró':                       { alqM2:7.5,   alqMin:370,  alqMax:960  },
    'Barri Fortuny':                       { alqM2:8.8,   alqMin:440,  alqMax:1100 },
    'Barri Gaudí':                         { alqM2:8.8,   alqMin:440,  alqMax:1100 },
    'Aigüesverts':                         { alqM2:7.5,   alqMin:370,  alqMax:960  },
  },
  'el-vendrell': {
    'Centre':                              { alqM2:9.5,   alqMin:520,  alqMax:1220 },
    'Comarruga / El Francàs':             { alqM2:11.0,  alqMin:620,  alqMax:1450 },
    'Sant Salvador':                       { alqM2:10.5,  alqMin:590,  alqMax:1380 },
    'Zona Residencial Periferia':          { alqM2:7.5,   alqMin:400,  alqMax:950  },
  },
  'valls': {
    'Centre Històric':                     { alqM2:7.5,   alqMin:420,  alqMax:960  },
    'Eixample / Zona Nova':               { alqM2:6.5,   alqMin:360,  alqMax:820  },
    'Barris Perifèrics':                  { alqM2:5.5,   alqMin:300,  alqMax:700  },
  },
  'vandellos': {
    "L'Hospitalet de l'Infant Centro":    { alqM2:11.5,  alqMin:660,  alqMax:1550 },
    'Urbanització Ametlla / Costa':       { alqM2:9.5,   alqMin:540,  alqMax:1280 },
    'Vandellòs / Interior':               { alqM2:6.0,   alqMin:320,  alqMax:760  },
  },
  'ametlla-de-mar': {
    'Port Esportiu / Primera Línea':      { alqM2:11.0,  alqMin:640,  alqMax:1500 },
    'Centre':                             { alqM2:8.5,   alqMin:480,  alqMax:1080 },
    'Urbanitzacions Disperses':           { alqM2:7.0,   alqMin:380,  alqMax:880  },
  },
  'ampolla': {
    'Centre / Port':                      { alqM2:9.5,   alqMin:540,  alqMax:1220 },
    'Urbanitzacions Delta':               { alqM2:7.5,   alqMin:400,  alqMax:960  },
  },
  'mont-roig': {
    'Miami Platja':                       { alqM2:11.0,  alqMin:640,  alqMax:1500 },
    'Mont-roig Centre':                   { alqM2:7.0,   alqMin:380,  alqMax:880  },
    'Mas Clariana / Residencial':         { alqM2:7.5,   alqMin:420,  alqMax:960  },
  },
  'sant-carles': {
    'Port / Primera Línea':               { alqM2:9.0,   alqMin:510,  alqMax:1180 },
    'Centre':                             { alqM2:6.5,   alqMin:360,  alqMax:820  },
    "Les Cases d'Alcanar (límite)":       { alqM2:7.5,   alqMin:420,  alqMax:980  },
  },
  'alcanar': {
    "Les Cases d'Alcanar":                { alqM2:8.5,   alqMin:480,  alqMax:1100 },
    'Alcanar Centre':                     { alqM2:5.5,   alqMin:300,  alqMax:700  },
  },
  'amposta': {
    'Centre':                             { alqM2:6.5,   alqMin:360,  alqMax:840  },
    'Barris Residencials':                { alqM2:5.5,   alqMin:300,  alqMax:700  },
    'Delta / Rururbà':                    { alqM2:4.5,   alqMin:220,  alqMax:560  },
  },
  'tortosa': {
    'Centre Històric':                    { alqM2:7.5,   alqMin:420,  alqMax:980  },
    'Eixample / Zona Nova':              { alqM2:6.8,   alqMin:380,  alqMax:860  },
    'Barris Perifèrics':                 { alqM2:5.5,   alqMin:300,  alqMax:700  },
    'Ferreries / Zona Industrial':        { alqM2:5.0,   alqMin:270,  alqMax:640  },
  },
  'deltebre': {
    'La Cava / Zona Fluvial':            { alqM2:6.0,   alqMin:320,  alqMax:760  },
    "Deltebre Centre / L'Aldea":         { alqM2:5.2,   alqMin:270,  alqMax:660  },
  },
  'constanti': {
    'Centre':                             { alqM2:6.2,   alqMin:330,  alqMax:790  },
    'Polígon Industrial / Límites':       { alqM2:5.0,   alqMin:260,  alqMax:640  },
  },
  'el-catllar':  { 'Centre del Poble':                  { alqM2:6.0,   alqMin:310,  alqMax:760  } },
  'montblanc': {
    'Muralles / Centre Històric':         { alqM2:8.5,   alqMin:480,  alqMax:1100 },
    'Eixample / Zona Residencial':        { alqM2:6.5,   alqMin:360,  alqMax:820  },
  },
  'alcover':     { 'Centre del Poble':                  { alqM2:6.0,   alqMin:320,  alqMax:760  } },
  'la-selva':    { 'Centre':                             { alqM2:6.5,   alqMin:360,  alqMax:820  } },
  'riudoms':     { 'Centre':                             { alqM2:5.8,   alqMin:300,  alqMax:740  } },
  'santa-barbara': { 'Centre':                           { alqM2:4.5,   alqMin:220,  alqMax:560  } },
  'horta-de-sant-joan': {
    'Centre Històric / Pueblo Picasso':   { alqM2:5.0,   alqMin:250,  alqMax:640  },
    'Diseminado Rural':                   { alqM2:4.0,   alqMin:200,  alqMax:520  },
  },
  'prades': {
    'Centre del Poble Rosa':              { alqM2:5.5,   alqMin:280,  alqMax:700  },
    'Diseminado / Bosc':                  { alqM2:4.2,   alqMin:210,  alqMax:540  },
  },
  'gandesa':     { 'Centre':                             { alqM2:5.0,   alqMin:250,  alqMax:640  } },
  'mora-d-ebre': { 'Centre':                             { alqM2:5.2,   alqMin:260,  alqMax:660  } },
  'santa-coloma-de-queralt': { 'Centre':                 { alqM2:4.8,   alqMin:240,  alqMax:610  } },
  'ulldecona': {
    'Centre Urbà':                        { alqM2:5.8,   alqMin:300,  alqMax:740  },
    'Diseminado / Rural':                 { alqM2:4.5,   alqMin:220,  alqMax:560  },
  },
  'roquetes': {
    'Centre':                             { alqM2:5.5,   alqMin:280,  alqMax:700  },
    'Urbanitzacions Perifèriques':        { alqM2:4.8,   alqMin:240,  alqMax:620  },
  },
};

// ─── 1d. REFORMA DATA ──────────────────────────────────────
// Fuente: Estudio_Reforma_Rentabilidad_Tarragona_2025.xlsx
// ppm2R = €/m² tras reforma básica | reval80 = revalorización para 80m²
// roi = ROI reforma básica 80m² | roiCocina/roiBano/roiHS = ROI parciales
// absorbe: Sí/Parcial/No — si el mercado absorbe el sobrecoste
const REFORMA = {
  'altafulla':               { ppm2R:3300, reval80:20548, roi:105.5, roiCocina:81.3,  roiBano:51.1,  roiHS:353.3, absorbe:'Sí',      notas:'Mercado premium absorbe muy bien reformas de calidad alta. ROI máximo provincia.' },
  'tarragona-parte-alta':    { ppm2R:2900, reval80:22000, roi:120.0, roiCocina:53.6,  roiBano:28.0,  roiHS:284.0, absorbe:'Sí',      notas:'Zona histórica. Reforma premium se paga muy bien. Comprador sofisticado.' },
  'salou':                   { ppm2R:2750, reval80:19228, roi:92.3,  roiCocina:48.0,  roiBano:23.4,  roiHS:270.1, absorbe:'Sí',      notas:'Inversor turístico valora la reforma. Reforma básica siempre rentable.' },
  'cambrils':                { ppm2R:2950, reval80:19800, roi:98.0,  roiCocina:60.0,  roiBano:33.3,  roiHS:300.0, absorbe:'Sí',      notas:'Mercado costa premium. Reforma media con excelente ROI.' },
  'torredembarra':           { ppm2R:2450, reval80:17600, roi:76.0,  roiCocina:31.2,  roiBano:9.3,   roiHS:228.0, absorbe:'Sí',      notas:'Buen mercado. Reforma básica + cocina muy rentable.' },
  'tarragona-eixample':      { ppm2R:2280, reval80:16720, roi:67.2,  roiCocina:21.6,  roiBano:1.3,   roiHS:204.0, absorbe:'Sí',      notas:'Alta demanda. Reforma media muy buena inversión.' },
  'roda-de-bera':            { ppm2R:2320, reval80:16280, roi:62.8,  roiCocina:24.8,  roiBano:4.0,   roiHS:212.0, absorbe:'Sí',      notas:'Mercado segunda residencia valora la reforma.' },
  'creixell':                { ppm2R:2250, reval80:15400, roi:54.0,  roiCocina:21.6,  roiBano:1.3,   roiHS:204.0, absorbe:'Sí',      notas:'Mercado pequeño pero absorbe bien reformas básicas.' },
  'calafell':                { ppm2R:2220, reval80:16280, roi:62.8,  roiCocina:18.4,  roiBano:-1.3,  roiHS:196.0, absorbe:'Sí',      notas:'Tren BCN. Comprador exigente. Reforma siempre rentable.' },
  'cunit':                   { ppm2R:2080, reval80:14520, roi:45.2,  roiCocina:12.0,  roiBano:-6.7,  roiHS:180.0, absorbe:'Sí',      notas:'Buena absorción. Reforma básica recomendada.' },
  'vila-seca':               { ppm2R:1910, reval80:13420, roi:34.2,  roiCocina:2.7,   roiBano:-14.4, roiHS:156.8, absorbe:'Sí',      notas:'La Pineda eleva mercado. Reforma básica rentable.' },
  'la-pineda':               { ppm2R:1910, reval80:13420, roi:34.2,  roiCocina:2.7,   roiBano:-14.4, roiHS:156.8, absorbe:'Sí',      notas:'La Pineda eleva mercado. Reforma básica rentable.' },
  'vandellos':               { ppm2R:2150, reval80:15400, roi:54.0,  roiCocina:15.2,  roiBano:-4.0,  roiHS:188.0, absorbe:'Sí',      notas:'Mercado en subida fuerte. Cualquier reforma básica rentable ahora.' },
  'ametlla-de-mar':          { ppm2R:2010, reval80:13640, roi:36.4,  roiCocina:8.8,   roiBano:-9.3,  roiHS:172.0, absorbe:'Sí',      notas:'Puerto deportivo. Reforma básica muy recomendable.' },
  'ampolla':                 { ppm2R:1880, reval80:12320, roi:23.2,  roiCocina:2.4,   roiBano:-14.7, roiHS:156.0, absorbe:'Sí',      notas:'Mercado más tranquilo. Solo reforma básica recomendada.' },
  'mont-roig':               { ppm2R:1960, reval80:13640, roi:36.4,  roiCocina:5.6,   roiBano:-12.0, roiHS:164.0, absorbe:'Sí',      notas:'Miami Platja eleva. Reforma básica rentable en zona costera.' },
  'el-vendrell':             { ppm2R:1840, reval80:12760, roi:27.6,  roiCocina:-0.8,  roiBano:-17.3, roiHS:148.0, absorbe:'Sí',      notas:'Comarruga eleva demanda. Reforma básica y cocina recomendadas.' },
  'tarragona-bonavista':     { ppm2R:1640, reval80:10560, roi:5.6,   roiCocina:-10.4, roiBano:-25.3, roiHS:124.0, absorbe:'Parcial', notas:'Mercado obrero. Solo reforma básica y home staging justificados.' },
  'reus':                    { ppm2R:1550, reval80:10692, roi:6.9,   roiCocina:-16.3, roiBano:-30.3, roiHS:109.1, absorbe:'Parcial', notas:'Mercado amplio. Reforma básica sí. Integral solo en Eixample.' },
  'constanti':               { ppm2R:1250, reval80:8228,  roi:-17.7, roiCocina:-32.0, roiBano:-43.3, roiHS:70.1,  absorbe:'Parcial', notas:'Zona tensionada. Precio de venta bajo. Reforma básica con cautela.' },
  'el-catllar':              { ppm2R:1230, reval80:7920,  roi:-20.8, roiCocina:-32.8, roiBano:-44.0, roiHS:68.0,  absorbe:'No',      notas:'Precio demasiado bajo. Reforma integral no recuperable.' },
  'montblanc':               { ppm2R:1540, reval80:10560, roi:5.6,   roiCocina:-16.8, roiBano:-30.7, roiHS:108.0, absorbe:'Parcial', notas:'Muralles zona especial. Reforma premium para casa histórica sí.' },
  'valls':                   { ppm2R:1140, reval80:7744,  roi:-22.6, roiCocina:-38.3, roiBano:-48.6, roiHS:54.2,  absorbe:'Parcial', notas:'Precio bajo. Solo pintura+suelos y home staging justificados.' },
  'alcover':                 { ppm2R:1240, reval80:8360,  roi:-16.4, roiCocina:-32.8, roiBano:-44.0, roiHS:68.0,  absorbe:'Parcial', notas:'Mercado pequeño. Reforma básica con cautela.' },
  'la-selva':                { ppm2R:1300, reval80:8800,  roi:-12.0, roiCocina:-29.6, roiBano:-41.3, roiHS:76.0,  absorbe:'Parcial', notas:'Proximidad a Reus ayuda. Reforma básica recomendada.' },
  'riudoms':                 { ppm2R:1170, reval80:7480,  roi:-25.2, roiCocina:-36.0, roiBano:-46.7, roiHS:60.0,  absorbe:'No',      notas:'Precio muy bajo. Reforma básica borderline. Integral no recomendada.' },
  'tortosa':                 { ppm2R:1310, reval80:9240,  roi:-7.6,  roiCocina:-29.6, roiBano:-41.3, roiHS:76.0,  absorbe:'Parcial', notas:'Centro histórico es excepción. Reforma con potencial off-market.' },
  'amposta':                 { ppm2R:1190, reval80:7788,  roi:-22.1, roiCocina:-35.2, roiBano:-46.0, roiHS:62.1,  absorbe:'No',      notas:'Precio bajo. Solo pintura y limpieza justificados.' },
  'sant-carles':             { ppm2R:1480, reval80:10120, roi:1.2,   roiCocina:-20.0, roiBano:-33.3, roiHS:100.0, absorbe:'Parcial', notas:'Puerto eleva. Reforma básica recomendada en zona costera.' },
  'alcanar':                 { ppm2R:1300, reval80:8800,  roi:-12.0, roiCocina:-29.6, roiBano:-41.3, roiHS:76.0,  absorbe:'Parcial', notas:'Les Cases sí. Interior no. Diferenciar por zona.' },
  'deltebre':                { ppm2R:1050, reval80:6600,  roi:-34.0, roiCocina:-42.4, roiBano:-52.0, roiHS:44.0,  absorbe:'No',      notas:'Precio muy bajo. Ninguna reforma integral justificada.' },
  'ulldecona':               { ppm2R:1100, reval80:6600,  roi:-34.0, roiCocina:-39.2, roiBano:-49.3, roiHS:52.0,  absorbe:'No',      notas:'Mercado local. Solo cosmética básica justificada.' },
  'roquetes':                { ppm2R:1050, reval80:6600,  roi:-34.0, roiCocina:-42.4, roiBano:-52.0, roiHS:44.0,  absorbe:'No',      notas:'Precio mínimo. Solo pintura si propietario quiere vender más rápido.' },
  'santa-barbara':           { ppm2R:820,  reval80:4972,  roi:-50.3, roiCocina:-54.7, roiBano:-62.3, roiHS:13.1,  absorbe:'No',      notas:'Precio más bajo de la provincia. Ninguna reforma justificada.' },
  'horta-de-sant-joan':      { ppm2R:950,  reval80:6600,  roi:-34.0, roiCocina:-48.8, roiBano:-57.3, roiHS:28.0,  absorbe:'Parcial', notas:'Casa rural histórica sí. Piso estándar no justificado.' },
  'prades':                  { ppm2R:1010, reval80:7040,  roi:-29.6, roiCocina:-45.6, roiBano:-54.7, roiHS:36.0,  absorbe:'Parcial', notas:'Pueblo rosa. Reforma auténtica rural muy valorada. Nicho específico.' },
  'gandesa':                 { ppm2R:990,  reval80:6160,  roi:-38.4, roiCocina:-45.6, roiBano:-54.7, roiHS:36.0,  absorbe:'No',      notas:'Mercado local. Solo pintura básica.' },
  'mora-d-ebre':             { ppm2R:1010, reval80:6160,  roi:-38.4, roiCocina:-44.3, roiBano:-53.6, roiHS:39.2,  absorbe:'No',      notas:'Mercado muy local. Solo cosmética.' },
  'santa-coloma-de-queralt': { ppm2R:930,  reval80:5720,  roi:-42.8, roiCocina:-48.8, roiBano:-57.3, roiHS:28.0,  absorbe:'No',      notas:'Precio mínimo. No justificado.' },
  'tarragona':               { ppm2R:2490, reval80:17424, roi:74.2,  roiCocina:34.0,  roiBano:11.7,  roiHS:235.0, absorbe:'Sí',      notas:'Media ciudad. Reforma básica siempre recomendada.' },
};

// ─── 1e. CALC REFORMA ──────────────────────────────────────
// Escala datos del estudio (base 80m²) a la superficie real
function calcReforma(muniKey, m2) {
  const rf = REFORMA[muniKey] || REFORMA['tarragona'];
  const m2s = m2 || 80;
  const costeBasica    = Math.round(m2s * 125);          // €125/m² coste unitario provincia
  const revalBasica    = Math.round(rf.reval80 * m2s / 80);
  const neto           = revalBasica - costeBasica;
  const roiReal        = +((neto / costeBasica) * 100).toFixed(1);
  const scenario       = roiReal > 30 ? 'rentable' : roiReal >= 0 ? 'borderline' : 'no_rentable';
  return {
    scenario, roiReal, costeBasica, revalBasica, neto,
    ppm2R:          rf.ppm2R,
    precioReformado: Math.round(m2s * rf.ppm2R),
    roiCocina:      rf.roiCocina,
    roiBano:        rf.roiBano,
    roiHS:          rf.roiHS,
    absorbe:        rf.absorbe,
    notas:          rf.notas,
  };
}

// ─── 1d. REUS — PRECIOS BASE POR ZONA (€/m² buen estado post-1980) ────────
// Fuente: Parametros_Calculadora_Tarragona_2026.xlsx — Hoja 02
const REUS_ZONAS = {
  'Centre + Eixample Premium':     { base:1820, alqM2:11.0, alqMin:880,  alqMax:2300 },
  'Eixample Exterior / Nou Eixample':{ base:1720, alqM2:10.5, alqMin:840,  alqMax:2150 },
  'Carrilet / Estació Bus':        { base:1670, alqM2:10.0, alqMin:800,  alqMax:2000 },
  'Ponent / Passeig Prim':         { base:1580, alqM2:9.5,  alqMin:760,  alqMax:1950 },
  'Fortuny / Migjorn':             { base:1530, alqM2:9.2,  alqMin:736,  alqMax:1900 },
  'Barri Centre Històric':         { base:1650, alqM2:10.2, alqMin:816,  alqMax:2100 },
  'Llevant / Zona Est':            { base:1300, alqM2:8.0,  alqMin:640,  alqMax:1650 },
  'Mas Abelló / Barris Nord':      { base:1150, alqM2:7.2,  alqMin:576,  alqMax:1480 },
};

// ─── 2. MULTIPLIERS ────────────────────────────────────────
// Floor/year: global. State: global (Parametros_Calculadora_Tarragona_2026.xlsx)
const STATE_MULT = {
  'nueva':        1.22,
  'reformado':    1.15,
  'bueno':        1.00,
  'bueno_pre80':  0.90,
  'reformar':     0.82,
  'deteriorado':  0.68,
};
const FLOOR_MULT = {
  'pb_interior': 0.85,
  'pb_jardin':   0.98,
  'entreplanta': 0.90,
  '1a3':         1.00,
  '4a6':         1.04,
  '7mas':        1.04,
  'atico':       1.12,
  'bajo':        0.85,
};
const YEAR_MULT  = { '2015+':1.06, '2000-14':1.00, '1980-99':0.96, '1960-79':0.92, 'antes60':0.88 };

// Extras como % sobre valor base calculado (antes de extras)
// Descuento escalonado: 1º→100%, 2º→85%, 3º+→70%
// Fuente: Parametros_Calculadora_Tarragona_2026.xlsx — Hoja 04
const EXTRAS_PCT = {
  // Terraza
  'balcon_pequeno':  0.03,
  'terraza_mediana': 0.07,
  'terraza_grande':  0.11,
  'terraza_premium': 0.15,
  // Extras positivos
  'parking':              0.07,
  'jardin':               0.13,
  'piscina':              0.04,
  'vistas':               0.13,
  'trastero':             0.02,
  'aire_acondicionado':   0.02,
  'cert_AB':              0.04,
  'licencia_turistica':   0.10,
  'orientacion_sur':      0.04,
  'reforma_reciente':     0.06,
  'segunda_parking':      0.04,
  // Penalizaciones (valor negativo — se aplican al 100%, sin cascade)
  'cert_EFG':             -0.03,
  'orientacion_norte':    -0.05,
  'suelos_deteriorados':  -0.04,
};

// Cap máximo por extra (en €). Los extras de terraza usan cap zonal aparte.
const EXTRAS_CAP = {
  'trastero':           4000,
  'aire_acondicionado': 3500,
  'cert_AB':            8000,
  'licencia_turistica': 25000,
  'orientacion_sur':    7000,
  'reforma_reciente':   12000,
  'segunda_parking':    10000,
};

const EXTRAS_NOTES = {
  trastero:           'Muy valorado en pisos sin almacenamiento interior',
  cert_AB:            'Compradores cada vez más exigentes con eficiencia energética',
  cert_EFG:           'Calificación baja puede dificultar financiación bancaria',
  licencia_turistica: 'Activo con rentabilidad vacacional demostrada',
};

const TERRAZA_TYPES = ['balcon_pequeno','terraza_mediana','terraza_grande','terraza_premium','terraza_exacta'];

const EXTRA_LABELS = {
  balcon_pequeno:     'Balcón pequeño <4m²',
  terraza_mediana:    'Terraza mediana 4-14m²',
  terraza_grande:     'Terraza grande 15-29m²',
  terraza_premium:    'Terraza premium 30m²+',
  parking:            'Parking',
  piscina:            'Piscina',
  vistas:             'Vistas',
  trastero:           'Trastero',
  aire_acondicionado: 'Aire acondicionado',
  cert_AB:            'Cert. energético A/B',
  cert_EFG:           'Cert. energético E/F/G',
  licencia_turistica: 'Licencia turística',
  orientacion_sur:    'Orientación sur/suroeste',
  orientacion_norte:  'Orientación norte',
  reforma_reciente:   'Reforma reciente <3 años',
  suelos_deteriorados:'Suelos deteriorados',
  segunda_parking:    '2ª plaza parking',
};

// Municipios costeros donde aplica la licencia turística
const COASTAL_LICENCIA = new Set(['salou','cambrils','torredembarra','altafulla','calafell','cunit','vila-seca','vandellos','ametlla-de-mar','ampolla','mont-roig']);

// Horquilla de precio por tipo de zona:
// Costa premium → mayor volatilidad (compradores internacionales + inversores)
// Interior bajo → mercado local predecible, menor dispersión de precios
const H_COSTA_PREMIUM  = new Set(['altafulla','salou','cambrils','torredembarra','calafell','vandellos']);
const H_CAPITAL_MEDIA  = new Set(['tarragona','tarragona-parte-alta','tarragona-eixample','tarragona-bonavista','vila-seca','la-pineda','ametlla-de-mar','ampolla','mont-roig','roda-de-bera','creixell','cunit']);
const H_INTERIOR_BUENO = new Set(['reus','el-vendrell','montblanc','valls','la-selva','constanti','el-catllar']);

function getHorquillaMults(municipio) {
  if (H_COSTA_PREMIUM.has(municipio))  return { lo: 0.86, hi: 1.20 };
  if (H_CAPITAL_MEDIA.has(municipio))  return { lo: 0.88, hi: 1.15 };
  if (H_INTERIOR_BUENO.has(municipio)) return { lo: 0.90, hi: 1.12 };
  return { lo: 0.92, hi: 1.10 }; // Terres de l'Ebre / interior bajo
}

// ─── 3. STATE ──────────────────────────────────────────────
const QS = {
  step: 1,
  total: 5,
  d: {
    municipio:'', zona:'', calle:'', numero:'', piso:'', codigoPostal:'',
    tipo:'', m2:'', habitaciones:3, banos:1,
    anio:'', planta:'1a3', ascensor:'', estado:'', extras:[], terrazaM2: null,
    intencion:'', plazo:'', motivo:'',
    precioDeseado:'', hipoteca:'', inmobiliaria:'',
    nombre:'', email:'', telefono:'',
    preferenciaContacto:'', relacion:'', comentarios:'',
  },
  result: null,
};

// ─── 4. HELPERS ────────────────────────────────────────────
function snap(n, s) { return Math.round(n / s) * s; }

function eur(n) {
  return new Intl.NumberFormat('es-ES', { style:'currency', currency:'EUR', maximumFractionDigits:0 }).format(n);
}

function animNum(el, target, dur) {
  if (!el) return;
  const t0 = performance.now();
  const tick = (now) => {
    const p = Math.min((now - t0) / dur, 1);
    const e = 1 - Math.pow(1 - p, 3);
    el.textContent = eur(Math.round(e * target));
    if (p < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

function animBar(el, pct, delay) {
  if (!el) return;
  setTimeout(() => { el.style.width = pct + '%'; }, delay || 400);
}

function dots(score, max, color) {
  let html = '';
  for (let i = 1; i <= max; i++) {
    html += `<span class="score-dot${i <= score ? ' lit ' + color : ''}"></span>`;
  }
  return html;
}

function isUrgent(d) {
  return ['inmediato','1a3'].includes(d.plazo) || ['necesidad','divorcio','traslado'].includes(d.motivo);
}

// ─── 4b. BARRIO SELECTOR ───────────────────────────────────
function updateBarrioSelect(muni) {
  const sel = document.getElementById('barrio-select');
  if (!sel) return;
  QS.d.zona = '';
  const barrios = BARRIOS[muni] || [];
  if (!barrios.length) {
    sel.innerHTML = '<option value="">— Sin zonas específicas —</option>';
    sel.disabled = true;
    return;
  }
  sel.innerHTML = '<option value="">— Selecciona zona o barrio —</option>' +
    barrios.map(b => `<option value="${b}">${b}</option>`).join('');
  sel.disabled = false;
}

// ─── 5. NAVIGATION ─────────────────────────────────────────
function quizNext() {
  if (!validateStep(QS.step)) return;
  if (QS.step === 4) { runCalculation(); renderResults(); }
  moveTo(QS.step + 1);
}

function quizPrev() {
  if (QS.step > 1) moveTo(QS.step - 1);
}

function moveTo(n) {
  const from = document.getElementById('step-' + QS.step);
  const to   = document.getElementById('step-' + n);
  if (!to) return;
  from.classList.remove('qactive');
  QS.step = n;
  to.classList.add('qactive');
  updateProgress(n);
  updateSummaryPanel();
  const wrap = document.getElementById('quiz-wrap');
  if (wrap) setTimeout(() => wrap.scrollIntoView({ behavior:'smooth', block:'start' }), 60);
  const prevBtn = document.getElementById('quiz-prev');
  const nextBtn = document.getElementById('quiz-next');
  if (prevBtn) prevBtn.style.visibility = n > 1 && n < 5 ? 'visible' : 'hidden';
  if (nextBtn) nextBtn.style.display    = n < 5 ? 'flex' : 'none';
  // Hide sidebar on step 5 (results take full width)
  const sb = document.getElementById('calc-sidebar');
  if (sb) sb.style.display = n === 5 ? 'none' : '';
  const cl = document.querySelector('.calc-layout');
  if (cl) cl.classList.toggle('calc-full', n === 5);
}

function updateProgress(n) {
  document.querySelectorAll('.qdot').forEach((dot, i) => {
    const s = i + 1;
    dot.classList.remove('active', 'completed');
    if (s < n) dot.classList.add('completed');
    else if (s === n) dot.classList.add('active');
  });
  document.querySelectorAll('.qline').forEach((line, i) => {
    line.classList.toggle('done', i + 1 < n);
  });
  const lbl = document.getElementById('quiz-step-label');
  const labels = ['Ubicación', 'Activo', 'Estrategia', 'Contacto', 'Diagnóstico'];
  if (lbl) lbl.textContent = `Paso ${n} de 5 — ${labels[n - 1]}`;
}

// ─── SIDEBAR SUMMARY PANEL ─────────────────────────────
function updateSummaryPanel() {
  const d = QS.d;
  const TIPO_LABELS = { piso:'Piso', casa:'Casa', atico:'Ático', duplex:'Dúplex', chalet:'Chalet' };
  const ESTADO_LABELS = { nueva:'Obra nueva', reformado:'Reformado', bueno:'Buen estado', bueno_pre80:'Buen estado pre-1980', reformar:'A reformar', deteriorado:'Muy deteriorado' };
  const INTENCION_LABELS = { vender:'Vender', alquilar:'Alquilar', reformar:'Reformar', valorar:'Valorar', nose:'Por decidir' };
  const PLAZO_LABELS = { inmediato:'Inmediato', '1a3':'1–3 meses', '3a6':'3–6 meses', '6a12':'6–12 meses', sinprisa:'Sin prisa' };
  const m = d.municipio ? MUNI[d.municipio] : null;

  function csSet(id, val) {
    const el = document.getElementById(id);
    if (!el) return;
    if (val && val !== '—') {
      el.textContent = val;
      el.classList.add('cs-filled');
    } else {
      el.textContent = '—';
      el.classList.remove('cs-filled');
    }
  }

  csSet('cs-municipio-val', m ? m.label : null);
  csSet('cs-tipo-val',      d.tipo     ? TIPO_LABELS[d.tipo]            : null);
  csSet('cs-m2-val',        d.m2       ? d.m2 + ' m²'                   : null);
  csSet('cs-estado-val',    d.estado   ? ESTADO_LABELS[d.estado]        : null);
  csSet('cs-objetivo-val',  d.intencion ? INTENCION_LABELS[d.intencion] : null);
  csSet('cs-plazo-val',     d.plazo    ? PLAZO_LABELS[d.plazo]          : null);
}

// ─── 6. VALIDATION ─────────────────────────────────────────
function validateStep(step) {
  clearQError();
  switch (step) {
    case 1:
      if (!QS.d.municipio) { showQError('Selecciona el municipio para calibrar el análisis.'); return false; }
      return true;
    case 2:
      if (!QS.d.tipo)  { showQError('Selecciona el tipo de vivienda.'); return false; }
      const m2v = parseFloat(QS.d.m2);
      if (!m2v || m2v < 20 || m2v > 1000) { showQError('Introduce una superficie válida entre 20 y 1.000 m².'); return false; }
      if (!QS.d.estado) { showQError('Indica el estado del inmueble.'); return false; }
      return true;
    case 3:
      if (!QS.d.intencion) { showQError('Indica qué quieres hacer con la propiedad.'); return false; }
      return true;
    case 4:
      if (!QS.d.nombre.trim()) { showQError('Introduce tu nombre.'); return false; }
      if (!QS.d.email.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(QS.d.email)) {
        showQError('Introduce un email válido.'); return false;
      }
      return true;
    default: return true;
  }
}

function showQError(msg) {
  const el = document.getElementById('quiz-error');
  if (!el) return;
  el.textContent = msg;
  el.classList.remove('hidden');
  el.scrollIntoView({ behavior:'smooth', block:'nearest' });
}
function clearQError() {
  const el = document.getElementById('quiz-error');
  if (el) el.classList.add('hidden');
}

// ─── 7. INTERACTION HANDLERS ───────────────────────────────
function qCard(el, field, value) {
  const group = el.dataset.group;
  document.querySelectorAll(`[data-group="${group}"]`).forEach(c => c.classList.remove('selected'));
  el.classList.add('selected');
  QS.d[field] = value;
  clearQError();
  updateSummaryPanel();
  updateConditionalExtras();
}

function qMulti(el, value) {
  if (value === 'ninguno') {
    QS.d.extras = ['ninguno'];
    document.querySelectorAll('.q-tag').forEach(t => t.classList.remove('selected'));
    el.classList.add('selected');
    updateConditionalExtras();
    return;
  }
  document.querySelectorAll('[data-extra="ninguno"]').forEach(t => t.classList.remove('selected'));
  QS.d.extras = QS.d.extras.filter(e => e !== 'ninguno');
  if (QS.d.extras.includes(value)) {
    QS.d.extras = QS.d.extras.filter(e => e !== value);
    el.classList.remove('selected');
  } else {
    QS.d.extras.push(value);
    el.classList.add('selected');
  }
  updateConditionalExtras();
}

function qMultiExcl(el, value, excludes) {
  excludes.forEach(excl => {
    QS.d.extras = QS.d.extras.filter(e => e !== excl);
    document.querySelectorAll(`[data-extra="${excl}"]`).forEach(b => b.classList.remove('selected'));
  });
  qMulti(el, value);
}

function updateConditionalExtras() {
  const d = QS.d;
  function toggleBtn(id, show) {
    const btn = document.getElementById(id);
    if (!btn) return;
    if (show) {
      btn.classList.remove('hidden');
    } else {
      btn.classList.add('hidden');
      const ex = btn.dataset.extra;
      if (ex && d.extras.includes(ex)) {
        d.extras = d.extras.filter(e => e !== ex);
        btn.classList.remove('selected');
      }
    }
  }
  toggleBtn('btn-licencia_turistica', COASTAL_LICENCIA.has(d.municipio));
  const showReforma = (d.estado === 'bueno' || d.estado === 'bueno_pre80');
  toggleBtn('btn-reforma_reciente', showReforma);
  const antesDe1980 = (d.anio === '1960-79' || d.anio === 'antes60');
  toggleBtn('btn-suelos_deteriorados', d.estado === 'reformar' || antesDe1980);
  toggleBtn('btn-segunda_parking', d.extras.includes('parking'));
}

function selectTerrazaA(btn, choice) {
  document.querySelectorAll('#terraza-pregA .q-tag').forEach(b => b.classList.remove('selected'));
  btn.classList.add('selected');
  const pregB = document.getElementById('terraza-pregB');
  if (choice === 'si') {
    pregB.classList.remove('hidden');
  } else {
    pregB.classList.add('hidden');
    document.querySelectorAll('#terraza-opciones .q-tag').forEach(b => b.classList.remove('selected'));
    document.getElementById('terraza-metros-wrap').classList.add('hidden');
    QS.d.extras = (QS.d.extras || []).filter(e => !TERRAZA_TYPES.includes(e));
    QS.d.terrazaM2 = null;
  }
}

function selectTerrazaTipo(btn, tipo) {
  document.querySelectorAll('#terraza-opciones .q-tag').forEach(b => b.classList.remove('selected'));
  btn.classList.add('selected');
  QS.d.extras = (QS.d.extras || []).filter(e => !TERRAZA_TYPES.includes(e));
  QS.d.extras.push(tipo);
  const metrosWrap = document.getElementById('terraza-metros-wrap');
  if (tipo === 'terraza_exacta') {
    metrosWrap.classList.remove('hidden');
  } else {
    metrosWrap.classList.add('hidden');
    QS.d.terrazaM2 = null;
  }
}

function setTerrazaM2(val) {
  QS.d.terrazaM2 = parseFloat(val) || null;
}

function qCounter(field, delta, min, max) {
  const val = Math.max(min, Math.min(max, (parseInt(QS.d[field]) || min) + delta));
  QS.d[field] = val;
  const el = document.getElementById('ctr-' + field);
  if (el) el.textContent = val >= max ? val + '+' : val;
}

// ─── 8. CALCULATION ENGINE ─────────────────────────────────
function runCalculation() {
  const d = QS.d;
  const m = MUNI[d.municipio] || MUNI['tarragona'];
  const m2 = parseFloat(d.m2) || 80;
  const reforma = calcReforma(d.municipio, m2);

  // Precio base por m²: si Reus y zona seleccionada, usar precio de zona
  const reusZona = (d.municipio === 'reus' && d.zona && REUS_ZONAS[d.zona]) ? REUS_ZONAS[d.zona] : null;
  const baseM2   = reusZona ? reusZona.base : m.base;

  // Tipo de inmueble
  const typeMult = d.tipo === 'piso'   ? m.mPiso :
                   d.tipo === 'casa'   ? m.mCasa :
                   d.tipo === 'atico'  ? m.mAtico :
                   d.tipo === 'duplex' ? (m.mPiso + m.mAtico) / 2 :
                   d.tipo === 'chalet' ? m.mCasa * 1.08 :
                   m.mPiso;

  // Estado del inmueble — global (Parametros_Calculadora_Tarragona_2026.xlsx)
  const stateMult = STATE_MULT[d.estado] || 1.0;

  // Planta + ascensor: 4ª+ sin ascensor usa mult reducido
  const highFloor = d.planta === '4a6' || d.planta === '7mas';
  let floorMult;
  if (highFloor && d.ascensor === 'no') {
    floorMult = 0.86;
  } else {
    floorMult = FLOOR_MULT[d.planta] || 1.00;
  }
  // Bonus ascensor para plantas 1-3 en edificios altos
  const ascMult = (!highFloor && d.planta !== 'atico' && d.ascensor === 'si') ? 1.04 : 1.00;

  const yearMult  = YEAR_MULT[d.anio] || 1;

  // Valor base antes de extras
  const ppm2     = Math.round(baseM2 * typeMult * stateMult * floorMult * ascMult * yearMult);
  const valorBase = m2 * ppm2;

  // Extras: positivos con cascade escalonado, penalizaciones a 100% sin cascade
  const extras = (d.extras || []).filter(e => e !== 'ninguno');
  const positiveExtras = extras.filter(e => e === 'terraza_exacta' || (EXTRAS_PCT[e] || 0) >= 0);
  const penaltyExtras  = extras.filter(e => e !== 'terraza_exacta' && (EXTRAS_PCT[e] || 0) < 0);

  const effectivePct = (e) => {
    if (e === 'terraza_exacta' && d.terrazaM2) return (d.terrazaM2 * baseM2 * 0.25) / valorBase;
    return EXTRAS_PCT[e] || 0;
  };
  const positivesSorted = [...positiveExtras].sort((a, b) => effectivePct(b) - effectivePct(a));

  let totalExtras = 0;
  const extrasItems = [];

  positivesSorted.forEach((extra, idx) => {
    const factor = idx === 0 ? 1.00 : idx === 1 ? 0.85 : 0.70;
    let valor, item;
    if (extra === 'terraza_exacta' && d.terrazaM2) {
      valor = snap(d.terrazaM2 * baseM2 * 0.25 * factor, 100);
      const terrazaCap = m.tourist ? 45000 : m.urban ? 35000 : 25000;
      valor = Math.min(valor, terrazaCap);
      item = { extra, exacta: true, m2: d.terrazaM2, baseM2, cascadePct: Math.round(factor * 100), valor };
    } else {
      const pct = EXTRAS_PCT[extra] || 0;
      valor = snap(valorBase * pct * factor, 100);
      if (TERRAZA_TYPES.includes(extra)) {
        const terrazaCap = m.tourist ? 45000 : m.urban ? 35000 : 25000;
        valor = Math.min(valor, terrazaCap);
      } else if (EXTRAS_CAP[extra] !== undefined) {
        valor = Math.min(valor, EXTRAS_CAP[extra]);
      }
      item = { extra, basePct: Math.round(pct * 100), cascadePct: Math.round(factor * 100), valor };
    }
    totalExtras += valor;
    extrasItems.push(item);
  });

  // Penalizaciones a 100% (sin cascade, sin cap)
  penaltyExtras.forEach(extra => {
    const pct = EXTRAS_PCT[extra] || 0;
    const valor = snap(valorBase * pct, 100);
    extrasItems.push({ extra, basePct: Math.round(pct * 100), penalty: true, valor });
    totalExtras += valor;
  });

  let base = snap(valorBase + totalExtras, 500);
  const hm = getHorquillaMults(d.municipio);
  let lo   = snap(base * hm.lo, 500);
  let hi   = snap(base * hm.hi, 500);

  // Alquiler: prioridad → Reus zona > ALQUILER_ZONAS barrio > municipio
  const zoneAlq = reusZona ? reusZona :
                  (d.zona && ALQUILER_ZONAS[d.municipio]) ? ALQUILER_ZONAS[d.municipio][d.zona] : null;
  const alqData = zoneAlq || m;
  const rentRaw = Math.round(m2 * alqData.alqM2);
  const rent    = snap(Math.max(alqData.alqMin, Math.min(alqData.alqMax, rentRaw)), 25);
  const rentLo  = snap(alqData.alqMin, 25);
  const rentHi  = snap(alqData.alqMax, 25);

  const desired = parseFloat(d.precioDeseado) || 0;
  const overpriced  = desired > 0 && desired > base * 1.15;
  const underpriced = desired > 0 && desired < base * 0.85;
  const overpricePct = desired > 0 ? Math.round((desired / base - 1) * 100) : 0;

  const confidence = calcConfidence(d, m);
  const { recommendation, recLabel, recTag } = getRecommendation(d, m, base, reforma);
  const diagnosis  = generateDiagnosis(d, m, base, desired, reforma);
  const strategy   = generateStrategy(d, m, base, recommendation, diagnosis, reforma);
  const leadProfile = generateLeadProfile(d, base, desired);

  // Precio de salida según plazo
  const PLAZO_MULT = { inmediato:0.94, '1a3':0.97, '3a6':0.99, '6a12':1.00, sinprisa:1.02 };
  const precioSalida = snap(base * (PLAZO_MULT[d.plazo] || 1.00), 500);

  // Desglose del cálculo para mostrar en resultado
  const desglose = {
    baseM2,
    m2,
    ppm2,
    valorBase: snap(valorBase, 500),
    extrasItems,
    totalExtras: snap(totalExtras, 500),
  };

  QS.result = {
    base, lo, hi, ppm2, rent, rentLo, rentHi,
    confidence, overpriced, underpriced, overpricePct, desired,
    recommendation, recLabel, recTag,
    diagnosis, strategy, leadProfile,
    reforma, precioSalida, desglose,
    muniLabel: m.label,
    muni: m,
  };
}

// ─── 9. CONFIDENCE ─────────────────────────────────────────
function calcConfidence(d, m) {
  let c = Math.round(m.conf * 100);
  if (d.tipo)    c += 2;
  if (d.anio)    c += 2;
  if (d.zona)    c += 3;
  if (d.planta !== '1a3') c += 1;
  const extras = (d.extras || []).filter(e => e !== 'ninguno');
  if (extras.length > 0) c += 2;
  return Math.min(97, c);
}

// ─── 10. RECOMMENDATION ENGINE ─────────────────────────────
function getRecommendation(d, m, base, reforma) {
  const urgent   = isUrgent(d);
  const tourist  = m.tourist;
  const lowDemand = m.base < 1200;
  const reformar = d.estado === 'reformar';
  const rfScenario = reforma ? reforma.scenario : 'borderline';

  // Edge combinations
  if (reformar && urgent) {
    return { recommendation:'vender', recLabel:'Vender con precio competitivo', recTag:'Precio ajustado al mercado real' };
  }
  if (reformar && (d.intencion === 'vender' || d.intencion === 'nose')) {
    if (rfScenario === 'rentable') {
      return { recommendation:'reformar', recLabel:'Reformar antes de vender', recTag:`Reforma básica con ROI del ${reforma.roiReal}% en ${m.label}` };
    } else if (rfScenario === 'no_rentable') {
      return { recommendation:'vender', recLabel:'Vender sin reforma (no rentable)', recTag:`Reforma no recuperable en ${m.label} — precio ajustado` };
    }
    return { recommendation:'reformar', recLabel:'Reformar selectivamente antes de vender', recTag:'Reforma selectiva para maximizar precio' };
  }
  if (d.intencion === 'alquilar' && tourist) {
    return { recommendation:'alquilar', recLabel:'Alquiler turístico o temporal', recTag:'Potencial vacacional elevado en esta zona' };
  }
  if (d.intencion === 'alquilar') {
    return { recommendation:'alquilar', recLabel:'Alquiler de larga duración', recTag:'Rentabilidad estimada 5.2% bruto anual' };
  }
  if (d.intencion === 'vender' && !reformar && urgent) {
    return { recommendation:'vender', recLabel:'Vender con estrategia rápida', recTag:'Precio de salida ligeramente por debajo del máximo' };
  }
  if (d.intencion === 'vender' && !reformar && !urgent) {
    return { recommendation:'vender', recLabel:'Preparar y vender bien posicionado', recTag:'Sin urgencia: optimizar presentación antes de salir' };
  }
  if (d.intencion === 'reformar') {
    return { recommendation:'reformar', recLabel:'Reformar y reposicionar', recTag:'Reforma + venta o alquiler premium' };
  }
  if (d.intencion === 'valorar' || d.intencion === 'nose') {
    if (lowDemand) return { recommendation:'analizar', recLabel:'Análisis personalizado necesario', recTag:'Mercado con menor dinámica — estrategia a medida' };
    return { recommendation:'analizar', recLabel:'Analizar opciones en detalle', recTag:'Varias vías válidas — requiere análisis completo' };
  }
  return { recommendation:'vender', recLabel:'Vender al precio de mercado', recTag:'Posicionamiento estándar' };
}

// ─── 11. MARKET DIAGNOSIS ──────────────────────────────────
function generateDiagnosis(d, m, base, desired, reforma) {
  const tourist  = m.tourist;
  const urban    = m.urban;
  const lowDemand = m.base < 1200;
  const highDemand = m.base >= 1700;

  // Demand level
  let demandLabel, demandLevel;
  if (highDemand || tourist) { demandLabel='Alta'; demandLevel=3; }
  else if (m.base >= 1400)   { demandLabel='Media-alta'; demandLevel=2; }
  else if (m.base >= 1200)   { demandLabel='Media'; demandLevel=2; }
  else                       { demandLabel='Moderada'; demandLevel=1; }

  // Liquidity
  let liquidityLabel, liquidityDays, liquidityLevel;
  if ((d.estado === 'reformar' || d.estado === 'deteriorado') && lowDemand) { liquidityLabel='Baja'; liquidityDays='90–120 días'; liquidityLevel=1; }
  else if (d.estado === 'reformar' || d.estado === 'deteriorado') { liquidityLabel='Reducida'; liquidityDays='60–90 días'; liquidityLevel=1; }
  else if (highDemand || tourist)               { liquidityLabel='Alta'; liquidityDays='25–45 días'; liquidityLevel=3; }
  else if (m.base >= 1400)                      { liquidityLabel='Media'; liquidityDays='40–65 días'; liquidityLevel=2; }
  else                                          { liquidityLabel='Moderada'; liquidityDays='60–90 días'; liquidityLevel=1; }

  // State impact
  let stateLabel, stateLevel;
  if (d.estado === 'nueva')        { stateLabel='Muy positivo (+22%)'; stateLevel=3; }
  else if (d.estado === 'reformado') { stateLabel='Positivo (+15%)'; stateLevel=3; }
  else if (d.estado === 'bueno')   { stateLabel='Neutro (mercado)'; stateLevel=2; }
  else if (d.estado === 'bueno_pre80') { stateLabel='Leve descuento (−10%)'; stateLevel=2; }
  else if (d.estado === 'reformar') { stateLabel='Reductor (−18%)'; stateLevel=1; }
  else                             { stateLabel='Muy reductor (−32%)'; stateLevel=1; }

  // Price alignment
  let priceLabel, priceLevel;
  if (!desired || desired === 0) { priceLabel='No indicado'; priceLevel=2; }
  else if (desired <= base * 1.00) { priceLabel='Por debajo de mercado'; priceLevel=2; }
  else if (desired <= base * 1.08) { priceLabel='Dentro del rango'; priceLevel=3; }
  else if (desired <= base * 1.15) { priceLabel='Ligeramente alto'; priceLevel=2; }
  else { priceLabel='Sobrepreciado'; priceLevel=1; }

  // Build diagnosis paragraphs
  const paragraphs = [];

  if (tourist) {
    paragraphs.push(`${m.label} es una zona con demanda turística activa. El mercado combina compradores nacionales con perfiles internacionales (mercados nórdico, inglés y alemán) y cuenta con demanda inversora orientada al alquiler vacacional. Esto aporta liquidez elevada y precio por metro cuadrado superior a la media provincial.`);
  } else if (urban) {
    paragraphs.push(`${m.label} mantiene demanda residencial constante impulsada principalmente por compradores locales, reubicaciones profesionales y pequeños inversores patrimonialistas. El mercado tiene buena absorción y tiempos de venta competitivos cuando el precio de salida es correcto.`);
  } else if (lowDemand) {
    paragraphs.push(`El mercado de ${m.label} presenta menor dinamismo respecto a las zonas costeras o urbanas principales. Los plazos de venta son más largos y el margen de negociación suele ser mayor. Una estrategia de precio realista desde el inicio es especialmente crítica en esta zona.`);
  } else {
    paragraphs.push(`${m.label} es una zona con mercado activo y demanda estable. Los compradores buscan principalmente vivienda habitual o de inversión. El posicionamiento de precio es el factor más determinante para el plazo de venta.`);
  }

  if (d.estado === 'reformar' && reforma) {
    const rfSign = reforma.roiReal >= 0 ? '+' : '';
    if (reforma.scenario === 'rentable') {
      paragraphs.push(`El estado a reformar reduce el universo de compradores potenciales en un 35–45%. Sin embargo, en ${m.label} una reforma básica de ${eur(reforma.costeBasica)} genera una revalorización estimada de ${eur(reforma.revalBasica)}, un neto de ${eur(reforma.neto)} (ROI: ${rfSign}${reforma.roiReal}%). Invertir en reforma básica antes de vender es financieramente sólido en esta zona.`);
    } else if (reforma.scenario === 'borderline') {
      paragraphs.push(`El estado a reformar reduce el universo de compradores potenciales en un 35–45%. En ${m.label}, la reforma básica (${eur(reforma.costeBasica)}) recupera ${eur(reforma.revalBasica)} — el margen neto es ${reforma.neto >= 0 ? eur(reforma.neto) : '−'+eur(Math.abs(reforma.neto))} (ROI: ${rfSign}${reforma.roiReal}%). La rentabilidad es ajustada; puede compensar si se combina con home staging y presentación cuidada.`);
    } else {
      paragraphs.push(`El estado a reformar reduce el universo de compradores potenciales en un 35–45%. En ${m.label}, el precio de venta no absorbe el coste de reforma básica (${eur(reforma.costeBasica)} de inversión frente a ${eur(reforma.revalBasica)} de revalorización, ROI: ${reforma.roiReal}%). La estrategia óptima es ajustar el precio de salida sin acometer obras significativas.`);
    }
  } else if (d.estado === 'reformar') {
    paragraphs.push(`El estado a reformar reduce el universo de compradores potenciales en un 35–45%, al dirigirse principalmente a inversores o compradores con capacidad de obra. El precio de venta incorpora ya ese descuento de mercado (−18% aproximado). Una reforma básica (pintura, limpieza, pequeñas reparaciones) puede recuperar entre un 8–12% de ese descuento con una inversión reducida.`);
  }

  if (d.estado === 'nueva') {
    paragraphs.push(`El estado de obra nueva o muy reciente posiciona el inmueble en la franja premium del mercado local. Los compradores perciben este tipo de producto con mayor valor y menor negociación. Es el estado con mayor liquidez y menor tiempo de venta.`);
  }

  const urgentFlag = isUrgent(d);
  if (urgentFlag) {
    paragraphs.push(`El perfil del propietario indica urgencia o motivación fuerte (${d.motivo === 'necesidad' ? 'necesidad económica' : d.motivo === 'divorcio' ? 'divorcio/separación' : d.motivo === 'traslado' ? 'traslado' : 'plazo inmediato'}). En estos casos, la estrategia de precio debe ser más ajustada al mercado real: salir con precio competitivo es más efectivo que un precio aspiracional que prolongue el plazo.`);
  }

  if (desired > base * 1.15) {
    const overpct = Math.round((desired / base - 1) * 100);
    paragraphs.push(`Precio deseado con desajuste significativo: el precio que tienes en mente (${eur(desired)}) está un ${overpct}% por encima de la estimación de mercado (${eur(base)}). Los inmuebles con sobreprecio inicial generan menos visitas y visibilidad en los primeros días —el momento clave— y suelen terminar vendiéndose a precios más bajos que si hubieran salido correctamente desde el principio.`);
  }

  return { demandLabel, demandLevel, liquidityLabel, liquidityDays, liquidityLevel, stateLabel, stateLevel, priceLabel, priceLevel, paragraphs };
}

// ─── 12. STRATEGY GENERATOR ────────────────────────────────
function generateStrategy(d, m, base, rec, diag, reforma) {
  const urgent   = isUrgent(d);
  const tourist  = m.tourist;
  const lowDemand = m.base < 1200;
  const reformar = d.estado === 'reformar';
  const desired  = parseFloat(d.precioDeseado) || 0;

  // Recommended exit price
  let recommendedPrice;
  if (reformar && urgent)  recommendedPrice = snap(base * 0.92, 500);
  else if (urgent)          recommendedPrice = snap(base * 0.96, 500);
  else if (d.estado === 'nueva' || d.extras.includes('vistas')) recommendedPrice = snap(base * 1.03, 500);
  else                      recommendedPrice = base;

  // What to improve
  const improvements = [];
  if (reformar && reforma) {
    if (reforma.scenario === 'rentable') {
      improvements.push({ icon:'paint', text:`Reforma básica recomendada: inversión estimada ${eur(reforma.costeBasica)} → revalorización ${eur(reforma.revalBasica)} (ROI ${reforma.roiReal > 0 ? '+' : ''}${reforma.roiReal}% en ${m.label})` });
      if (reforma.roiCocina > 15) improvements.push({ icon:'fix', text:`Reforma de cocina especialmente rentable en esta zona (ROI ${reforma.roiCocina}%) — alta demanda de compradores exigentes` });
      improvements.push({ icon:'stage', text:`Home staging: ROI estimado ${reforma.roiHS}% — muy alto retorno con inversión mínima en ${m.label}` });
    } else if (reforma.scenario === 'borderline') {
      improvements.push({ icon:'paint', text:`Reforma básica ajustada: ${eur(reforma.costeBasica)} de inversión para recuperar ${eur(reforma.revalBasica)} — margen neto ${reforma.neto >= 0 ? eur(reforma.neto) : '−'+eur(Math.abs(reforma.neto))}` });
      improvements.push({ icon:'stage', text:`Home staging prioritario (ROI ${reforma.roiHS}%) — máximo impacto con mínima inversión en presentación` });
      improvements.push({ icon:'fix',   text:'Verificar instalaciones básicas (electricidad, fontanería) para neutralizar objeciones en visita' });
    } else {
      improvements.push({ icon:'paint', text:'Pintura y limpieza profunda — inversión de 800–1.500€ mínima para mejorar presentación sin reforma integral' });
      improvements.push({ icon:'stage', text:`Home staging: ROI estimado ${reforma.roiHS}% — la mejor palanca disponible en este mercado` });
      improvements.push({ icon:'fix',   text:'Ajustar precio de salida descontando el estado: la reforma no se recupera en esta zona, el precio correcto es la mejor estrategia' });
    }
  } else if (reformar) {
    improvements.push({ icon:'paint', text:'Pintura general y limpieza profunda — inversión de 1.500–3.000€ con alto retorno en presentación' });
    improvements.push({ icon:'fix',   text:'Verificar instalaciones básicas (electricidad, fontanería) para neutralizar objeciones en visita' });
  } else if (d.estado === 'bueno') {
    improvements.push({ icon:'camera', text:'Fotografía profesional con gran angular y postproducción — diferencia del 15–25% en visitas recibidas' });
    improvements.push({ icon:'stage',  text:'Home staging básico: despersonalizar, mejorar iluminación, pequeños arreglos visibles' });
    if (reforma && reforma.roiHS > 100) improvements.push({ icon:'stage', text:`Home staging especialmente efectivo en ${m.label} (ROI estimado ${reforma.roiHS}%) — no subestimar este paso` });
  } else {
    improvements.push({ icon:'docs',  text:'Documentación completa y certificado energético actualizado para evitar fricciones en proceso' });
    improvements.push({ icon:'pos',   text:'Comunicación activa del estado de obra nueva y sus ventajas frente a inmuebles más antiguos' });
  }
  if (!d.extras.includes('parking') && m.urban) {
    improvements.push({ icon:'park', text:'La ausencia de parking en zona urbana puede ser objeción — tenerlo en cuenta en el precio de salida' });
  }

  // Buyer profile
  let buyerProfile;
  if (reformar && lowDemand) {
    buyerProfile = 'Inversor de oportunidad con capital disponible para obra. Perfil profesionalizado, no comprador de uso propio.';
  } else if (reformar) {
    buyerProfile = 'Inversor privado o comprador con presupuesto para reforma. Busca rentabilidad o adaptación a medida. Negocia más, pero cierra si el precio es claro.';
  } else if (tourist) {
    buyerProfile = 'Inversor vacacional (nacional o europeo), familia buscando segunda residencia o perfil de jubilación activa. Sensible a potencial de alquiler.';
  } else if (base > 280000) {
    buyerProfile = 'Familia en mejora de vivienda, directivo o profesional liberal con capacidad de compra sin financiación completa.';
  } else {
    buyerProfile = 'Primera vivienda con financiación bancaria (hasta 80% LTV) o perfil de mejora. Muy sensible al precio de salida y al estado del inmueble.';
  }

  // Approach
  let approach;
  if (d.inmobiliaria === 'exclusiva') {
    approach = 'Revisar condiciones y duración de la exclusiva actual. Si permite complementar, activar difusión adicional. Valorar negociar término anticipado si el servicio no está siendo efectivo.';
  } else if (reformar || lowDemand) {
    approach = 'Contacto directo con inversores y network privado. Portales especializados en reforma. Considerar subasta o precio cerrado para acelerar operación.';
  } else if (tourist) {
    approach = 'Portales nacionales con énfasis en potencial vacacional. Portales internacionales (Rightmove, A Place in the Sun) para captar comprador europeo. Red de contactos con inversores turísticos.';
  } else {
    approach = 'Posicionamiento en Idealista y Fotocasa con precio de salida correcto desde el día 1. Fotografía profesional obligatoria. Red de compradores activos como canal preferente.';
  }

  // Main risk
  let mainRisk;
  if (desired > base * 1.15) {
    mainRisk = `Precio de salida sobrevalorado (${Math.round((desired/base-1)*100)}% sobre mercado). Riesgo: caída de interés en los primeros días de publicación, negociaciones desde debilidad y precio final menor al que se obtendría saliendo bien posicionado desde el inicio.`;
  } else if (reformar && urgent) {
    mainRisk = 'Urgencia + estado a reformar = presión de precio. Los compradores de reforma negocian agresivamente cuando detectan necesidad de venta. El precio de salida realista mitiga este efecto.';
  } else if (d.hipoteca === 'alta') {
    mainRisk = 'La carga hipotecaria alta puede limitar el margen de negociación. Calcular el neto real después de cancelación de hipoteca, comisión e impuestos (plusvalía) antes de fijar precio mínimo aceptable.';
  } else if (d.inmobiliaria === 'exclusiva') {
    mainRisk = 'La exclusiva puede limitar canales de venta. Verificar duración, qué incluye y qué penalizaciones contempla su ruptura anticipada. Una mala exclusiva en el momento equivocado cuesta semanas de inactividad.';
  } else if (lowDemand) {
    mainRisk = 'Menor absorción del mercado local. El efecto "quemado" — inmueble tiempo en portales sin venderse — es más dañino en zonas de baja demanda. Precio correcto desde el inicio es crítico.';
  } else {
    mainRisk = 'Posicionamiento de precio incorrecto en los primeros 15 días de publicación. Es el período de mayor visibilidad. Un precio optimista puede desperdiciar esta ventana y requerir bajadas posteriores.';
  }

  // Next step
  let nextStep;
  if (urgent) {
    nextStep = 'Contacto en las próximas 24 horas para definir precio de salida y activar canales de venta de forma inmediata. El tiempo es un factor crítico en tu caso.';
  } else if (d.intencion === 'valorar' || d.intencion === 'nose') {
    nextStep = 'Visita al inmueble para valoración más precisa y presentación de un plan de opciones concreto. Sin compromiso. En menos de 48 horas.';
  } else if (rec === 'reformar') {
    nextStep = 'Reunión para revisar qué reformas tienen mayor retorno en tu caso específico y cuánto costaría. Con esos datos, decidir si reformar es financieramente rentable.';
  } else {
    nextStep = 'Reunión de análisis para revisar datos, ajustar estrategia de precio y definir el plan de acción con calendario. Agenda cuando quieras.';
  }

  return { recommendedPrice, improvements, buyerProfile, approach, mainRisk, nextStep };
}

// ─── 13. LEAD PROFILE ──────────────────────────────────────
function generateLeadProfile(d, base, desired) {
  // Urgency (1–5)
  let urgency = { inmediato:5, '1a3':4, '3a6':3, '6a12':2, sinprisa:1 }[d.plazo] || 2;
  if (['necesidad','divorcio','traslado'].includes(d.motivo)) urgency = Math.min(5, urgency + 1);

  // Price realism (1–5)
  let priceRealism = 3;
  if (desired > 0) {
    const r = desired / base;
    if (r <= 1.00) priceRealism = 5;
    else if (r <= 1.05) priceRealism = 4;
    else if (r <= 1.12) priceRealism = 3;
    else if (r <= 1.20) priceRealism = 2;
    else priceRealism = 1;
  }

  // Motivation (1–5)
  const intentMap = { vender:5, alquilar:4, reformar:3, valorar:2, nose:2 };
  let motivation = intentMap[d.intencion] || 2;
  if (['necesidad','divorcio','traslado','herencia'].includes(d.motivo)) motivation = Math.min(5, motivation + 1);

  // Contactability (1–5)
  let contactability = 2;
  if (d.telefono && d.telefono.trim().length > 8) contactability += 2;
  if (d.email) contactability += 1;
  if (['whatsapp','llamada'].includes(d.preferenciaContacto)) contactability = Math.min(5, contactability + 1);

  // Agency penalty
  const agencyDelta = d.inmobiliaria === 'exclusiva' ? -2 : d.inmobiliaria === 'sinexclusiva' ? -1 : d.inmobiliaria === 'ninguna' ? 1 : 0;

  // Overall score
  const raw = urgency * 20 + priceRealism * 15 + motivation * 20 + contactability * 15 + Math.max(0, agencyDelta * 8) + 10;
  const score = Math.max(0, Math.min(100, raw));

  let tier, tierLabel, tierExplanation;
  if (score >= 72)      { tier='hot';  tierLabel='Situación de alta prioridad — te conviene actuar pronto';      tierExplanation='Tu situación muestra señales claras de urgencia o motivación fuerte. Actuar con una estrategia bien definida marcará la diferencia.'; }
  else if (score >= 45) { tier='warm'; tierLabel='Situación en desarrollo — vale la pena prepararse';            tierExplanation='Hay intención real, pero el proceso de decisión sigue abierto. Un análisis más detallado puede darte más claridad antes de actuar.'; }
  else                  { tier='cold'; tierLabel='Sin urgencia inmediata — tienes margen para analizar';         tierExplanation='No hay presión inmediata. Puedes tomarte el tiempo necesario para explorar las opciones con datos reales del mercado.'; }

  return { urgency, priceRealism, motivation, contactability, score, tier, tierLabel, tierExplanation };
}

// ─── 14a. STRATEGY BARS ────────────────────────────────────
function calcStrategyBars(d, m, result) {
  const desired    = parseFloat(d.precioDeseado) || 0;
  const base       = result.base;
  const urgent     = isUrgent(d);
  const tourist    = m.tourist;
  const lowDemand  = m.base < 1200;
  const highDemand = m.base >= 1700;
  const reformar   = d.estado === 'reformar';
  const nueva      = d.estado === 'nueva';
  const diag       = result.diagnosis;

  // Liquidez (0–100)
  const liquidityMap = { 3:90, 2:60, 1:30 };
  let liquidez = liquidityMap[diag.liquidityLevel] || 60;
  if (nueva) liquidez = Math.min(100, liquidez + 10);

  // Riesgo sobreprecio (0–100)
  let riesgo = 20;
  if (desired > 0) {
    const ratio = desired / base;
    if (ratio > 1.25)      riesgo = 95;
    else if (ratio > 1.15) riesgo = 75;
    else if (ratio > 1.08) riesgo = 50;
    else if (ratio > 1.00) riesgo = 30;
    else                   riesgo = 10;
  } else {
    riesgo = reformar ? 55 : lowDemand ? 45 : 20;
  }

  // Potencial venta (0–100)
  let potVenta = 60;
  if (highDemand || tourist) potVenta = 85;
  if (lowDemand)             potVenta = 40;
  if (nueva)                 potVenta = Math.min(100, potVenta + 15);
  if (reformar)              potVenta = Math.max(25, potVenta - 20);
  if (urgent)                potVenta = Math.min(100, potVenta + 10);

  // Potencial alquiler (0–100)
  let potAlquiler = 55;
  if (tourist)    potAlquiler = 88;
  if (m.urban)    potAlquiler = 70;
  if (lowDemand)  potAlquiler = 35;
  if (nueva)      potAlquiler = Math.min(100, potAlquiler + 12);
  if (reformar)   potAlquiler = Math.max(30, potAlquiler - 15);

  // Potencial reforma (0–100) — derived from real ROI data
  let potReforma;
  if (result.reforma) {
    potReforma = Math.max(5, Math.min(98, Math.round(40 + result.reforma.roiReal * 0.5)));
  } else {
    potReforma = 50;
    if (reformar)              potReforma = 82;
    else if (d.estado === 'bueno') potReforma = 42;
    else                       potReforma = 18;
    if (tourist || highDemand) potReforma = Math.min(100, potReforma + 10);
    if (lowDemand)             potReforma = Math.max(20, potReforma - 15);
  }

  // Urgencia estratégica (0–100)
  const urgencyMap = { inmediato:95, '1a3':75, '3a6':55, '6a12':35, sinprisa:15 };
  let urgencia = urgencyMap[d.plazo] || 40;
  if (['necesidad','divorcio','traslado'].includes(d.motivo)) urgencia = Math.min(100, urgencia + 15);

  // ── Ajustes por intención del propietario ───────────
  if (d.intencion === 'alquilar') {
    potAlquiler = Math.min(100, potAlquiler + 20);
    potVenta    = Math.max(20,  potVenta    - 10);
  }
  if (d.intencion === 'vender') {
    potVenta  = Math.min(100, potVenta + 8);
    urgencia  = Math.min(100, urgencia + 10);
  }
  // Sin decisión clara → normalizar al rango medio
  if (d.intencion === 'nose' || d.intencion === 'valorar') {
    potVenta    = Math.max(35, Math.min(60, potVenta));
    potAlquiler = Math.max(35, Math.min(60, potAlquiler));
    potReforma  = Math.max(30, Math.min(55, potReforma));
    urgencia    = Math.max(15, urgencia - 20);
  }

  // ── Hipoteca alta → mayor urgencia ──────────────────
  if (d.hipoteca === 'alta') urgencia = Math.min(100, urgencia + 15);

  // ── Liquidez: ajuste por estado ─────────────────────
  if (reformar) liquidez = Math.max(15, liquidez - 15);

  return { liquidez, riesgo, potVenta, potAlquiler, potReforma, urgencia };
}

// ─── 14b. 7-DAY PLAN ───────────────────────────────────────
function generate7DayPlan(d, m, result) {
  const urgent    = isUrgent(d);
  const tourist   = m.tourist;
  const lowDemand = m.base < 1200;
  const reformar  = d.estado === 'reformar';
  const rec       = result.recommendation;
  const strat     = result.strategy;

  const steps = [];

  // Day 1 always: call/meeting
  if (urgent) {
    steps.push({
      day: 'Día 1',
      title: 'Contacto inmediato',
      desc: 'Llamada o WhatsApp para definir situación real y mínimo aceptable. La urgencia requiere activar canales en menos de 48 horas.'
    });
  } else {
    steps.push({
      day: 'Día 1',
      title: 'Reunión de análisis',
      desc: `Visita al inmueble en ${m.label} para afinar valoración, detectar puntos fuertes y acordar estrategia de precio concreta.`
    });
  }

  // Day 2-3: prep / docs
  if (reformar) {
    steps.push({
      day: 'Días 2–3',
      title: 'Evaluar inversión en presentación',
      desc: 'Presupuesto de pequeña reforma estética (pintura, limpieza, reparaciones menores). Decidir si el retorno justifica la inversión.'
    });
  } else {
    steps.push({
      day: 'Días 2–3',
      title: 'Documentación y presentación',
      desc: 'Certificado energético, nota simple, fotos profesionales y descripción de valor. El material de presentación impacta directamente en precio final.'
    });
  }

  // Day 4-5: market activation
  if (tourist) {
    steps.push({
      day: 'Días 4–5',
      title: 'Activación en canales clave',
      desc: 'Publicación en portales nacionales e internacionales con énfasis en potencial vacacional y rentabilidad para inversores europeos.'
    });
  } else if (lowDemand) {
    steps.push({
      day: 'Días 4–5',
      title: 'Difusión en red privada',
      desc: 'Activar contactos de inversores y red off-market. En mercados de menor demanda, los compradores correctos raramente llegan solo por portales.'
    });
  } else if (rec === 'alquilar') {
    steps.push({
      day: 'Días 4–5',
      title: 'Preparar activo para alquiler',
      desc: 'Pequeños ajustes de presentación para maximizar precio de alquiler. Definir si alquiler de larga duración o vacacional es más rentable en tu caso.'
    });
  } else {
    steps.push({
      day: 'Días 4–5',
      title: 'Lanzamiento al mercado',
      desc: `Publicación con precio de salida correcto (${eur(strat.recommendedPrice)}) en Idealista y Fotocasa. El posicionamiento desde el día 1 define el 80% del éxito.`
    });
  }

  // Day 7: review
  steps.push({
    day: 'Día 7',
    title: 'Primera lectura de mercado',
    desc: 'Revisión de métricas (visitas, contactos, ratio de interés). Si el mercado no responde en la primera semana, ajustar estrategia antes de que el inmueble se "queme".'
  });

  return steps;
}

// ─── 14c. VENDER VS ALQUILAR ───────────────────────────────
function generateVsComparison(d, m, r) {
  const sellPrice  = r.base;
  const sellNet    = Math.round(sellPrice * 0.92);
  const rentMonth  = r.rent;
  const rentAnnual = rentMonth * 12;
  const rentYears  = (sellPrice / rentAnnual).toFixed(1);
  const yieldPct   = m.rentBruta ? m.rentBruta : +((rentAnnual / sellPrice) * 100).toFixed(1);

  const daysLabel  = r.diagnosis.liquidityDays || '40-65 días';

  let sellMoment;
  if (r.recommendation === 'reformar')  sellMoment = 'Después de reforma selectiva';
  else if (isUrgent(d))                  sellMoment = 'Inmediato — actuar ya es la mejor estrategia';
  else if (d.estado === 'nueva')         sellMoment = 'Ahora — precio y demanda a tu favor';
  else                                   sellMoment = 'Con precio correcto desde el primer día';

  let vsRec, vsRecType;
  if (yieldPct > 6) {
    vsRec    = `El alquiler ofrece buena rentabilidad en tu zona (${yieldPct.toFixed(1)}%). Vale la pena comparar opciones antes de decidir.`;
    vsRecType = 'neutral';
  } else if (yieldPct < 4) {
    vsRec    = `La venta puede ser más interesante que el alquiler en tu zona. La rentabilidad estimada del ${yieldPct.toFixed(1)}% es relativamente baja.`;
    vsRecType = 'sell';
  } else {
    vsRec    = `Ambas opciones son viables (rentabilidad estimada ${yieldPct.toFixed(1)}%). La decisión depende de tu situación personal y horizonte temporal.`;
    vsRecType = 'neutral';
  }

  return { sellPrice, sellNet, daysLabel, sellMoment, rentMonth, rentAnnual, rentYears, yieldPct, vsRec, vsRecType };
}

// ─── 14. RENDER RESULTS ────────────────────────────────────
function renderResults() {
  const r = QS.result;
  if (!r) return;
  const d = QS.d;
  const lp = r.leadProfile;
  const diag = r.diagnosis;
  const strat = r.strategy;

  // Timestamp
  const ts = document.getElementById('r-timestamp');
  if (ts) ts.textContent = `Generado el ${new Date().toLocaleDateString('es-ES', {day:'2-digit', month:'long', year:'numeric'})} · ${r.muniLabel}`;

  // Lead tier badge
  const tierEl = document.getElementById('r-tier');
  const tierMap = { hot:'tier-hot', warm:'tier-warm', cold:'tier-cold' };
  if (tierEl) {
    tierEl.className = `tier-badge ${tierMap[lp.tier] || 'tier-warm'}`;
    tierEl.textContent = lp.tierLabel;
  }

  // ── RESULT CAPSULE ────────────────────────────────────
  setText('rc-rec',   r.recLabel || '—');
  setText('rc-price', r.base ? eur(r.base) : '—');
  setText('rc-conf',  r.confidence ? r.confidence + '%' : '—');

  // ── SECTION A: Valoración ─────────────────────────────
  animNum(document.getElementById('r-price'), r.base, 1600);
  setText('r-range', `${eur(r.lo)} — ${eur(r.hi)}`);
  setText('r-ppm2', `${r.ppm2.toLocaleString('es-ES')} €/m²`);
  setText('r-conf-pct', 'Precisión: Alta · Datos 2026');
  animBar(document.getElementById('r-conf-bar'), r.confidence, 500);
  setText('r-rent', eur(r.rent) + '/mes');
  setText('r-rent-range', `Horquilla alquiler: ${eur(r.rentLo)} – ${eur(r.rentHi)}/mes`);

  // Precio de salida según plazo
  if (r.precioSalida) {
    setText('r-precio-salida', eur(r.precioSalida));
    const plazoMap = { inmediato:'Urgente (×0.94) — venta en 20-35 días', '1a3':'Plazo 1-3 meses (×0.97) — venta en 35-55 días', '3a6':'Plazo 3-6 meses (×0.99) — venta en 60-90 días', '6a12':'Plazo 6-12 meses (×1.00)', sinprisa:'Sin prisa (×1.02) — venta en 90-150 días' };
    setText('r-precio-salida-plazo', plazoMap[d.plazo] || 'Ajustado según plazo seleccionado');
  }

  // Desglose del cálculo
  const dsg = r.desglose;
  if (dsg) {
    const extraLines = dsg.extrasItems.length
      ? dsg.extrasItems.map(e => {
          let mainLine;
          if (e.exacta) {
            mainLine = `+ Terraza ${e.m2}m² (${e.m2} × ${e.baseM2}€ × 0.25): +${eur(e.valor)}`;
          } else {
            const label = (EXTRA_LABELS[e.extra] || e.extra).padEnd(22);
            if (e.penalty) {
              mainLine = `− ${label} (${e.basePct}%): ${eur(e.valor)}`;
            } else {
              const pctStr = e.cascadePct === 100 ? `+${e.basePct}%` : `+${e.basePct}% × ${e.cascadePct}%`;
              mainLine = `+ ${label} (${pctStr}): +${eur(e.valor)}`;
            }
          }
          const note = EXTRAS_NOTES[e.extra];
          return note ? `${mainLine}\n  ↳ ${note}` : mainLine;
        }).join('\n')
      : '  (sin extras)';
    const desgloseHtml = `<pre style="font-size:11px;line-height:1.7;white-space:pre-wrap;">Valor base (${dsg.m2}m² × ${dsg.baseM2}€/m²):  ${eur(dsg.valorBase)}\n${extraLines}\n${'─'.repeat(42)}\nValor estimado:                    ${eur(r.base)}\nHorquilla:          ${eur(r.lo)} — ${eur(r.hi)}\nPrecio de salida:                  ${eur(r.precioSalida)}</pre>`;
    setHTML('r-desglose-body', desgloseHtml);
  }

  // ── SECTION B: Diagnóstico ─────────────────────────────
  setHTML('r-demand-label', diag.demandLabel);
  setHTML('r-liquidity-label', `${diag.liquidityLabel} · ${diag.liquidityDays}`);
  setHTML('r-state-label', diag.stateLabel);
  setHTML('r-price-label', diag.priceLabel);
  animBar(document.getElementById('r-demand-bar'),    [33,66,100][diag.demandLevel-1],    600);
  animBar(document.getElementById('r-liquidity-bar'), [33,66,100][diag.liquidityLevel-1], 700);
  animBar(document.getElementById('r-state-bar'),     [33,66,100][diag.stateLevel-1],     800);
  animBar(document.getElementById('r-price-bar'),     [33,66,100][diag.priceLevel-1],     900);
  setBarColor('r-demand-bar',    diag.demandLevel);
  setBarColor('r-liquidity-bar', diag.liquidityLevel);
  setBarColor('r-state-bar',     diag.stateLevel);
  setBarColor('r-price-bar',     diag.priceLevel);

  const diagText = document.getElementById('r-diag-text');
  if (diagText) {
    diagText.innerHTML = diag.paragraphs.map(p => `<p class="text-[var(--text-2)] text-sm leading-relaxed mb-3 last:mb-0">${p}</p>`).join('');
  }

  // ── SECTION C: Recomendación ───────────────────────────
  setText('r-rec-label', r.recLabel);
  setText('r-rec-tag', r.recTag);

  // ── SECTION D: Estrategia ──────────────────────────────
  setText('r-rec-price', eur(strat.recommendedPrice));
  setText('r-buyer-profile', strat.buyerProfile);
  setText('r-approach', strat.approach);
  setText('r-main-risk', strat.mainRisk);
  setText('r-next-step', strat.nextStep);

  const improvList = document.getElementById('r-improvements');
  if (improvList) {
    improvList.innerHTML = strat.improvements.map(item => `
      <li class="flex items-start gap-3 py-2.5 border-b border-[var(--border)] last:border-0">
        <span class="strategy-icon flex-shrink-0">
          <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" class="text-[var(--gold)]"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>
        </span>
        <span class="text-[var(--text-2)] text-sm leading-relaxed">${item.text}</span>
      </li>`).join('');
  }

  // ── REFORMA BLOCK ─────────────────────────────────────
  const rfBlock = document.getElementById('r-reforma-block');
  if (rfBlock && r.reforma) {
    const rf = r.reforma;
    const scenarioMap = {
      rentable:    { badge:'✅ Reforma RENTABLE',    cls:'rf-rentable',    bg:'bg-green-900/30',  border:'border-green-700/40' },
      borderline:  { badge:'⚠️ Reforma BORDERLINE', cls:'rf-borderline',  bg:'bg-yellow-900/30', border:'border-yellow-700/40' },
      no_rentable: { badge:'❌ Reforma NO RENTABLE', cls:'rf-no-rentable', bg:'bg-red-900/30',    border:'border-red-700/40' },
    };
    const sc = scenarioMap[rf.scenario] || scenarioMap['borderline'];
    const sign = rf.neto >= 0 ? '+' : '−';
    rfBlock.innerHTML = `
      <div class="reforma-section border ${sc.border} ${sc.bg} rounded-xl p-4 mt-4">
        <div class="flex items-center gap-3 mb-3">
          <span class="reforma-badge ${sc.cls} text-sm font-semibold px-3 py-1 rounded-full">${sc.badge}</span>
          <span class="text-[var(--text-3)] text-xs">${r.muniLabel} · ${d.m2 || 80} m²</span>
        </div>
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-3">
          <div class="rf-metric">
            <div class="rf-metric-label">Coste reforma básica</div>
            <div class="rf-metric-value">${eur(rf.costeBasica)}</div>
          </div>
          <div class="rf-metric">
            <div class="rf-metric-label">Revalorización estimada</div>
            <div class="rf-metric-value">${eur(rf.revalBasica)}</div>
          </div>
          <div class="rf-metric">
            <div class="rf-metric-label">Neto reforma</div>
            <div class="rf-metric-value ${rf.neto >= 0 ? 'text-green-400' : 'text-red-400'}">${sign}${eur(Math.abs(rf.neto))}</div>
          </div>
          <div class="rf-metric">
            <div class="rf-metric-label">ROI reforma básica</div>
            <div class="rf-metric-value ${rf.roiReal >= 0 ? 'text-green-400' : 'text-red-400'}">${rf.roiReal > 0 ? '+' : ''}${rf.roiReal}%</div>
          </div>
        </div>
        <div class="grid grid-cols-3 gap-2 mb-3 text-center text-xs">
          <div class="rf-roi-item">
            <div class="rf-roi-label">ROI cocina</div>
            <div class="rf-roi-val ${rf.roiCocina >= 0 ? 'text-[var(--gold)]' : 'text-red-400'}">${rf.roiCocina > 0 ? '+' : ''}${rf.roiCocina}%</div>
          </div>
          <div class="rf-roi-item">
            <div class="rf-roi-label">ROI baño</div>
            <div class="rf-roi-val ${rf.roiBano >= 0 ? 'text-[var(--gold)]' : 'text-red-400'}">${rf.roiBano > 0 ? '+' : ''}${rf.roiBano}%</div>
          </div>
          <div class="rf-roi-item">
            <div class="rf-roi-label">ROI home staging</div>
            <div class="rf-roi-val text-[var(--gold)]">+${rf.roiHS}%</div>
          </div>
        </div>
        <p class="text-[var(--text-3)] text-xs leading-relaxed italic">${rf.notas}</p>
      </div>`;
    rfBlock.classList.remove('hidden');
  }

  // Overprice warning
  const warnEl = document.getElementById('r-overprice');
  if (warnEl) {
    if (r.overpriced) {
      warnEl.innerHTML = `<strong class="text-[#fdba74]">Aviso de sobreprecio:</strong> Tu precio deseado (${eur(r.desired)}) está un <strong>${r.overpricePct}% por encima</strong> de la estimación de mercado (${eur(r.base)}). Esto reducirá drásticamente las visitas en los primeros días de publicación, que son los más valiosos.`;
      warnEl.classList.remove('hidden');
    } else if (r.underpriced) {
      warnEl.innerHTML = `<strong>Nota:</strong> Tu precio deseado (${eur(r.desired)}) está por debajo de la estimación de mercado. Puedes vender más rápido, pero conviene analizar si estás dejando valor encima de la mesa.`;
      warnEl.classList.remove('hidden');
    } else {
      warnEl.classList.add('hidden');
    }
  }

  // ── SECTION E: Perfil de lead ──────────────────────────
  setHTML('lp-urgency-dots',    dots(lp.urgency,       5, 'red'));
  setHTML('lp-realism-dots',    dots(lp.priceRealism,  5, 'green'));
  setHTML('lp-motivation-dots', dots(lp.motivation,    5, 'blue'));
  setHTML('lp-contact-dots',    dots(lp.contactability,5, 'gold'));
  setText('lp-tier-label',      lp.tierLabel);
  setText('lp-tier-explanation',lp.tierExplanation);
  animBar(document.getElementById('lp-score-bar'), lp.score, 800);

  // ── VS: Vender vs Alquilar ────────────────────────────
  const vs = generateVsComparison(d, r.muni, r);
  setText('vs-sell-price',   eur(vs.sellPrice));
  setText('vs-sell-net',     eur(vs.sellNet));
  setText('vs-sell-days',    vs.daysLabel);
  setText('vs-sell-moment',  vs.sellMoment);
  setText('vs-rent-month',   eur(vs.rentMonth) + '/mes');
  setText('vs-rent-annual',  eur(vs.rentAnnual) + '/año');
  setText('vs-rent-years',   vs.rentYears + ' años');
  setText('vs-rent-yield',   vs.yieldPct.toFixed(1) + '%');
  const vsRecEl = document.getElementById('vs-recommendation');
  if (vsRecEl) {
    vsRecEl.textContent = vs.vsRec;
    vsRecEl.className   = 'vs-rec vs-rec-' + vs.vsRecType;
  }

  // ── SECTION F: Strategy bars ──────────────────────────
  const bars = calcStrategyBars(d, r.muni, r);
  const pctLabel = v => Math.round(v) + '%';
  function animRB(id, valId, pct, delay) {
    const fill = document.getElementById(id);
    const val  = document.getElementById(valId);
    if (fill) setTimeout(() => { fill.style.width = pct + '%'; }, delay);
    if (val)  setTimeout(() => { val.textContent  = pctLabel(pct); }, delay + 200);
  }
  animRB('rb-liquidez',  'rb-liquidez-val',  bars.liquidez,    700);
  animRB('rb-riesgo',    'rb-riesgo-val',    bars.riesgo,      800);
  animRB('rb-venta',     'rb-venta-val',     bars.potVenta,    900);
  animRB('rb-alquiler',  'rb-alquiler-val',  bars.potAlquiler, 1000);
  animRB('rb-reforma',   'rb-reforma-val',   bars.potReforma,  1100);
  animRB('rb-urgencia',  'rb-urgencia-val',  bars.urgencia,    1200);

  // ── SECTION G: 7-day plan ─────────────────────────────
  const plan = generate7DayPlan(d, r.muni, r);
  const planEl = document.getElementById('r-plan-7');
  if (planEl) {
    planEl.innerHTML = plan.map((step, i) => `
      <div class="day-item">
        <div class="day-num">${i + 1}</div>
        <div class="day-body">
          <div class="day-title">${step.day} · ${step.title}</div>
          <p class="day-desc">${step.desc}</p>
        </div>
      </div>`).join('');
  }

  // ── CTAs ───────────────────────────────────────────────
  const nombre = d.nombre ? d.nombre + ' — ' : '';
  const msg = `Hola Aleix, ${nombre}acabo de completar tu diagnóstico inmobiliario. ${r.muniLabel}, ${d.tipo || 'propiedad'} de ${d.m2 || '—'} m², estado: ${d.estado || 'no indicado'}. Estimación: ${eur(r.base)}. Recomendación: ${r.recLabel}. Me gustaría analizar mi caso contigo.`;
  const wa = document.getElementById('r-whatsapp');
  if (wa) wa.href = `https://wa.me/34600000000?text=${encodeURIComponent(msg)}`;
}

// ─── Helpers ────────────────────────────────────────────────
function setText(id, val) { const el = document.getElementById(id); if (el) el.textContent = val; }
function setHTML(id, val) { const el = document.getElementById(id); if (el) el.innerHTML = val; }
function setBarColor(id, level) {
  const el = document.getElementById(id); if (!el) return;
  const colors = ['#f87171', '#c9a84c', '#34d399'];
  el.style.background = colors[level - 1] || colors[1];
}

// ─── 15. RESET ─────────────────────────────────────────────
function resetQuiz() {
  QS.step = 1; QS.result = null;
  QS.d = { municipio:'', zona:'', calle:'', numero:'', piso:'', codigoPostal:'', tipo:'', m2:'', habitaciones:3, banos:1, anio:'', planta:'1a3', ascensor:'', estado:'', extras:[], intencion:'', plazo:'', motivo:'', precioDeseado:'', hipoteca:'', inmobiliaria:'', nombre:'', email:'', telefono:'', preferenciaContacto:'', relacion:'', comentarios:'' };
  const barrioSel = document.getElementById('barrio-select');
  if (barrioSel) { barrioSel.innerHTML = '<option value="">— Selecciona primero el municipio —</option>'; barrioSel.disabled = true; }
  document.querySelectorAll('.q-card, .q-tag').forEach(el => el.classList.remove('selected'));
  document.querySelectorAll('#quiz-wrap input, #quiz-wrap textarea, #quiz-wrap select').forEach(el => { if (el.type !== 'button') el.value = ''; });
  document.querySelectorAll('.quiz-step').forEach(el => el.classList.remove('qactive'));
  document.getElementById('step-1').classList.add('qactive');
  const ctrH = document.getElementById('ctr-habitaciones'); if (ctrH) ctrH.textContent = '3';
  const ctrB = document.getElementById('ctr-banos');        if (ctrB) ctrB.textContent = '1';
  const prevBtn = document.getElementById('quiz-prev'); if (prevBtn) prevBtn.style.visibility = 'hidden';
  const nextBtn = document.getElementById('quiz-next'); if (nextBtn) nextBtn.style.display = 'flex';
  updateProgress(1); clearQError(); updateSummaryPanel();
  const sb = document.getElementById('calc-sidebar');
  if (sb) sb.style.display = '';
  const cl = document.querySelector('.calc-layout');
  if (cl) cl.classList.remove('calc-full');
  document.getElementById('quiz-wrap').scrollIntoView({ behavior:'smooth', block:'start' });
}

// ─── 16. INIT ──────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.quiz-step').forEach(s => s.classList.remove('qactive'));
  const s1 = document.getElementById('step-1'); if (s1) s1.classList.add('qactive');
  const prevBtn = document.getElementById('quiz-prev'); if (prevBtn) prevBtn.style.visibility = 'hidden';
  updateProgress(1);
});
