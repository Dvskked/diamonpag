const API = '/api/admin';
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

let db = null;
let currentView = 'resumen';
let listFilter = { query: '', chips: {} };
let searchBindings = null;

const ICON = {
  edit: '<path d="M4 20h4l10-10-4-4L4 16z"/><path d="M14.5 5.5l4 4"/>',
  trash: '<path d="M4 7h16M9 7V5h6v2M6.5 7l1 13h9l1-13"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  search: '<circle cx="11" cy="11" r="6.5"/><path d="M16 16l4.5 4.5"/>',
  empty: '<path d="M5 8h14l-1.2 11.2a1.5 1.5 0 0 1-1.5 1.3H7.7a1.5 1.5 0 0 1-1.5-1.3z"/><path d="M9 8V6.5a3 3 0 0 1 6 0V8"/>'
};

const svgIcon = (path) => {
  const wrap = document.createElement('span');
  wrap.className = 'app-ico';
  wrap.innerHTML = `<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">${path}</svg>`;
  return wrap;
};

/* ---------------- Utilidades ---------------- */
async function api(path, options = {}) {
  const res = await fetch(API + path, {
    headers: { 'Content-Type': 'application/json' },
    ...options
  });
  let payload = null;
  try {
    payload = await res.json();
  } catch {
    payload = null;
  }
  if (!res.ok) {
    if (res.status === 401) {
      window.location.href = '/entrar?next=/panel';
      throw new Error('Sesión expirada');
    }
    throw new Error((payload && payload.error) || 'Error inesperado');
  }
  return payload;
}

const el = (tag, attrs = {}, children = []) => {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (key === 'class') node.className = value;
    else if (key === 'text') node.textContent = value;
    else if (key === 'html') node.innerHTML = value;
    else if (key.startsWith('on') && typeof value === 'function') node.addEventListener(key.slice(2), value);
    else if (value === true) node.setAttribute(key, '');
    else if (value !== false && value != null) node.setAttribute(key, value);
  }
  for (const child of [].concat(children)) {
    if (child == null || child === false) continue;
    node.append(child.nodeType ? child : document.createTextNode(String(child)));
  }
  return node;
};

let toastTimer;
function toast(message, kind = 'ok') {
  const box = $('[data-toast]');
  $('p', box).textContent = message;
  box.dataset.kind = kind;
  box.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    box.hidden = true;
  }, 3400);
}

const fmtDate = (value) => {
  if (!value) return '—';
  const [y, m, d] = String(value).split('-');
  return d ? `${d}/${m}/${y.slice(2)}` : value;
};

const linesToArray = (value) =>
  String(value || '')
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean);

const splitParts = (line) => line.split('|').map((part) => part.trim());

const D1 = [
  { value: 'd1', label: 'División 1' },
  { value: 'd2', label: 'División 2' }
];

const DIVISIONS = [...D1, { value: 'ambas', label: 'Ambas divisiones' }];

