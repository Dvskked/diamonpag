const YEAR = 2026;
const SEASON = 'Temporada 3';

const MONTHS = {
  enero: 1,
  febrero: 2,
  marzo: 3,
  abril: 4,
  mayo: 5,
  junio: 6,
  julio: 7,
  agosto: 8,
  septiembre: 9,
  octubre: 10,
  noviembre: 11,
  diciembre: 12
};

export function isoDate(label) {
  const m = String(label).match(/(\d{2})\/(\d{2})/);
  if (!m) return '';
  const day = m[1];
  const month = m[2];
  return `${YEAR}-${month}-${day}`;
}

export function time24(label) {
  const raw = String(label).trim().toUpperCase();
  const m = raw.match(/(\d{1,2}):(\d{2})\s*(AM|PM)?/);
  if (!m) return '';
  let hour = Number(m[1]);
  const minute = m[2];
  const meridiem = m[3];
  if (meridiem === 'PM' && hour < 12) hour += 12;
  if (meridiem === 'AM' && hour === 12) hour = 0;
  return `${String(hour).padStart(2, '0')}:${minute}`;
}

const D1_TEAMS = [
  'MASCAPITOS-FC',
  'KIOSCO-FC',
  'PEQUEÑOS-HERMANOS',
  'ORENSE',
  'SKYLINE-SC',
  'LIGA-DEPORTIVA-ALAJUELENSE',
  'KLOKAN-FC',
  'LEXINGTON',
  'FRC-CLUB',
  'PARCEROS-FC',
  'CHELSEA',
  'MYSTIC-STORM'
];