/* ---------------- Colecciones ---------------- */
const VIEWS = {
  matches: {
    title: 'Partidos',
    sub: 'Calendario, horarios y resultados. Alimentan la sección Fechas y la clasificación.',
    endpoint: '/matches',
    addLabel: 'Nuevo partido',
    singular: 'partido',
    titleOf: (m) => `${m.home} vs ${m.away}`,
    subtitleOf: (m) => {
      const journey = m.journeyLabel || (m.journey ? `Jornada ${m.journey}` : '');
      const score =
        m.homeGoals !== null && m.homeGoals !== undefined && m.homeGoals !== ''
          ? `${m.homeGoals} - ${m.awayGoals ?? 0}`
          : '';
      return [fmtDate(m.date), m.time || '—', journey, score, m.notes]
        .filter((part) => part !== null && part !== undefined && part !== '')
        .join(' · ');
    },
    tagOf: (m) => m.status,
    filters: [
      {
        key: 'division',
        label: 'División',
        options: [
          { value: 'all', label: 'Todas' },
          { value: 'd1', label: 'D1' },
          { value: 'd2', label: 'D2' }
        ]
      },
      {
        key: 'status',
        label: 'Estado',
        options: [
          { value: 'all', label: 'Todos' },
          { value: 'programado', label: 'Programados' },
          { value: 'en-vivo', label: 'En vivo' },
          { value: 'finalizado', label: 'Finalizados' },
          { value: 'por-definir', label: 'Por definir' }
        ]
      }
    ],
    fields: [
      { name: 'home', label: 'Equipo local', type: 'text', required: true, placeholder: 'MASCAPITOS-FC' },
      { name: 'away', label: 'Equipo visitante', type: 'text', required: true, placeholder: 'KIOSCO-FC' },
      { name: 'division', label: 'División', type: 'select', options: D1 },
      { name: 'stage', label: 'Fase', type: 'select', options: [{ value: 'liga', label: 'Liga regular' }, { value: 'playoffs', label: 'Playoffs' }] },
      { name: 'journey', label: 'Jornada', type: 'number', min: 1, placeholder: '1' },
      { name: 'journeyLabel', label: 'Etiqueta de jornada', type: 'text', placeholder: 'Jornada 1 o SF1' },
      { name: 'date', label: 'Fecha', type: 'date' },
      { name: 'time', label: 'Hora', type: 'time' },
      { name: 'homeGoals', label: 'Goles local', type: 'number', min: 0 },
      { name: 'awayGoals', label: 'Goles visitante', type: 'number', min: 0 },
      {
        name: 'status',
        label: 'Estado',
        type: 'select',
        options: [
          { value: 'programado', label: 'Programado' },
          { value: 'en-vivo', label: 'En vivo' },
          { value: 'finalizado', label: 'Finalizado' },
          { value: 'wo', label: 'W.O.' },
          { value: 'pospuesto', label: 'Pospuesto' },
          { value: 'por-definir', label: 'Por definir' }
        ]
      },
      { name: 'replay', label: 'Enlace del replay', type: 'url', placeholder: 'https://' },
      { name: 'notes', label: 'Notas', type: 'textarea' }
    ]
  },
  teams: {
    title: 'Equipos',
    sub: 'Los equipos que participan en cada división.',
    endpoint: '/teams',
    addLabel: 'Nuevo equipo',
    singular: 'equipo',
    titleOf: (t) => t.name,
    subtitleOf: (t) => (t.division === 'd1' ? 'División 1' : 'División 2') + (t.coach ? ` · ${t.coach}` : ''),
    tagOf: (t) => (t.division === 'd1' ? 'D1' : 'D2'),
    filters: [
      {
        key: 'division',
        label: 'División',
        options: [
          { value: 'all', label: 'Todas' },
          { value: 'd1', label: 'División 1' },
          { value: 'd2', label: 'División 2' }
        ]
      }
    ],
    fields: [
      { name: 'name', label: 'Nombre', type: 'text', required: true, placeholder: 'LEXINGTON' },
      { name: 'division', label: 'División', type: 'select', options: D1 },
      { name: 'coach', label: 'DT / Manager', type: 'text' },
      { name: 'note', label: 'Nota', type: 'textarea' }
    ]
  },
  news: {
    title: 'Noticias',
    sub: 'Tarjetas de la sección Noticias. La marcada como portada sale destacada.',
    endpoint: '/news',
    addLabel: 'Nueva noticia',
    singular: 'noticia',
    titleOf: (n) => n.title,
    subtitleOf: (n) => `${n.category || 'Noticia'} · ${fmtDate(n.date)}`,
    tagOf: (n) => (n.pinned ? 'Portada' : ''),
    filters: [
      {
        key: 'category',
        label: 'Categoría',
        options: [
          { value: 'all', label: 'Todas' },
          { value: 'Portada', label: 'Portada' },
          { value: 'Periódico', label: 'Periódico' },
          { value: 'Entrevistas', label: 'Entrevistas' }
        ]
      }
    ],
    fields: [
      { name: 'title', label: 'Título', type: 'text', required: true },
      { name: 'category', label: 'Categoría', type: 'text', placeholder: 'Portada, Periódico, Entrevistas' },
      { name: 'excerpt', label: 'Resumen', type: 'textarea' },
      { name: 'body', label: 'Contenido', type: 'textarea', rows: 6 },
      { name: 'date', label: 'Fecha', type: 'date' },
      { name: 'author', label: 'Autor', type: 'text' },
      { name: 'image', label: 'Imagen (ruta)', type: 'text', placeholder: '/assets/diamonds-logo.webp' },
      { name: 'pinned', label: 'Marcar como portada', type: 'checkbox' }
    ]
  },
  announcements: {
    title: 'Anuncios',
    sub: 'Comunicados de la liga: premios, inscripciones y avisos.',
    endpoint: '/announcements',
    addLabel: 'Nuevo anuncio',
    singular: 'anuncio',
    titleOf: (a) => a.title,
    subtitleOf: (a) => `${a.kicker || 'Anuncio'} · ${fmtDate(a.date)}`,
    tagOf: (a) => a.season || '',
    fields: [
      { name: 'title', label: 'Título', type: 'text', required: true },
      { name: 'kicker', label: 'Antetítulo', type: 'text', placeholder: 'Ceremonia de premios' },
      { name: 'season', label: 'Temporada', type: 'text', placeholder: 'Temporada 2' },
      {
        name: 'kind',
        label: 'Tipo',
        type: 'select',
        options: [
          { value: 'general', label: 'General' },
          { value: 'awards', label: 'Premios' },
          { value: 'registration', label: 'Inscripciones' }
        ]
      },
      { name: 'date', label: 'Fecha', type: 'date' },
      { name: 'text', label: 'Texto', type: 'textarea', rows: 5 },
      { name: 'closing', label: 'Cierre', type: 'textarea' },
      { name: 'warning', label: 'Aviso destacado', type: 'text' },
      { name: 'day', label: 'Día (badge)', type: 'text', max: 4, placeholder: '27' },
      { name: 'month', label: 'Mes (badge)', type: 'text', max: 12, placeholder: 'JULIO' },
      { name: 'year', label: 'Año (badge)', type: 'text', max: 8, placeholder: '2026' }
    ]
  },
  awards: {
    title: 'Premios',
    sub: 'Galería de premios, rankings y clubes campeones de los comunicados.',
    endpoint: '/awards',
    addLabel: 'Nuevo premio',
    singular: 'premio',
    titleOf: (a) => a.title,
    subtitleOf: (a) => `${a.team || '—'} · ${a.text || ''}`,
    tagOf: (a) => a.category,
    filters: [
      {
        key: 'category',
        label: 'Categoría',
        options: [
          { value: 'all', label: 'Todas' },
          { value: 'premios', label: 'Premios' },
          { value: 'rankings', label: 'Rankings' },
          { value: 'campeones', label: 'Campeones' }
        ]
      }
    ],
    fields: [
      { name: 'title', label: 'Título', type: 'text', required: true },
      { name: 'team', label: 'Club / Jugador', type: 'text' },
      { name: 'text', label: 'Descripción', type: 'text' },
      { name: 'season', label: 'Temporada', type: 'text' },
      { name: 'division', label: 'División', type: 'select', options: DIVISIONS },
      {
        name: 'category',
        label: 'Categoría',
        type: 'select',
        options: [
          { value: 'premios', label: 'Premios' },
          { value: 'rankings', label: 'Rankings' },
          { value: 'campeones', label: 'Campeones' }
        ]
      },
      { name: 'image', label: 'Imagen (ruta)', type: 'text', placeholder: '/assets/announcements/d1-balon-de-oro.webp' }
    ]
  },
  pubs: {
    title: 'Salas públicas',
    sub: 'Salas de HaxBall enlazadas en la sección Pubs.',
    endpoint: '/pubs',
    addLabel: 'Nueva sala',
    singular: 'sala',
    titleOf: (p) => `${p.label} · ${p.name}`,
    subtitleOf: (p) => p.url,
    tagOf: (p) => p.status,
    filters: [
      {
        key: 'status',
        label: 'Estado',
        options: [
          { value: 'all', label: 'Todas' },
          { value: 'ABIERTA', label: 'Abiertas' },
          { value: 'CERRADA', label: 'Cerradas' },
          { value: 'MANTENIMIENTO', label: 'Mantenimiento' }
        ]
      }
    ],
    fields: [
      { name: 'label', label: 'Etiqueta', type: 'text', placeholder: 'Room 06' },
      { name: 'name', label: 'Nombre', type: 'text', placeholder: 'Diamonds Public' },
      { name: 'url', label: 'Enlace de HaxBall', type: 'url', required: true, placeholder: 'https://www.haxball.com/play?c=...' },
      {
        name: 'status',
        label: 'Estado',
        type: 'select',
        options: [
          { value: 'ABIERTA', label: 'Abierta' },
          { value: 'CERRADA', label: 'Cerrada' },
          { value: 'MANTENIMIENTO', label: 'Mantenimiento' }
        ]
      },
      { name: 'players', label: 'Jugadores (opcional)', type: 'number', min: 0 },
      { name: 'note', label: 'Nota', type: 'text' }
    ]
  },
  important: {
    title: 'Importante',
    sub: 'Accesos rápidos y estado de la liga.',
    endpoint: '/important',
    addLabel: 'Nuevo acceso',
    singular: 'acceso',
    titleOf: (i) => i.title,
    subtitleOf: (i) => i.description,
    tagOf: (i) => (i.kind === 'external' ? 'Externo' : 'Interno'),
    fields: [
      { name: 'title', label: 'Título', type: 'text', required: true },
      { name: 'description', label: 'Descripción', type: 'text' },
      {
        name: 'kind',
        label: 'Tipo',
        type: 'select',
        options: [
          { value: 'link', label: 'Enlace interno (#seccion)' },
          { value: 'external', label: 'Enlace externo' },
          { value: 'status', label: 'Estado' }
        ]
      },
      { name: 'href', label: 'Destino', type: 'text', placeholder: '#pubs' },
      { name: 'cta', label: 'Texto del botón', type: 'text', placeholder: 'Abrir' }
    ]
  },
  staff: {
    title: 'Equipo',
    sub: 'Owner, master y staff que aparecen en la sección Equipos.',
    endpoint: '/staff',
    addLabel: 'Nuevo miembro',
    singular: 'miembro',
    titleOf: (s) => s.name,
    subtitleOf: (s) => `@${s.username || '—'}`,
    tagOf: (s) => s.role,
    filters: [
      {
        key: 'role',
        label: 'Rol',
        options: [
          { value: 'all', label: 'Todos' },
          { value: 'Owner', label: 'Owner' },
          { value: 'Master', label: 'Master' },
          { value: 'Staff', label: 'Staff' },
          { value: 'Moderador', label: 'Moderador' }
        ]
      }
    ],
    fields: [
      { name: 'name', label: 'Nombre', type: 'text', required: true },
      { name: 'username', label: 'Usuario', type: 'text' },
      {
        name: 'role',
        label: 'Rol',
        type: 'select',
        options: [
          { value: 'Owner', label: 'Owner' },
          { value: 'Master', label: 'Master' },
          { value: 'Staff', label: 'Staff' },
          { value: 'Moderador', label: 'Moderador' }
        ]
      },
      { name: 'bio', label: 'Descripción', type: 'textarea' },
      { name: 'avatar', label: 'Avatar (ruta)', type: 'text', placeholder: '/assets/team/stefy-avatar.webp' },
      { name: 'banner', label: 'Banner (ruta)', type: 'text', placeholder: '/assets/team/stefy-banner.webp' }
    ]
  }
};

/* ---------------- Formularios de bloques (reglas, divisiones, ajustes) ---------------- */
const BLOCK_FORMS = {
  rules: () => ({
    key: 'rules',
    title: 'Reglas',
    sub: 'Secciones del reglamento. Formato: Título | Texto (una regla por línea).',
    build: (data) =>
      data.rules.map((group) => {
        const base = [
          { name: 'title', label: 'Nombre de la sección', type: 'text' },
          { name: 'summary', label: 'Resumen', type: 'text' }
        ];
        if (group.cards && group.cards.length) {
          base.push(
            { name: 'cardsText', label: 'Tarjetas: Nombre | lista separada por comas | nota', type: 'textarea', rows: 5 },
            { name: 'cardsKicker', label: 'Antetítulo de las tarjetas', type: 'text' },
            {
              name: 'cardsTone',
              label: 'Color de las tarjetas',
              type: 'select',
              options: [
                { value: 'info', label: 'Celeste' },
                { value: 'warn', label: 'Amarillo' },
                { value: 'danger', label: 'Rojo' }
              ]
            }
          );
        } else if (group.blocks && group.blocks.length) {
          base.push({ name: 'blocksText', label: 'Bloques: Título | subtítulo | puntos separados por comas', type: 'textarea', rows: 8 });
        } else {
          base.push({ name: 'rulesText', label: 'Reglas: Título | texto', type: 'textarea', rows: 8 });
        }

        const values = { title: group.title, summary: group.summary };
        if (group.cards && group.cards.length) {
          values.cardsText = group.cards.map((c) => `${c.title} | ${c.list.join(', ')} | ${c.text}`).join('\n');
          values.cardsKicker = group.cards[0].kicker || '';
          values.cardsTone = group.cards[0].tone || 'info';
        } else if (group.blocks && group.blocks.length) {
          values.blocksText = group.blocks.map((b) => `${b.title} | ${b.subtitle} | ${b.list.join(', ')}`).join('\n');
        } else {
          values.rulesText = group.items.map((i) => `${i.title} | ${i.text}`).join('\n');
        }

        return {
          id: group.id,
          name: group.title,
          fields: base,
          values,
          read: (form) => {
            const out = { id: group.id, title: form.title, summary: form.summary, items: [], blocks: [], cards: [] };
            if (form.rulesText != null) {
              out.items = linesToArray(form.rulesText).map((line) => {
                const [title, ...rest] = splitParts(line);
                return { title, text: rest.join('|').trim() };
              });
            }
            if (form.blocksText != null) {
              out.blocks = linesToArray(form.blocksText).map((line) => {
                const [title, subtitle, points] = splitParts(line);
                return {
                  title,
                  subtitle,
                  text: '',
                  list: (points || '').split(',').map((li) => li.trim()).filter(Boolean)
                };
              });
            }
            if (form.cardsText != null) {
              out.cards = linesToArray(form.cardsText).map((line) => {
                const [title, list, ...rest] = splitParts(line);
                return {
                  title,
                  kicker: form.cardsKicker || 'Escala',
                  tone: form.cardsTone || 'info',
                  list: (list || '').split(',').map((li) => li.trim()).filter(Boolean),
                  text: rest.join('|').trim()
                };
              });
            }
            return out;
          }
        };
      }),
    save: async (resolve) => {
      await api('/rules', { method: 'PUT', body: JSON.stringify(db.rules.map((group) => resolve(group.id))) });
    }
  }),

  divisions: () => ({
    key: 'divisions',
    title: 'Competición',
    sub: 'Formato, fases, ascensos y descensos de cada división.',
    build: (data) =>
      data.divisions.map((division) => ({
        id: division.id,
        name: division.name,
        values: {
          name: division.name,
          code: division.code,
          season: division.season,
          summary: division.summary,
          teams: division.teams,
          journeys: division.journeys,
          playoffs: division.playoffs,
          promotion: division.promotion,
          relegation: division.relegation,
          movementTitle: (division.movement && division.movement.title) || '',
          phasesText: division.phases.map((p) => `${p.label} | ${p.title} | ${p.text} | ${p.note || ''}`).join('\n'),
          movementText: ((division.movement && division.movement.items) || [])
            .map((i) => `${i.place} | ${i.label} | ${i.text}`)
            .join('\n'),
          rulesText: division.rules.map((r) => `${r.title} | ${r.text}`).join('\n')
        },
        fields: [
          { name: 'name', label: 'Nombre', type: 'text' },
          { name: 'code', label: 'Código', type: 'text' },
          { name: 'season', label: 'Temporada', type: 'text' },
          { name: 'summary', label: 'Resumen', type: 'textarea' },
          { name: 'teams', label: 'Equipos', type: 'number' },
          { name: 'journeys', label: 'Jornadas', type: 'number' },
          { name: 'playoffs', label: 'Playoffs', type: 'number' },
          { name: 'promotion', label: 'Ascenso', type: 'text' },
          { name: 'relegation', label: 'Descenso', type: 'text' },
          { name: 'movementTitle', label: 'Título de movimiento', type: 'text' },
          { name: 'phasesText', label: 'Fases: Etiqueta | Título | texto | nota', type: 'textarea', rows: 6 },
          { name: 'movementText', label: 'Movimiento: Lugar | etiqueta | texto', type: 'textarea', rows: 4 },
          { name: 'rulesText', label: 'Reglas: Título | texto', type: 'textarea', rows: 5 }
        ],
        read: (form) => ({
          id: division.id,
          name: form.name,
          code: form.code,
          season: form.season,
          summary: form.summary,
          teams: Number(form.teams) || 0,
          journeys: Number(form.journeys) || 0,
          playoffs: Number(form.playoffs) || 0,
          promotion: form.promotion,
          relegation: form.relegation,
          phases: linesToArray(form.phasesText).map((line) => {
            const [label, title, text, note] = splitParts(line);
            return { label, title, text, note };
          }),
          movement: {
            title: form.movementTitle,
            items: linesToArray(form.movementText).map((line) => {
              const [place, name, text] = splitParts(line);
              return { place, label: name, text };
            })
          },
          rules: linesToArray(form.rulesText).map((line) => {
            const [title, ...rest] = splitParts(line);
            return { title, text: rest.join('|').trim() };
          })
        })
      })),
    save: async (resolve) => {
      await api('/divisions', { method: 'PUT', body: JSON.stringify(db.divisions.map((d) => resolve(d.id))) });
    }
  }),

  settings: () => ({
    key: 'settings',
    title: 'Ajustes',
    sub: 'Nombre de la liga, temporada, estado y configuración de partidos.',
    build: () => [
      {
        id: 'settings',
        name: 'Datos de la liga',
        values: { ...db.settings },
        fields: [
          { name: 'leagueName', label: 'Nombre de la liga', type: 'text' },
          { name: 'shortName', label: 'Abreviatura', type: 'text' },
          { name: 'tagline', label: 'Bajada', type: 'text' },
          { name: 'description', label: 'Descripción (SEO)', type: 'textarea', rows: 3 },
          { name: 'season', label: 'Temporada', type: 'text' },
          { name: 'modality', label: 'Modalidad', type: 'text' },
          {
            name: 'status',
            label: 'Estado',
            type: 'select',
            options: [
              { value: 'ACTIVA', label: 'Activa' },
              { value: 'EN PAUSA', label: 'En pausa' },
              { value: 'CERRADA', label: 'Cerrada' }
            ]
          },
          { name: 'statusNote', label: 'Nota de estado', type: 'text' },
          { name: 'map', label: 'Mapa', type: 'text' },
          { name: 'server', label: 'Servidor', type: 'text' },
          { name: 'matchDuration', label: 'Duración del partido', type: 'text' },
          { name: 'tolerance', label: 'Tolerancia', type: 'text' },
          { name: 'pointsWin', label: 'Puntos por victoria', type: 'number' },
          { name: 'pointsDraw', label: 'Puntos por empate', type: 'number' },
          { name: 'tiktok', label: 'TikTok', type: 'url' },
          { name: 'tiktokHandle', label: 'TikTok (usuario)', type: 'text' },
          { name: 'founded', label: 'Fundada en', type: 'text' }
        ],
        read: (form) => form
      },
      {
        id: 'matchConfig',
        name: 'Configuración de partidos',
        values: { configText: db.matchConfig.map((c) => `${c.label} | ${c.value}`).join('\n') },
        fields: [
          {
            name: 'configText',
            label: 'Campos: Etiqueta | valor (uno por línea)',
            type: 'textarea',
            rows: 6
          }
        ],
        read: (form) => form
      }
    ],
    save: async (resolve) => {
      await api('/settings', { method: 'PUT', body: JSON.stringify(resolve('settings')) });
      const config = linesToArray(resolve('matchConfig').configText).map((line) => {
        const [name, ...rest] = splitParts(line);
        return { label: name, value: rest.join('|').trim() };
      });
      await api('/match-config', { method: 'PUT', body: JSON.stringify(config) });
    }
  })
};