const D1_CALENDAR = [
  {
    journey: 1,
    range: '03/08 · 04/08',
    matches: [
      ['Lunes 03/08', '7:00 PM', 'MASCAPITOS-FC', 'KIOSCO-FC'],
      ['Lunes 03/08', '7:45 PM', 'PEQUEÑOS-HERMANOS', 'ORENSE'],
      ['Lunes 03/08', '8:30 PM', 'SKYLINE-SC', 'LIGA-DEPORTIVA-ALAJUELENSE'],
      ['Martes 04/08', '7:00 PM', 'KLOKAN-FC', 'LEXINGTON'],
      ['Martes 04/08', '7:45 PM', 'FRC-CLUB', 'PARCEROS-FC'],
      ['Martes 04/08', '8:30 PM', 'CHELSEA', 'MYSTIC-STORM']
    ]
  },
  {
    journey: 2,
    range: '05/08 · 06/08',
    matches: [
      ['Miércoles 05/08', '7:00 PM', 'KIOSCO-FC', 'LIGA-DEPORTIVA-ALAJUELENSE'],
      ['Miércoles 05/08', '7:45 PM', 'PEQUEÑOS-HERMANOS', 'LEXINGTON'],
      ['Miércoles 05/08', '8:30 PM', 'SKYLINE-SC', 'PARCEROS-FC'],
      ['Jueves 06/08', '7:00 PM', 'KLOKAN-FC', 'MYSTIC-STORM'],
      ['Jueves 06/08', '7:45 PM', 'FRC-CLUB', 'CHELSEA'],
      ['Jueves 06/08', '8:30 PM', 'MASCAPITOS-FC', 'ORENSE']
    ]
  },
  {
    journey: 3,
    range: '10/08 · 11/08',
    matches: [
      ['Lunes 10/08', '7:00 PM', 'KIOSCO-FC', 'PARCEROS-FC'],
      ['Lunes 10/08', '7:45 PM', 'PEQUEÑOS-HERMANOS', 'MYSTIC-STORM'],
      ['Lunes 10/08', '8:30 PM', 'SKYLINE-SC', 'CHELSEA'],
      ['Martes 11/08', '7:00 PM', 'KLOKAN-FC', 'FRC-CLUB'],
      ['Martes 11/08', '7:45 PM', 'MASCAPITOS-FC', 'LIGA-DEPORTIVA-ALAJUELENSE'],
      ['Martes 11/08', '8:30 PM', 'ORENSE', 'LEXINGTON']
    ]
  },
  {
    journey: 4,
    range: '12/08 · 13/08',
    matches: [
      ['Miércoles 12/08', '7:00 PM', 'KIOSCO-FC', 'CHELSEA'],
      ['Miércoles 12/08', '7:45 PM', 'PEQUEÑOS-HERMANOS', 'FRC-CLUB'],
      ['Miércoles 12/08', '8:30 PM', 'SKYLINE-SC', 'KLOKAN-FC'],
      ['Jueves 13/08', '7:00 PM', 'MASCAPITOS-FC', 'LEXINGTON'],
      ['Jueves 13/08', '7:45 PM', 'LIGA-DEPORTIVA-ALAJUELENSE', 'PARCEROS-FC'],
      ['Jueves 13/08', '8:30 PM', 'ORENSE', 'MYSTIC-STORM']
    ]
  },
  {
    journey: 5,
    range: '17/08 · 18/08',
    matches: [
      ['Lunes 17/08', '7:00 PM', 'KIOSCO-FC', 'KLOKAN-FC'],
      ['Lunes 17/08', '7:45 PM', 'PEQUEÑOS-HERMANOS', 'SKYLINE-SC'],
      ['Lunes 17/08', '8:30 PM', 'MASCAPITOS-FC', 'PARCEROS-FC'],
      ['Martes 18/08', '7:00 PM', 'LEXINGTON', 'MYSTIC-STORM'],
      ['Martes 18/08', '7:45 PM', 'LIGA-DEPORTIVA-ALAJUELENSE', 'CHELSEA'],
      ['Martes 18/08', '8:30 PM', 'ORENSE', 'FRC-CLUB']
    ]
  },
  {
    journey: 6,
    range: '19/08 · 20/08',
    matches: [
      ['Miércoles 19/08', '7:00 PM', 'KIOSCO-FC', 'PEQUEÑOS-HERMANOS'],
      ['Miércoles 19/08', '7:45 PM', 'MASCAPITOS-FC', 'MYSTIC-STORM'],
      ['Miércoles 19/08', '8:30 PM', 'PARCEROS-FC', 'CHELSEA'],
      ['Jueves 20/08', '7:00 PM', 'LEXINGTON', 'FRC-CLUB'],
      ['Jueves 20/08', '7:45 PM', 'LIGA-DEPORTIVA-ALAJUELENSE', 'KLOKAN-FC'],
      ['Jueves 20/08', '8:30 PM', 'ORENSE', 'SKYLINE-SC']
    ]
  },
  {
    journey: 7,
    range: '24/08 · 25/08',
    matches: [
      ['Lunes 24/08', '7:00 PM', 'MASCAPITOS-FC', 'CHELSEA'],
      ['Lunes 24/08', '7:45 PM', 'MYSTIC-STORM', 'FRC-CLUB'],
      ['Lunes 24/08', '8:30 PM', 'PARCEROS-FC', 'KLOKAN-FC'],
      ['Martes 25/08', '7:00 PM', 'LEXINGTON', 'SKYLINE-SC'],
      ['Martes 25/08', '7:45 PM', 'LIGA-DEPORTIVA-ALAJUELENSE', 'PEQUEÑOS-HERMANOS'],
      ['Martes 25/08', '8:30 PM', 'ORENSE', 'KIOSCO-FC']
    ]
  },
  {
    journey: 8,
    range: '26/08 · 27/08',
    matches: [
      ['Miércoles 26/08', '7:00 PM', 'CHELSEA', 'KLOKAN-FC'],
      ['Miércoles 26/08', '7:45 PM', 'MYSTIC-STORM', 'SKYLINE-SC'],
      ['Miércoles 26/08', '8:30 PM', 'PARCEROS-FC', 'PEQUEÑOS-HERMANOS'],
      ['Jueves 27/08', '7:00 PM', 'LEXINGTON', 'KIOSCO-FC'],
      ['Jueves 27/08', '7:45 PM', 'LIGA-DEPORTIVA-ALAJUELENSE', 'ORENSE'],
      ['Jueves 27/08', '8:30 PM', 'MASCAPITOS-FC', 'FRC-CLUB']
    ]
  },
  {
    journey: 9,
    range: '31/08 · 01/09',
    matches: [
      ['Lunes 31/08', '7:00 PM', 'CHELSEA', 'PEQUEÑOS-HERMANOS'],
      ['Lunes 31/08', '7:45 PM', 'MYSTIC-STORM', 'KIOSCO-FC'],
      ['Lunes 31/08', '8:30 PM', 'PARCEROS-FC', 'ORENSE'],
      ['Martes 01/09', '7:00 PM', 'LEXINGTON', 'LIGA-DEPORTIVA-ALAJUELENSE'],
      ['Martes 01/09', '7:45 PM', 'MASCAPITOS-FC', 'KLOKAN-FC'],
      ['Martes 01/09', '8:30 PM', 'FRC-CLUB', 'SKYLINE-SC']
    ]
  },
  {
    journey: 10,
    range: '02/09 · 03/09',
    matches: [
      ['Miércoles 02/09', '7:00 PM', 'CHELSEA', 'ORENSE'],
      ['Miércoles 02/09', '7:45 PM', 'MYSTIC-STORM', 'LIGA-DEPORTIVA-ALAJUELENSE'],
      ['Miércoles 02/09', '8:30 PM', 'PARCEROS-FC', 'LEXINGTON'],
      ['Jueves 03/09', '7:00 PM', 'MASCAPITOS-FC', 'SKYLINE-SC'],
      ['Jueves 03/09', '7:45 PM', 'KLOKAN-FC', 'PEQUEÑOS-HERMANOS'],
      ['Jueves 03/09', '8:30 PM', 'FRC-CLUB', 'KIOSCO-FC']
    ]
  },
  {
    journey: 11,
    range: '07/09 · 08/09',
    matches: [
      ['Lunes 07/09', '7:00 PM', 'CHELSEA', 'LEXINGTON'],
      ['Lunes 07/09', '7:45 PM', 'MYSTIC-STORM', 'PARCEROS-FC'],
      ['Lunes 07/09', '8:30 PM', 'MASCAPITOS-FC', 'PEQUEÑOS-HERMANOS'],
      ['Martes 08/09', '7:00 PM', 'SKYLINE-SC', 'KIOSCO-FC'],
      ['Martes 08/09', '7:45 PM', 'KLOKAN-FC', 'ORENSE'],
      ['Martes 08/09', '8:30 PM', 'FRC-CLUB', 'LIGA-DEPORTIVA-ALAJUELENSE']
    ]
  }
];