/* ---------------- Modal ---------------- */
const modal = $('[data-modal]');
let modalSubmit = null;

function openModal({ title, fields, values = {}, onSubmit }) {
  $('[data-modal-title]').textContent = title;
  const container = $('[data-modal-fields]');
  container.replaceChildren();
  modalSubmit = onSubmit;

  fields.forEach((field) => {
    const id = `f-${field.name}`;
    if (field.type === 'checkbox') {
      const input = el('input', { type: 'checkbox', id, name: field.name });
      input.checked = Boolean(values[field.name]);
      container.append(
        el('div', { class: 'field-check' }, [input, el('label', { for: id, text: field.label })])
      );
      return;
    }

    const wrap = el('div', { class: 'field' });
    wrap.append(el('label', { for: id, text: field.required ? `${field.label} *` : field.label }));

    const value = values[field.name] ?? '';
    if (field.type === 'select') {
      const select = el('select', { id, name: field.name });
      field.options.forEach((option) => {
        const node = el('option', { value: option.value, text: option.label });
        if (String(value) === option.value) node.selected = true;
        select.append(node);
      });
      wrap.append(select);
    } else if (field.type === 'textarea') {
      const area = el('textarea', { id, name: field.name, rows: field.rows || 3 });
      area.value = value ?? '';
      wrap.append(area);
    } else {
      const typeMap = { number: 'number', date: 'date', time: 'time', url: 'url' };
      wrap.append(
        el('input', {
          type: typeMap[field.type] || 'text',
          id,
          name: field.name,
          min: field.min,
          maxlength: field.max,
          placeholder: field.placeholder || ''
        })
      );
      wrap.querySelector('input').value = value ?? '';
    }
    container.append(wrap);
  });

  modal.hidden = false;
  document.body.classList.add('is-locked');
  $('[data-modal-close]').focus();
}

function closeModal() {
  modal.hidden = true;
  document.body.classList.remove('is-locked');
  modalSubmit = null;
}

$('[data-modal-close]').addEventListener('click', closeModal);
$('[data-modal-cancel]').addEventListener('click', closeModal);
modal.addEventListener('click', (event) => {
  if (event.target === modal) closeModal();
});
document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && !modal.hidden) closeModal();
});

$('[data-modal-form]').addEventListener('submit', async (event) => {
  event.preventDefault();
  const button = $('[data-modal-submit]');
  button.disabled = true;
  try {
    await modalSubmit(Object.fromEntries(new FormData(event.target).entries()));
    closeModal();
  } catch (error) {
    toast(error.message, 'error');
  } finally {
    button.disabled = false;
  }
});

/* ---------------- Componentes ---------------- */
function card({ title, sub, tag, search, onEdit, onDelete, extra }) {
  return el('article', { class: 'app-card', 'data-search': search || '' }, [
    el('div', { class: 'app-card-head' }, [
      el('div', {}, [el('h3', { text: title }), sub ? el('p', { text: sub }) : null]),
      tag ? el('span', { class: 'app-tag', text: tag }) : null
    ]),
    el('div', { class: 'app-card-actions' }, [
      onEdit
        ? el('button', { class: 'btn btn-outline btn-sm', type: 'button', onclick: onEdit }, [svgIcon(ICON.edit), 'Editar'])
        : null,
      onDelete
        ? el('button', { class: 'btn btn-ghost btn-sm is-danger', type: 'button', onclick: onDelete }, [
            svgIcon(ICON.trash),
            'Eliminar'
          ])
        : null
    ]),
    extra || null
  ]);
}