const PLAYOFFS = [
  { journey: 'SF1', date: '2026-09-10', time: '19:00', home: '1° D1', away: '4° D1' },
  { journey: 'SF2', date: '2026-09-10', time: '20:15', home: '2° D1', away: '3° D1' },
  { journey: 'FINAL (IDA)', date: '2026-09-13', time: '19:00', home: 'Ganador SF1', away: 'Ganador SF2' },
  { journey: 'FINAL (VUELTA)', date: '2026-09-14', time: '19:00', home: 'Ganador SF2', away: 'Ganador SF1' }
];

export function buildSeed() {
  const now = new Date().toISOString();

  const teams = [
    ...D1_TEAMS.map((name, i) => ({
      id: `d1-${i + 1}`,
      name,
      division: 'd1',
      coach: '',
      colors: ['', ''],
      note: ''
    })),
    { id: 'd2-1', name: 'DEPORTIVO PEREIRA', division: 'd2', coach: 'DT Inuv', colors: ['', ''], note: 'Campeón División 2 · Temporada 2' },
    { id: 'd2-2', name: 'KIOSKO FC', division: 'd2', coach: '', colors: ['', ''], note: 'Guante de Oro · Temporada 2' }
  ];

  let seq = 0;
  const matches = [];

  for (const round of D1_CALENDAR) {
    for (const [day, time, home, away] of round.matches) {
      seq += 1;
      matches.push({
        id: `md1-${seq}`,
        division: 'd1',
        stage: 'liga',
        journey: round.journey,
        journeyLabel: `Jornada ${round.journey}`,
        range: round.range,
        date: isoDate(day),
        time: time24(time),
        home,
        away,
        homeGoals: null,
        awayGoals: null,
        status: 'programado',
        replay: '',
        notes: ''
      });
    }
  }

  for (const p of PLAYOFFS) {
    seq += 1;
    matches.push({
      id: `md1-${seq}`,
      division: 'd1',
      stage: 'playoffs',
      journey: null,
      journeyLabel: p.journey,
      range: '',
      date: p.date,
      time: p.time,
      home: p.home,
      away: p.away,
      homeGoals: null,
      awayGoals: null,
      status: 'por-definir',
      replay: '',
      notes: 'Cuadros de playoffs por confirmar al cerrar la liga regular.'
    });
  }

  return {
    version: 1,
    updatedAt: now,
    settings: {
      leagueName: 'The Diamonds League',
      shortName: 'TDL',
      tagline: 'Liga competitiva de HaxBall X5',
      description:
        'The Diamonds League es la liga competitiva de HaxBall X5 con 2 divisiones, 12 equipos en División 1, salas públicas abiertas y calendario oficial por jornadas.',
      season: SEASON,
      seasonNumber: 3,
      modality: '5 vs 5',
      status: 'ACTIVA',
      statusNote: 'Temporada 3 en curso · Inscripciones abiertas',
      server: 'X Hosting',
      map: '5v5 Diamonds League',
      matchDuration: 'Dos tiempos de 10:00 + última jugada',
      tolerance: '15 minutos',
      pointsWin: 3,
      pointsDraw: 1,
      tiktok: 'https://www.tiktok.com/@diamondsleague89?is_from_webapp=1&sender_device=pc',
      tiktokHandle: '@diamondsleague89',
      founded: '2025'
    },
    divisions: [
      {
        id: 'd1',
        name: 'División 1',
        code: 'D1',
        season: SEASON,
        summary: 'La categoría principal: 12 equipos, 11 jornadas y playoffs por el título.',
        teams: 12,
        journeys: 11,
        playoffs: 4,
        relegation: '2 descensos directos',
        promotion: 'Sin ascensos',
        phases: [
          {
            label: 'Fase 1',
            title: 'Liga regular',
            text: 'Todos contra todos durante 11 jornadas. Victoria 3 puntos, empate 1 punto y derrota 0 puntos.',
            note: 'Clasifican a playoffs los puestos 1°, 2°, 3° y 4°.'
          },
          {
            label: 'Fase 2',
            title: 'Playoffs',
            text: 'Semifinal 1: 1° vs 4°. Semifinal 2: 2° vs 3°.',
            note: 'Semifinales a un partido. Final de ida y vuelta.'
          }
        ],
        movement: {
          title: 'Descenso',
          items: [
            { place: '11° lugar', label: 'Descenso directo', text: 'Baja a División 2 al terminar la liga regular.' },
            { place: '12° lugar', label: 'Descenso directo', text: 'Baja a División 2 al terminar la liga regular.' }
          ]
        },
        rules: [
          { title: 'Tolerancia', text: '15 minutos antes de aplicar W.O.' },
          { title: 'W.O.', text: 'Se aplica si un equipo no presenta mínimo 4 jugadores.' },
          { title: 'Respeto', text: 'Cero toxicidad durante los partidos y en los canales de la liga.' },
          { title: 'Resultado y replay', text: 'Al terminar el partido es obligatorio enviar el resultado y la repetición.' }
        ]
      },
      {
        id: 'd2',
        name: 'División 2',
        code: 'D2',
        season: SEASON,
        summary: '8 equipos, 7 jornadas, playoffs y dos ascensos a División 1.',
        teams: 8,
        journeys: 7,
        playoffs: 4,
        relegation: 'Sin descenso',
        promotion: '2 ascensos',
        phases: [
          {
            label: 'Liga',
            title: 'Liga regular',
            text: 'Todos contra todos durante 7 jornadas. Victoria 3 puntos, empate 1 punto y derrota 0 puntos.',
            note: 'Clasifican los puestos 1, 2, 3 y 4.'
          },
          {
            label: 'Fase final',
            title: 'Playoffs',
            text: '2° vs 3° y 4° vs 1°. Las semifinales son únicamente de ida.',
            note: 'La final se juega ida y vuelta.'
          }
        ],
        movement: {
          title: 'Ascensos',
          items: [
            { place: 'Primer ascenso', label: '1° lugar de la liga', text: 'Ascenso directo a División 1.' },
            { place: 'Segundo ascenso', label: 'Ganador de los Playoffs', text: 'El campeón de playoffs siempre asciende.' }
          ]
        },
        rules: [
          { title: 'Tolerancia', text: '15 minutos.' },
          { title: 'W.O.', text: 'Se aplica si un equipo no presenta mínimo 4 jugadores.' },
          { title: 'Resultados', text: 'Se debe enviar captura y replay.' }
        ]
      }
    ],
    matchConfig: [
      { label: 'Modalidad', value: '5 vs 5 · X5' },
      { label: 'Duración', value: 'Dos tiempos de 10:00 + última jugada' },
      { label: 'Mapa', value: '5v5 Diamonds League' },
      { label: 'Servidor', value: 'X Hosting' }
    ],
    teams,
    matches,
    rules: [
      {
        id: 'discord',
        title: 'Discord',
        summary: 'Normas de convivencia dentro del servidor de la liga.',
        items: [
          { title: 'Respeto ante todo', text: 'Respeta a todos los miembros, staff y admins. Cualquier falta de respeto será sancionada.' },
          { title: 'Prohibido el spam', text: 'No enviar mensajes repetitivos, links sin permiso o flood.' },
          { title: 'Cumplir indicaciones del staff', text: 'Las decisiones del staff deben respetarse en todo momento.' },
          { title: 'Cero toxicidad', text: 'Quedan prohibidos los insultos, racismo, discriminación, acoso o provocaciones.' },
          { title: 'Contenido adecuado', text: 'No se permite contenido NSFW, gore o inapropiado.' },
          { title: 'Uso correcto de canales', text: 'Habla en los canales correspondientes y evita el desorden.' },
          { title: 'Publicidad con autorización', text: 'Partners o promociones solo con autorización del staff.' }
        ]
      },
      {
        id: 'comunidad',
        title: 'Comunidad',
        summary: 'La forma en la que nos comportamos dentro y fuera del juego.',
        items: [
          { title: 'Buena conducta', text: 'Mantén un ambiente sano y competitivo.' },
          { title: 'Evitar conflictos', text: 'Los problemas personales deben resolverse por privado o con staff.' },
          { title: 'No suplantación', text: 'Está prohibido hacerse pasar por otro usuario o staff.' },
          { title: 'Nombres y perfiles adecuados', text: 'No usar nombres ofensivos o provocativos.' }
        ]
      },
      {
        id: 'division',
        title: 'División 1',
        summary: 'Formato de competición, descenso y configuración de partidos.',
        blocks: [
          {
            title: 'Formato de competición',
            subtitle: 'Liga regular y playoffs',
            text: 'Participan 12 equipos y se juega una vuelta de todos contra todos durante 11 jornadas.',
            list: [
              'Victoria: 3 puntos.',
              'Empate: 1 punto.',
              'Derrota: 0 puntos.',
              'Clasifican los puestos 1°, 2°, 3° y 4°.',
              'Semifinales: 1° vs 4° y 2° vs 3°, únicamente de ida.',
              'Final: ida y vuelta.'
            ]
          },
          {
            title: 'Sistema de descenso',
            subtitle: 'Dos descensos directos',
            list: ['11° lugar: desciende directamente a División 2.', '12° lugar: desciende directamente a División 2.']
          },
          {
            title: 'Configuración de partidos',
            subtitle: 'Formato oficial X5',
            list: [
              'Modalidad: 5v5.',
              'Duración: dos tiempos de 10:00 minutos más última jugada.',
              'Mapa: 5v5 Diamonds League.',
              'Servidor: X Hosting.'
            ]
          },
          {
            title: 'Reglas generales',
            subtitle: 'Antes y después del partido',
            list: [
              'Tolerancia de 15 minutos.',
              'W.O. si un equipo no presenta mínimo 4 jugadores.',
              'Respeto obligatorio y cero toxicidad.',
              'Es obligatorio enviar resultado y replay.'
            ]
          }
        ]
      },
      {
        id: 'sanciones',
        title: 'Sanciones',
        summary: 'Escala disciplinaria aplicada por el staff de la liga.',
        cards: [
          {
            title: 'Escala general',
            kicker: 'Comunidad',
            tone: 'info',
            list: ['Advertencia o Warn', 'Silencio o Mute', 'Expulsión o Kick', 'Baneo o Ban'],
            text: 'Las sanciones dependerán de la gravedad de la falta.'
          },
          {
            title: 'Amarilla',
            kicker: 'Tarjeta',
            tone: 'warn',
            list: ['Conductas antideportivas', 'Pausas incorrectas', 'Reclamaciones excesivas'],
            text: '2 amarillas equivalen a 1 roja.'
          },
          {
            title: 'Roja',
            kicker: 'Tarjeta',
            tone: 'danger',
            list: ['Insultos graves', 'Falta de respeto', 'Conducta antideportiva grave'],
            text: 'Sanción más posible suspensión.'
          }
        ]
      }
    ],
    pubs: [
      { id: 'room-1', label: 'Room 01', name: 'Diamonds Public', url: 'https://www.haxball.com/play?c=lnjqtRG-Z-E', status: 'ABIERTA', players: null, note: '' },
      { id: 'room-2', label: 'Room 02', name: 'Diamonds Public', url: 'https://www.haxball.com/play?c=lX3wqk3eNlo', status: 'ABIERTA', players: null, note: '' },
      { id: 'room-3', label: 'Room 03', name: 'Diamonds Public', url: 'https://www.haxball.com/play?c=1ziccjYd2JU', status: 'ABIERTA', players: null, note: '' },
      { id: 'room-4', label: 'Room 04', name: 'Diamonds Public', url: 'https://www.haxball.com/play?c=cPP-NvFDXTc', status: 'ABIERTA', players: null, note: '' },
      { id: 'room-5', label: 'Room 05', name: 'Diamonds Public', url: 'https://www.haxball.com/play?c=Fu5CTxD2F-s', status: 'ABIERTA', players: null, note: '' }
    ],
    news: [
      {
        id: 'news-1',
        title: 'Nueva página de The Diamonds League',
        category: 'Portada',
        excerpt: 'En esta página se reunirán los avisos, resultados, entrevistas y contenido de cada jornada.',
        body: 'Todo el contenido oficial de la liga vive aquí: calendario por jornadas, salas públicas, reglas, premios y comunicados. El panel de administración permite actualizar cada módulo sin tocar código.',
        date: '2026-07-27',
        author: 'Staff',
        image: '/assets/diamonds-logo.webp',
        pinned: true
      },
      {
        id: 'news-2',
        title: 'Resumen de jornada',
        category: 'Periódico',
        excerpt: 'Resultados, marcadores y resumen de cada jornada.',
        body: 'Publicamos el resumen de cada jornada con marcadores, goleadores y la mejor actuación del partido.',
        date: '2026-08-03',
        author: 'Staff',
        image: '',
        pinned: false
      },
      {
        id: 'news-3',
        title: 'Entrevistas',
        category: 'Comunidad',
        excerpt: 'Entrevistas con jugadores, capitanes, staff y personas de la comunidad.',
        body: 'Una conversación con los protagonistas de cada fecha: capitanes, jugadores y staff de The Diamonds League.',
        date: '2026-08-10',
        author: 'Staff',
        image: '',
        pinned: false
      }
    ],
    announcements: [
      {
        id: 'ann-1',
        kind: 'awards',
        season: 'Temporada 2',
        title: 'Premios de la Temporada 2',
        kicker: 'Ceremonia de premios',
        date: '2026-03-11',
        text: 'Se anuncian los ganadores de las principales categorías y los clubes campeones de cada división.',
        bullets: [
          'Balón de Oro · Mejor jugador',
          'Bota de Oro · Máximo goleador',
          'Guante de Oro · Mejor portero',
          'Campeones de División 1 y División 2'
        ],
        closing: 'Estos fueron los premios entregados al terminar la Temporada 2.',
        warning: '',
        day: '',
        month: '',
        year: ''
      },
      {
        id: 'ann-2',
        kind: 'registration',
        season: 'Temporada 3',
        title: 'Inscripciones para la Temporada 3',
        kicker: 'Inscripciones',
        date: '2026-07-27',
        day: '27',
        month: 'JULIO',
        year: '2026',
        text: 'Las inscripciones para la Temporada 3 abren el lunes 27 de julio de 2026. Los equipos y jugadores interesados podrán registrarse para participar desde la primera jornada.',
        bullets: [],
        closing: '',
        warning: 'Cupos limitados. Revisa el servidor y los anuncios para conocer el proceso de registro.'
      }
    ],
    awards: [
      { id: 'aw-01', division: 'd2', category: 'premios', season: 'Temporada 2', title: 'Balón de Oro · Gabinho', team: 'Deportivo Pereira', text: '24 goles y 12 asistencias.', image: '/assets/announcements/d2-balon-de-oro.webp' },
      { id: 'aw-02', division: 'd2', category: 'premios', season: 'Temporada 2', title: 'Guante de Oro · Sxra', team: 'Kiosko FC', text: '87 minutos y 6 segundos de clean sheet.', image: '/assets/announcements/d2-guante-de-oro.webp' },
      { id: 'aw-03', division: 'd2', category: 'premios', season: 'Temporada 2', title: 'Bota de Oro · Gabinho', team: 'Deportivo Pereira', text: '24 goles en liga.', image: '/assets/announcements/d2-bota-de-oro.webp' },
      { id: 'aw-04', division: 'd1', category: 'premios', season: 'Temporada 2', title: 'Balón de Oro · Muñoz', team: 'Lexington', text: '38 goles, 11 asistencias y 7 partidos.', image: '/assets/announcements/d1-balon-de-oro.webp' },
      { id: 'aw-05', division: 'd1', category: 'premios', season: 'Temporada 2', title: 'Guante de Oro · Oblea Gatona', team: 'Lexington', text: '68 minutos y 15 segundos de clean sheet.', image: '/assets/announcements/d1-guante-de-oro.webp' },
      { id: 'aw-06', division: 'd1', category: 'premios', season: 'Temporada 2', title: 'Bota de Oro · Muñoz', team: 'Lexington', text: '38 goles en 7 partidos.', image: '/assets/announcements/d1-bota-de-oro.webp' },
      { id: 'aw-07', division: 'd2', category: 'rankings', season: 'Temporada 2', title: 'Ranking Balón de Oro D2', team: 'División 2', text: 'Top 5 oficial de la Temporada 2.', image: '/assets/announcements/d2-ranking-balon.webp' },
      { id: 'aw-08', division: 'd2', category: 'rankings', season: 'Temporada 2', title: 'Ranking Guante de Oro D2', team: 'División 2', text: 'Top 5 oficial de porteros de la Temporada 2.', image: '/assets/announcements/d2-ranking-guante.webp' },
      { id: 'aw-09', division: 'd2', category: 'rankings', season: 'Temporada 2', title: 'Ranking Bota de Oro D2', team: 'División 2', text: 'Top 5 oficial de goleadores de la Temporada 2.', image: '/assets/announcements/d2-ranking-bota.webp' },
      { id: 'aw-10', division: 'd1', category: 'rankings', season: 'Temporada 2', title: 'Ranking Balón de Oro D1', team: 'División 1', text: 'Top 5 oficial de la Temporada 2.', image: '/assets/announcements/d1-ranking-balon.webp' },
      { id: 'aw-11', division: 'd1', category: 'rankings', season: 'Temporada 2', title: 'Ranking Guante de Oro D1', team: 'División 1', text: 'Top 5 oficial de porteros de la Temporada 2.', image: '/assets/announcements/d1-ranking-guante.webp' },
      { id: 'aw-12', division: 'd1', category: 'rankings', season: 'Temporada 2', title: 'Ranking Bota de Oro D1', team: 'División 1', text: 'Top 5 oficial de goleadores de la Temporada 2.', image: '/assets/announcements/d1-ranking-bota.webp' },
      { id: 'aw-13', division: 'd2', category: 'campeones', season: 'Temporada 2', title: 'Mejor club D2 · Deportivo Pereira', team: 'DT Inuv', text: 'Campeón de División 2.', image: '/assets/announcements/d2-mejor-club.webp' },
      { id: 'aw-14', division: 'd1', category: 'campeones', season: 'Temporada 2', title: 'Mejor club D1 · Lexington', team: 'DT Santiago', text: 'Campeón de División 1.', image: '/assets/announcements/d1-mejor-club.webp' }
    ],
    important: [
      { id: 'imp-1', title: 'Estado de la liga', description: 'Temporada 3 activa · 2 divisiones · 12 equipos en D1', kind: 'status', href: '#importante', cta: 'Ver estado' },
      { id: 'imp-2', title: 'Reglamento', description: 'Discord, comunidad, partidos y sanciones', kind: 'link', href: '#reglas', cta: 'Abrir reglas' },
      { id: 'imp-3', title: 'Anuncios y premios', description: 'Premios T2 e inscripciones T3', kind: 'link', href: '#anuncios', cta: 'Ver anuncios' },
      { id: 'imp-4', title: 'Calendario oficial', description: '11 jornadas · 66 partidos · PDF descargable', kind: 'link', href: '#fechas', cta: 'Ver fechas' },
      { id: 'imp-5', title: 'Servers partners', description: '8 servidores aliados de la liga', kind: 'external', href: 'https://discord.gg/8JTfxJy66K', cta: 'Entrar' },
      { id: 'imp-6', title: 'Afiliación RushBet', description: 'Diamonds League × RushBet desde el 11·03·2026', kind: 'external', href: 'https://discord.gg/kVAjgkeRsC', cta: 'Entrar' },
      { id: 'imp-7', title: 'TikTok oficial', description: '@diamondsleague89', kind: 'external', href: 'https://www.tiktok.com/@diamondsleague89?is_from_webapp=1&sender_device=pc', cta: 'Seguir' },
      { id: 'imp-8', title: 'Staff y administración', description: 'Owner, master y staff de la liga', kind: 'link', href: '#equipos', cta: 'Ver equipo' }
    ],
    staff: [
      {
        id: 'st-1',
        name: 'STEFY',
        username: 'st_fxx',
        role: 'Owner',
        bio: 'Owner de The Diamonds League.',
        avatar: '/assets/team/stefy-avatar.webp',
        banner: '/assets/team/stefy-banner.webp',
        tags: ['Owner', 'Dirección']
      },
      {
        id: 'st-2',
        name: 'ZSHR08',
        username: 'zshr08',
        role: 'Master',
        bio: 'Master del servidor.',
        avatar: '/assets/team/zshr08-avatar.webp',
        banner: '/assets/team/zshr08-banner.webp',
        tags: ['Master']
      },
      {
        id: 'st-3',
        name: 'ZYROX',
        username: 'zyrox_0169',
        role: 'Staff',
        bio: '',
        avatar: '/assets/team/zyrox-avatar.webp',
        banner: '/assets/team/zyrox-banner.webp',
        tags: ['Staff']
      },
      {
        id: 'st-4',
        name: 'AYALA',
        username: 'juanayala_1',
        role: 'Staff',
        bio: '',
        avatar: '/assets/team/ayala-avatar.webp',
        banner: '/assets/team/ayala-banner.webp',
        tags: ['Staff']
      },
      {
        id: 'st-5',
        name: 'SHENLONG',
        username: 'stuncito923',
        role: 'Staff',
        bio: '',
        avatar: '/assets/team/shenlong-avatar.webp',
        banner: '/assets/team/shenlong-banner.webp',
        tags: ['Staff']
      }
    ]
  };
}

export { MONTHS, SEASON, YEAR };