function standingsTable(rows) {
  if (!rows.length) return el('p', { class: 'app-empty', text: 'Sin equipos cargados.' });
  return el('div', { class: 'table-wrap' }, [
    el('table', { class: 'standings' }, [
      el('thead', {}, [
        el('tr', {}, ['#', 'Equipo', 'PJ', 'G', 'E', 'P', 'GF', 'GC', 'DG', 'Pts'].map((h) => el('th', { scope: 'col', text: h })))
      ]),
      el(
        'tbody',
        {},
        rows.map((row) =>
          el('tr', {}, [
            el('td', { text: row.position }),
            el('th', { scope: 'row', text: row.name }),
            el('td', { text: row.played }),
            el('td', { text: row.won }),
            el('td', { text: row.drawn }),
            el('td', { text: row.lost }),
            el('td', { text: row.goalsFor }),
            el('td', { text: row.goalsAgainst }),
            el('td', { text: row.goalDiff > 0 ? `+${row.goalDiff}` : row.goalDiff }),
            el('td', { class: 'is-points', text: row.points })
          ])
        )
      )
    ])
  ]);
}

async function standingsPanels() {
  try {
    const data = await api('/standings');
    return el('div', { class: 'app-cards-2' }, [
      el('article', { class: 'app-card app-card-table' }, [el('h3', { text: 'Clasificación · División 1' }), standingsTable(data.d1)]),
      el('article', { class: 'app-card app-card-table' }, [el('h3', { text: 'Clasificación · División 2' }), standingsTable(data.d2)])
    ]);
  } catch {
    return null;
  }
}

function collectionView(name) {
  const view = VIEWS[name];
  const items = db[name] || [];
  const list = el('div', { class: 'app-list' });
  const rows = [];
  let query = '';
  const chips = {};

  items.forEach((item) => {
    const node = card({
      title: view.titleOf(item),
      sub: view.subtitleOf(item),
      tag: view.tagOf ? view.tagOf(item) : '',
      search: `${view.titleOf(item)} ${view.subtitleOf(item)} ${view.tagOf ? view.tagOf(item) : ''}`.toLowerCase(),
      onEdit: () =>
        openModal({
          title: `Editar ${view.singular}`,
          fields: view.fields,
          values: item,
          onSubmit: async (form) => {
            await api(`${view.endpoint}/${item.id}`, { method: 'PUT', body: JSON.stringify(form) });
            toast('Cambios guardados');
            await refresh();
          }
        }),
      onDelete: async () => {
        if (!window.confirm(`¿Eliminar “${view.titleOf(item)}”? Esta acción no se puede deshacer.`)) return;
        try {
          await api(`${view.endpoint}/${item.id}`, { method: 'DELETE' });
          toast('Registro eliminado');
          await refresh();
        } catch (error) {
          toast(error.message, 'error');
        }
      }
    });
    rows.push({ node, item, haystack: node.dataset.search || '' });
    list.append(node);
  });

  const count = el('p', { class: 'app-count' });
  const setCount = (shown) => {
    count.textContent = shown === items.length
      ? `${items.length} ${items.length === 1 ? 'registro' : 'registros'}`
      : `${shown} de ${items.length} ${items.length === 1 ? 'registro' : 'registros'}`;
  };

  const apply = () => {
    let shown = 0;
    rows.forEach((row) => {
      const okChip = Object.entries(chips).every(([key, value]) => {
        if (value === 'all') return true;
        return String(row.item[key] ?? '') === value;
      });
      const okText = !query || row.haystack.includes(query);
      const visible = okChip && okText;
      row.node.hidden = !visible;
      if (visible) shown += 1;
    });
    setCount(shown);
    empty.hidden = shown > 0;
  };

  const empty = el('div', { class: 'app-empty-box', hidden: true }, [
    el('span', { class: 'app-empty-ico' }, [svgIcon(ICON.empty)]),
    el('p', { text: 'No hay registros que coincidan con el filtro.' }),
    el('button', {
      class: 'btn btn-outline btn-sm',
      type: 'button',
      text: 'Limpiar filtros',
      onclick: () => {
        query = '';
        Object.keys(chips).forEach((key) => {
          chips[key] = 'all';
        });
        pane.querySelectorAll('.app-chip').forEach((chip) => {
          chip.setAttribute('aria-pressed', String(chip.dataset.value === 'all'));
        });
        syncSearch();
        apply();
      }
    })
  ]);

  const filters = el('div', { class: 'app-filters' });
  (view.filters || []).forEach((group) => {
    const row = el('div', { class: 'app-filter' });
    row.append(el('span', { class: 'app-filter-label', text: group.label }));
    const buttons = el('div', { class: 'app-filter-set' });
    chips[group.key] = chips[group.key] || 'all';
    group.options.forEach((option) => {
      const button = el('button', {
        class: 'app-chip',
        type: 'button',
        text: option.label,
        'aria-pressed': String(chips[group.key] === option.value),
        'data-value': option.value,
        onclick: () => {
          chips[group.key] = option.value;
          buttons.querySelectorAll('.app-chip').forEach((b) => {
            b.setAttribute('aria-pressed', String(b.dataset.value === option.value));
          });
          apply();
        }
      });
      buttons.append(button);
    });
    row.append(buttons);
    filters.append(row);
  });

  const pane = el('div', { class: 'app-pane' }, [
    name === 'matches' ? el('div', { class: 'app-loading', 'data-standings': 'Cargando clasificación…' }) : null,
    el('div', { class: 'app-toolbar' }, [
      el('div', { class: 'app-toolbar-info' }, [count]),
      el('button', {
        class: 'btn btn-primary btn-sm',
        type: 'button',
        onclick: () =>
          openModal({
            title: view.addLabel,
            fields: view.fields,
            values: {},
            onSubmit: async (form) => {
              await api(view.endpoint, { method: 'POST', body: JSON.stringify(form) });
              toast('Registro creado');
              await refresh();
            }
          })
      }, [svgIcon(ICON.plus), view.addLabel])
    ]),
    filters,
    items.length ? list : null,
    items.length
      ? empty
      : el('p', { class: 'app-empty', text: 'Todavía no hay registros. Crea el primero con el botón de arriba.' })
  ]);

  if (name === 'matches') {
    standingsPanels().then((node) => {
      const slot = pane.querySelector('[data-standings]');
      if (node && slot) slot.replaceWith(node);
    });
  }

  searchBindings = {
    view: name,
    set(value) {
      query = String(value || '').trim().toLowerCase();
      apply();
    },
    focus() {
      const input = $('[data-app-search]');
      if (input) {
        input.focus();
        input.select();
      }
    },
    add() {
      const addButton = pane.querySelector('.app-toolbar .btn-primary');
      if (addButton) addButton.click();
    }
  };

  setCount(items.length);
  return pane;
}

function blockView(viewName) {
  const form = BLOCK_FORMS[viewName]();
  form.items = form.build(db);
  const drafts = new Map();
  const list = el('div', { class: 'app-list' });

  const publish = el('button', {
    class: 'btn btn-primary',
    type: 'button',
    text: 'Publicar cambios',
    hidden: true,
    onclick: async () => {
      publish.disabled = true;
      try {
        await form.save((id) => {
          if (drafts.has(id)) return drafts.get(id);
          const original = form.items.find((item) => item.id === id);
          return original ? original.read(original.values) : null;
        });
        toast('Publicado. El sitio público ya muestra los cambios.');
        await refresh();
      } catch (error) {
        toast(error.message, 'error');
      } finally {
        publish.disabled = false;
      }
    }
  });

  const publishWrap = el('div', { class: 'app-publish', hidden: true }, [publish]);
  const revealPublish = () => {
    publish.hidden = false;
    publishWrap.hidden = false;
  };

  form.items.forEach((item) => {
    list.append(
      card({
        title: item.name,
        sub: `${item.fields.length} campos editables`,
        onEdit: () =>
          openModal({
            title: `Editar ${item.name}`,
            fields: item.fields,
            values: item.values,
            onSubmit: async (values) => {
              drafts.set(item.id, item.read(values));
              revealPublish();
              toast('Cambios guardados. Pulsa Publicar para aplicarlos.');
            }
          })
      })
    );
  });

  const pane = el('div', { class: 'app-pane' }, [
    el('p', { class: 'app-note', text: form.sub }),
    list,
    publishWrap
  ]);

  if (viewName === 'settings') {
    const reset = el('button', {
      class: 'btn btn-ghost btn-sm is-danger',
      type: 'button',
      text: 'Restaurar datos iniciales',
      onclick: async () => {
        const answer = window.prompt(
          'Esto reemplaza TODO el contenido con los datos de fábrica y no se puede deshacer.\nEscribe RESTABLECER para confirmar:'
        );
        if (answer !== 'RESTABLECER') return;
        try {
          await api('/reset', { method: 'POST', body: JSON.stringify({ confirm: 'RESTABLECER' }) });
          toast('Datos restaurados');
          await refresh();
        } catch (error) {
          toast(error.message, 'error');
        }
      }
    });
    pane.append(
      el('div', { class: 'app-danger' }, [
        el('h3', { text: 'Zona sensible' }),
        el('p', { text: 'Restaura la liga a los datos de fábrica migrated del sitio anterior.' }),
        reset
      ])
    );
  }

  return pane;
}

function statusBars() {
  const groups = [
    { key: 'finalizado', label: 'Finalizados', tone: 'ok' },
    { key: 'programado', label: 'Programados', tone: 'info' },
    { key: 'en-vivo', label: 'En vivo', tone: 'live' },
    { key: 'por-definir', label: 'Por definir', tone: 'idle' },
    { key: 'pospuesto', label: 'Pospuestos', tone: 'warn' },
    { key: 'wo', label: 'W.O.', tone: 'warn' }
  ];
  const total = db.matches.length || 1;

  return el('div', { class: 'app-bars' },
    groups
      .map((group) => {
        const value = db.matches.filter((m) => m.status === group.key).length;
        const pct = Math.round((value / total) * 100);
        return el('div', { class: `app-bar is-${group.tone}` }, [
          el('span', { class: 'app-bar-label' }, [group.label, el('b', { text: String(value) })]),
          el('span', { class: 'app-bar-track' }, [
            el('span', { class: 'app-bar-fill', style: `width:${Math.max(pct, value ? 3 : 0)}%` })
          ])
        ]);
      })
  );
}

function quickLinks() {
  const links = [
    { label: 'Publicar un partido', view: 'matches' },
    { label: 'Escribir una noticia', view: 'news' },
    { label: 'Abrir una sala', view: 'pubs' },
    { label: 'Actualizar el estado', view: 'settings' }
  ];
  return el(
    'div',
    { class: 'app-quick' },
    links.map((link) =>
      el('button', { class: 'app-quick-link', type: 'button', onclick: () => go(link.view) }, [
        el('span', { text: link.label }),
        el('i', { text: '→' })
      ])
    )
  );
}

function overviewView() {
  const upcoming = db.matches
    .filter((m) => m.status === 'programado' && m.date)
    .sort((a, b) => `${a.date}${b.time || ''}`.localeCompare(`${b.date}${b.time || ''}`))[0];

  const stats = [
    { label: 'Equipos', value: db.teams.length, view: 'teams' },
    { label: 'Partidos', value: db.matches.length, view: 'matches' },
    { label: 'Finalizados', value: db.matches.filter((m) => m.status === 'finalizado').length, view: 'matches' },
    { label: 'Salas', value: db.pubs.length, view: 'pubs' },
    { label: 'Noticias', value: db.news.length, view: 'news' },
    { label: 'Anuncios', value: db.announcements.length, view: 'announcements' }
  ];

  return el('div', { class: 'app-pane' }, [
    el(
      'div',
      { class: 'app-stats' },
      stats.map((stat) =>
        el('button', {
          class: 'app-stat',
          type: 'button',
          onclick: () => go(stat.view),
          html: `<small>${stat.label}</small><strong>${stat.value}</strong>`
        })
      )
    ),
    el('div', { class: 'app-cards-2' }, [
      el('article', { class: 'app-card' }, [
        el('h3', { text: 'Próximo partido' }),
        el('p', { class: 'app-lead-note', text: upcoming ? `${upcoming.home} vs ${upcoming.away}` : 'No hay partidos programados' }),
        el('p', {
          class: 'app-muted',
          text: upcoming
            ? `${fmtDate(upcoming.date)} · ${upcoming.time || '—'} · ${upcoming.journeyLabel || 'Sin jornada'}`
            : 'Publica una fecha desde Partidos.'
        })
      ]),
      el('article', { class: 'app-card' }, [
        el('h3', { text: 'Estado de la liga' }),
        el('p', { class: 'app-lead-note', text: `${db.settings.status} · ${db.settings.season}` }),
        el('p', { class: 'app-muted', text: db.settings.statusNote })
      ]),
      el('article', { class: 'app-card app-card-wide' }, [
        el('h3', { text: 'Partidos por estado' }),
        statusBars()
      ]),
      el('article', { class: 'app-card app-card-wide' }, [
        el('h3', { text: 'Accesos rápidos' }),
        quickLinks()
      ])
    ])
  ]);
}

/* ---------------- Router ---------------- */
function go(view) {
  currentView = view;
  $$('[data-app-nav] button').forEach((button) =>
    button.classList.toggle('is-active', button.dataset.view === view)
  );
  const body = $('[data-view-body]');
  body.replaceChildren();
  searchBindings = null;
  syncSearch();
  setSearchEnabled(false);

  if (view === 'resumen') {
    $('[data-view-title]').textContent = 'Resumen';
    $('[data-view-sub]').textContent = 'Todo lo que se publica en el sitio, en un solo lugar.';
    body.append(overviewView());
    return;
  }

  if (BLOCK_FORMS[view]) {
    const form = BLOCK_FORMS[view]();
    $('[data-view-title]').textContent = form.title;
    $('[data-view-sub]').textContent = form.sub;
    body.append(blockView(view));
    return;
  }

  const config = VIEWS[view];
  if (!config) return;
  $('[data-view-title]').textContent = config.title;
  $('[data-view-sub]').textContent = config.sub;
  body.append(collectionView(view));
  setSearchEnabled(true);
}

async function refresh() {
  db = await api('/data');
  go(currentView);
}

/* ---------------- Buscador ---------------- */
const searchInput = $('[data-app-search]');

function setSearchEnabled(enabled) {
  if (searchInput) searchInput.disabled = !enabled;
}

function syncSearch() {
  if (searchInput && searchInput.value) searchInput.value = '';
}

if (searchInput) {
  searchInput.addEventListener('input', () => {
    if (searchBindings) searchBindings.set(searchInput.value);
  });
  searchInput.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      event.stopPropagation();
      searchInput.value = '';
      if (searchBindings) searchBindings.set('');
      searchInput.blur();
    }
  });
}

/* ---------------- Atajos de teclado ---------------- */
document.addEventListener('keydown', (event) => {
  const typing = /^(INPUT|TEXTAREA|SELECT)$/.test(event.target.tagName) || event.target.isContentEditable;
  if (event.key === '/' && !typing && searchBindings) {
    event.preventDefault();
    searchBindings.focus();
    return;
  }
  if (event.key === 'Escape' && !modal.hidden) {
    closeModal();
    return;
  }
  if (typing || event.metaKey || event.ctrlKey || event.altKey) return;
  if (event.key === 'n' || event.key === 'N') {
    if (searchBindings) {
      event.preventDefault();
      searchBindings.add();
    }
  }
});

/* ---------------- Navegación ---------------- */
const side = $('#app-side');
const menuButton = $('[data-app-menu]');

function setSide(open) {
  side.classList.toggle('is-open', open);
  document.body.classList.toggle('is-side-open', open);
  if (menuButton) menuButton.setAttribute('aria-expanded', String(open));
}

$$('[data-app-nav] button').forEach((button) => {
  button.addEventListener('click', () => {
    go(button.dataset.view);
    setSide(false);
  });
});

if (menuButton) {
  menuButton.addEventListener('click', () => setSide(!side.classList.contains('is-open')));
}

const scrim = $('[data-app-scrim]');
if (scrim) scrim.addEventListener('click', () => setSide(false));

$('[data-logout]').addEventListener('click', async () => {
  try {
    await api('/logout', { method: 'POST' });
  } finally {
    window.location.href = '/entrar?salida=1';
  }
});

refresh().catch((error) => {
  $('[data-view-body]').replaceChildren(
    el('p', { class: 'app-empty', text: error.message || 'No se pudieron cargar los datos.' })
  );
});
