import { layout } from './layout.js';
import { esc, longDate, dayLabel, shortDate, timeLabel, statusLabel, stageLabel, plural } from './helpers.js';
import { computeStandings, nextMatch } from '../standings.js';

const MODULES = [
  { id: 'competencia', label: 'Competencia', desc: 'Cómo se juega el 5v5, divisiones y clasificación' },
  { id: 'fechas', label: 'Fechas', desc: 'Calendario por jornadas y horarios' },
  { id: 'reglas', label: 'Reglas', desc: 'Reglamento, comunidad y sanciones' },
  { id: 'pubs', label: 'Pubs', desc: 'Salas públicas para jugar' },
  { id: 'noticias', label: 'Noticias', desc: 'Resultados y contenido de la liga' },
  { id: 'anuncios', label: 'Anuncios', desc: 'Premios e inscripciones' },
  { id: 'importante', label: 'Importante', desc: 'Accesos y estado de la liga' },
  { id: 'equipos', label: 'Equipos', desc: 'Administración del servidor' }
];

const statusChip = (status) => {
  const map = {
    programado: 'chip',
    'en-vivo': 'chip chip-live',
    finalizado: 'chip chip-done',
    wo: 'chip chip-warn',
    pospuesto: 'chip chip-warn',
    'por-definir': 'chip chip-muted'
  };
  return `<span class="${map[status] || 'chip chip-muted'}">${esc(statusLabel[status] || status)}</span>`;
};

function header({ settings, isAdmin }) {
  return `<header class="site-header">
  <div class="shell header-inner">
    <a class="brand" href="#inicio" aria-label="The Diamonds League, ir al inicio">
      <img src="/assets/logo-mark.png" width="44" height="44" alt="Logo de The Diamonds League" fetchpriority="high">
      <span class="brand-text">
        <strong>${esc(settings.leagueName)}</strong>
        <small>${esc(settings.tagline)}</small>
      </span>
    </a>
    <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav" aria-label="Abrir menú">
      <span></span><span></span><span></span>
    </button>
    <nav class="site-nav" id="site-nav" aria-label="Módulos de la liga">
      <ul>
        ${MODULES.map(
          (module) =>
            `<li><a href="#${module.id}" data-nav="${module.id}">${esc(module.label)}</a></li>`
        ).join('')}
      </ul>
    </nav>
    <div class="header-actions">
      ${
        isAdmin
          ? `<a class="btn btn-ghost btn-sm" href="/panel">Panel admin</a>`
          : `<a class="btn btn-outline btn-sm" href="/entrar">Iniciar sesión</a>`
      }
    </div>
  </div>
</header>`;
}

function heroMarquee() {
  const items = MODULES.map(
    (module) => `<span class="marquee-item">${esc(module.label)}</span><i class="marquee-dot" aria-hidden="true"></i>`
  ).join('');
  return `<div class="marquee" aria-hidden="true">
  <div class="marquee-track">
    <div class="marquee-group">${items}</div>
    <div class="marquee-group">${items}</div>
  </div>
</div>`;
}

function hero({ data, standings }) {
  const { settings, pubs, matches, divisions, teams } = data;
  const upcoming = nextMatch(matches, divisions);
  const d1 = standings.d1;
  const leaders = d1.slice(0, 3);
  const openRooms = pubs.filter((room) => room.status === 'ABIERTA').length;
  const d1Teams = teams.filter((t) => t.division === 'd1').length;

  const stats = [
    { label: 'Modalidad', value: settings.modality },
    { label: 'Divisiones', value: String(divisions.length).padStart(2, '0') },
    { label: 'Equipos D1', value: String(d1Teams).padStart(2, '0') },
    { label: 'Salas públicas', value: String(pubs.length).padStart(2, '0') },
    { label: 'Estado', value: settings.status, live: true }
  ];

  return `<section class="hero" id="inicio">
  <div class="hero-bg" aria-hidden="true">
    <span class="hero-aura"></span>
    <span class="hero-beam"></span>
    <span class="hero-lines"></span>
    <span class="hero-grain"></span>
  </div>
  <p class="hero-rail hero-rail-start" aria-hidden="true">División ${String(divisions.length).padStart(2, '0')}</p>
  <p class="hero-rail hero-rail-end" aria-hidden="true">${esc(settings.season)}</p>

  <div class="shell hero-inner">
    <div class="hero-core">
      <p class="eyebrow hero-eyebrow"><span class="dot"></span>${esc(settings.season)} · ${esc(settings.status)}</p>

      <div class="hero-stage">
        <span class="hero-corner hero-corner-tl" aria-hidden="true"></span>
        <span class="hero-corner hero-corner-tr" aria-hidden="true"></span>
        <span class="hero-corner hero-corner-bl" aria-hidden="true"></span>
        <span class="hero-corner hero-corner-br" aria-hidden="true"></span>
        <span class="hero-orbit hero-orbit-1" aria-hidden="true"><i></i></span>
        <span class="hero-orbit hero-orbit-2" aria-hidden="true"><i></i></span>
        <span class="hero-orbit hero-orbit-3" aria-hidden="true"><i></i></span>
        <span class="hero-spark" aria-hidden="true"></span>
        <div class="hero-emblem">
          <img src="/assets/logo-mark.png" width="164" height="164" alt="" aria-hidden="true" fetchpriority="high" decoding="async">
        </div>
      </div>

      <h1 class="hero-title"><span>The Diamonds</span><em>League</em></h1>
      <p class="hero-lead">${esc(settings.description)}</p>
      <div class="hero-actions">
        <a class="btn btn-primary" href="#competencia">Ver competencia</a>
        <a class="btn btn-outline" href="#pubs">Jugar en una sala</a>
      </div>
      <p class="hero-note">${esc(settings.statusNote)}</p>
    </div>
  </div>

  <div class="shell hero-foot">
    <ul class="stat-strip">
      ${stats
        .map(
          (stat) => `<li>
            <small>${esc(stat.label)}</small>
            <strong${stat.live ? ' class="is-live"' : ''}>${esc(stat.value)}</strong>
          </li>`
        )
        .join('')}
    </ul>
    <p class="rooms-note">${esc(plural(openRooms, 'sala pública abierta', 'salas públicas abiertas'))} de ${
      pubs.length
    } en este momento.</p>

    <div class="hero-brief">
      ${
        upcoming
          ? `<a class="brief-card next-match" href="#fechas">
              <span class="next-label">Próximo partido</span>
              <strong class="next-teams">${esc(upcoming.home)} <i>vs</i> ${esc(upcoming.away)}</strong>
              <span class="next-meta">${esc(upcoming.divisionName)} · ${esc(dayLabel(upcoming.date))} · ${esc(
                timeLabel(upcoming.time)
              )}</span>
            </a>`
          : `<div class="brief-card next-match"><span class="next-label">Calendario</span><strong class="next-teams">Sin partidos programados</strong><span class="next-meta">El staff publicará las próximas fechas</span></div>`
      }
      ${
        leaders.length
          ? `<div class="brief-card hero-leaders">
              <span class="next-label">Cabeza de tabla · D1</span>
              <ol>${leaders
                .map(
                  (row) => `<li><b>${row.position}</b><span>${esc(row.name)}</span><i>${row.points} pts</i></li>`
                )
                .join('')}</ol>
            </div>`
          : ''
      }
    </div>
  </div>

  ${heroMarquee()}
</section>`;
}

function modulesGrid() {
  return `<section class="section section-modules" aria-labelledby="modulos-title">
  <div class="shell">
    <header class="section-head">
      <p class="eyebrow">Módulos</p>
      <h2 id="modulos-title">Todo en ocho secciones</h2>
      <p>Información pública de la liga, sin ruido y actualizada por el staff desde el panel de administración.</p>
    </header>
    <ul class="module-grid">
      ${MODULES.map(
        (module, index) => `<li>
        <a href="#${module.id}">
          <span class="module-index">${String(index + 1).padStart(2, '0')}</span>
          <strong>${esc(module.label)}</strong>
          <small>${esc(module.desc)}</small>
        </a>
      </li>`
      ).join('')}
    </ul>
  </div>
</section>`;
}

function howToPlay(data) {
  const { settings, matchConfig } = data;
  const points = [
    { label: 'Victoria', value: `${settings.pointsWin} pts` },
    { label: 'Empate', value: `${settings.pointsDraw} pt` },
    { label: 'Derrota', value: '0 pts' },
    { label: 'Tolerancia', value: settings.tolerance },
    { label: 'W.O.', value: 'Mínimo 4 jugadores' }
  ];
  return `<div class="how-to-play">
    <h3>Cómo se juega</h3>
    <p>Formato oficial <strong>${esc(settings.modality)}</strong> sobre el mapa <strong>${esc(
    settings.map
  )}</strong> en el servidor <strong>${esc(settings.server)}</strong>. ${esc(
    settings.matchDuration
  )}. Cada equipo debe presentar mínimo 4 jugadores o se aplica el W.O.</p>
    <dl class="rule-points">
      ${points
        .map((point) => `<div><dt>${esc(point.label)}</dt><dd>${esc(point.value)}</dd></div>`)
        .join('')}
    </dl>
    <ul class="config-list">
      ${matchConfig
        .map((item) => `<li><small>${esc(item.label)}</small><strong>${esc(item.value)}</strong></li>`)
        .join('')}
    </ul>
  </div>`;
}

function standingsTable(division, rows) {
  if (!rows.length) {
    return `<p class="empty">Todavía no hay equipos cargados en ${esc(division.name)}.</p>`;
  }
  return `<div class="table-wrap">
    <table class="standings">
      <caption class="sr-only">Clasificación de ${esc(division.name)}</caption>
      <thead>
        <tr>
          <th scope="col">#</th>
          <th scope="col">Equipo</th>
          <th scope="col">PJ</th>
          <th scope="col">G</th>
          <th scope="col">E</th>
          <th scope="col">P</th>
          <th scope="col">GF</th>
          <th scope="col">GC</th>
          <th scope="col">DG</th>
          <th scope="col">Pts</th>
        </tr>
      </thead>
      <tbody>
        ${rows
          .map(
            (row) => `<tr${row.position <= 4 ? ' class="is-qualified"' : ''}>
            <td>${row.position}</td>
            <th scope="row">${esc(row.name)}</th>
            <td>${row.played}</td>
            <td>${row.won}</td>
            <td>${row.drawn}</td>
            <td>${row.lost}</td>
            <td>${row.goalsFor}</td>
            <td>${row.goalsAgainst}</td>
            <td>${row.goalDiff > 0 ? '+' : ''}${row.goalDiff}</td>
            <td class="is-points">${row.points}</td>
          </tr>`
          )
          .join('')}
      </tbody>
    </table>
  </div>`;
}

function competition({ data, standings }) {
  return `<section class="section" id="competencia" aria-labelledby="competencia-title">
  <div class="shell">
    <header class="section-head">
      <p class="eyebrow">01 · Competencia</p>
      <h2 id="competencia-title">Divisiones y formato <span class="accent">${esc(data.settings.season)}</span></h2>
      <p>${esc(data.settings.modality)} con dos divisiones, liga regular, playoffs, ascensos y descensos.</p>
    </header>

    ${howToPlay(data)}

    <div class="tabs" data-tabs="division">
      <div class="tablist" role="tablist" aria-label="Elegir división">
        ${data.divisions
          .map(
            (division, index) => `<button type="button" role="tab" id="tab-${esc(
              division.id
            )}" aria-controls="panel-${esc(division.id)}" aria-selected="${index === 0}" data-tab="${esc(
              division.id
            )}">${esc(division.name)} <small>${esc(division.code)}</small></button>`
          )
          .join('')}
      </div>
      ${data.divisions
        .map(
          (division, index) =>
            `<div class="panel" id="panel-${esc(division.id)}" role="tabpanel" aria-labelledby="tab-${esc(
              division.id
            )}" data-tab-panel="${esc(division.id)}"${index === 0 ? '' : ' hidden'}>
            <p class="panel-lead">${esc(division.summary)}</p>
            <ul class="kv-grid">
              <li><small>Equipos</small><strong>${division.teams}</strong></li>
              <li><small>Jornadas</small><strong>${division.journeys}</strong></li>
              <li><small>Playoffs</small><strong>${division.playoffs}</strong></li>
              <li><small>${esc(division.movement.title || 'Movimiento')}</small><strong>${esc(
    division.promotion || division.relegation || '—'
  )}</strong></li>
            </ul>
            <div class="phase-grid">
              ${division.phases
                .map(
                  (phase) => `<article class="card">
              <span class="card-kicker">${esc(phase.label)}</span>
              <h4>${esc(phase.title)}</h4>
              <p>${esc(phase.text)}</p>
              ${phase.note ? `<p class="card-note">${esc(phase.note)}</p>` : ''}
            </article>`
                )
                .join('')}
            </div>
            <div class="movement">
              <h4>${esc(division.movement.title || 'Movimiento')}</h4>
              <div class="movement-grid">
                ${division.movement.items
                  .map(
                    (item) => `<article>
                  <small>${esc(item.place)}</small>
                  <strong>${esc(item.label)}</strong>
                  <p>${esc(item.text)}</p>
                </article>`
                  )
                  .join('')}
              </div>
            </div>
            <div class="division-rules">
              <h4>Reglas de ${esc(division.name)}</h4>
              <ul>
                ${division.rules
                  .map((rule) => `<li><strong>${esc(rule.title)}</strong><p>${esc(rule.text)}</p></li>`)
                  .join('')}
              </ul>
            </div>
            <div class="standings-block">
              <div class="block-head">
                <h4>Clasificación · ${esc(division.name)}</h4>
                <p>Se actualiza con los resultados que carga el staff.</p>
              </div>
              ${standingsTable(division, standings[division.id] || [])}
            </div>
          </div>`
        )
        .join('')}
    </div>
  </div>
</section>`;
}

function journeyGroups(matches) {
  const groups = new Map();
  for (const match of matches) {
    const key = match.journey != null ? `j${match.journey}` : `p-${match.journeyLabel || 'extra'}`;
    if (!groups.has(key)) {
      groups.set(key, {
        key,
        label: match.journey != null ? `J${match.journey}` : match.journeyLabel || 'Extra',
        title: match.journey != null ? `Jornada ${match.journey}` : stageLabel[match.stage] || 'Partido',
        range: match.range || '',
        stage: match.stage || 'liga',
        matches: []
      });
    }
    groups.get(key).matches.push(match);
  }
  return [...groups.values()].sort((a, b) => {
    if (a.stage !== b.stage) return a.stage === 'liga' ? -1 : 1;
    if (a.matches[0]?.date && b.matches[0]?.date) return a.matches[0].date.localeCompare(b.matches[0].date);
    return String(a.label).localeCompare(String(b.label), 'es', { numeric: true });
  });
}

function matchRow(match) {
  const played = match.status === 'finalizado' || match.status === 'wo';
  const score = played && match.homeGoals != null ? `${match.homeGoals} - ${match.awayGoals}` : null;
  return `<li class="match">
    <div class="match-when">
      <strong>${esc(dayLabel(match.date))}</strong>
      <span>${esc(timeLabel(match.time))}</span>
    </div>
    <div class="match-teams">
      <span class="team${match.status === 'en-vivo' ? ' is-hot' : ''}">${esc(match.home)}</span>
      <span class="vs">${score ? `<b>${esc(score)}</b>` : 'vs'}</span>
      <span class="team${match.status === 'en-vivo' ? ' is-hot' : ''}">${esc(match.away)}</span>
    </div>
    <div class="match-state">${statusChip(match.status)}${
    match.replay ? `<a href="${esc(match.replay)}" target="_blank" rel="noopener noreferrer">Replay</a>` : ''
  }</div>
  </li>`;
}

function fechas({ data }) {
  const byDivision = data.divisions
    .map((division) => ({ division, groups: journeyGroups(data.matches.filter((m) => m.division === division.id)) }))
    .filter((entry) => entry.groups.length);

  return `<section class="section section-alt" id="fechas" aria-labelledby="fechas-title">
  <div class="shell">
    <header class="section-head">
      <p class="eyebrow">02 · Fechas</p>
      <h2 id="fechas-title">Calendario oficial</h2>
      <p>Jornadas, horarios y resultados de ${esc(data.settings.season)}. Cada fecha la publica el staff desde el panel.</p>
    </header>

    ${
      byDivision.length
        ? byDivision
            .map(
              ({ division, groups }, divisionIndex) => `<div class="tabs" data-tabs="journey">
      <h3 class="division-title">${esc(division.name)} <small>${esc(division.code)}</small></h3>
      <div class="chip-row" role="tablist" aria-label="Jornadas de ${esc(division.name)}">
        ${groups
          .map(
            (group, index) => `<button type="button" role="tab" aria-selected="${divisionIndex === 0 && index === 0}" data-journey-tab="${esc(
              group.key
            )}">${esc(group.label)}</button>`
          )
          .join('')}
      </div>
      ${groups
        .map(
          (group, index) => `<div class="panel" data-journey-panel="${esc(
            group.key
          )}"${divisionIndex === 0 && index === 0 ? '' : ' hidden'}>
        <div class="block-head">
          <h4>${esc(group.title)}</h4>
          <p>${esc(group.range || longDate(group.matches[0]?.date))} · ${esc(
            plural(group.matches.length, 'partido', 'partidos')
          )}</p>
        </div>
        <ul class="match-list">${group.matches.map(matchRow).join('')}</ul>
      </div>`
        )
        .join('')}
    </div>`
            )
            .join('')
        : `<p class="empty">El calendario se publica próximamente.</p>`
    }
  </div>
</section>`;
}

function reglas({ data }) {
  return `<section class="section" id="reglas" aria-labelledby="reglas-title">
  <div class="shell">
    <header class="section-head">
      <p class="eyebrow">03 · Reglas</p>
      <h2 id="reglas-title">Reglamento de la liga</h2>
      <p>Normas de Discord, comunidad, formato de competición y sanciones.</p>
    </header>

    <div class="tabs" data-tabs="rules">
      <div class="chip-row" role="tablist" aria-label="Secciones del reglamento">
        ${data.rules
          .map(
            (group, index) =>
              `<button type="button" role="tab" aria-selected="${index === 0}" data-rule-tab="${esc(
                group.id
              )}">${esc(group.title)}</button>`
          )
          .join('')}
      </div>
      ${data.rules
        .map(
          (group, index) => `<div class="panel" data-rule-panel="${esc(group.id)}"${index === 0 ? '' : ' hidden'}>
        <p class="panel-lead">${esc(group.summary)}</p>
        ${
          group.items?.length
            ? `<ol class="rule-list">${group.items
                .map(
                  (item, i) => `<li><span>${String(i + 1).padStart(2, '0')}</span><div><strong>${esc(
                    item.title
                  )}</strong><p>${esc(item.text)}</p></div></li>`
                )
                .join('')}</ol>`
            : ''
        }
        ${
          group.blocks?.length
            ? `<div class="block-grid">${group.blocks
                .map(
                  (block) => `<article class="card">
              <span class="card-kicker">${esc(block.subtitle || 'Regla')}</span>
              <h4>${esc(block.title)}</h4>
              ${block.text ? `<p>${esc(block.text)}</p>` : ''}
              ${block.list?.length ? `<ul class="ticks">${block.list.map((li) => `<li>${esc(li)}</li>`).join('')}</ul>` : ''}
            </article>`
                )
                .join('')}</div>`
            : ''
        }
        ${
          group.cards?.length
            ? `<div class="discipline-grid">${group.cards
                .map(
                  (card) => `<article class="card card-${esc(card.tone)}">
              <span class="card-kicker">${esc(card.kicker)}</span>
              <h4>${esc(card.title)}</h4>
              <ul class="ticks">${card.list.map((li) => `<li>${esc(li)}</li>`).join('')}</ul>
              ${card.text ? `<p class="card-note">${esc(card.text)}</p>` : ''}
            </article>`
                )
                .join('')}</div>`
            : ''
        }
      </div>`
        )
        .join('')}
    </div>
  </div>
</section>`;
}

function pubs({ data }) {
  return `<section class="section section-alt" id="pubs" aria-labelledby="pubs-title">
  <div class="shell">
    <header class="section-head">
      <p class="eyebrow">04 · Pubs</p>
      <h2 id="pubs-title">Diamonds Pubs</h2>
      <p>Salas públicas de HaxBall. Elige una y entra a jugar: cada enlace abre la sala en una pestaña nueva.</p>
    </header>
    <ul class="room-grid">
      ${data.pubs
        .map(
          (room) => `<li>
        <a href="${esc(room.url)}" target="_blank" rel="noopener noreferrer">
          <div class="room-top">
            <img src="/assets/logo-mark.png" width="34" height="34" alt="" aria-hidden="true" loading="lazy">
            <span>${esc(room.label)}</span>
            <span class="chip ${room.status === 'ABIERTA' ? 'chip-live' : 'chip-muted'}">${esc(room.status)}</span>
          </div>
          <strong>${esc(room.name)}</strong>
          <small>${esc(room.note || `Sala pública oficial · ${esc(room.label)}`)}</small>
          <span class="room-cta">Abrir sala <i aria-hidden="true">→</i></span>
        </a>
      </li>`
        )
        .join('')}
    </ul>
  </div>
</section>`;
}

function noticias({ data }) {
  const items = [...data.news].sort((a, b) => {
    if (a.pinned !== b.pinned) return a.pinned ? -1 : 1;
    return String(b.date).localeCompare(String(a.date));
  });
  return `<section class="section" id="noticias" aria-labelledby="noticias-title">
  <div class="shell">
    <header class="section-head">
      <p class="eyebrow">05 · Noticias</p>
      <h2 id="noticias-title">Noticias de la liga</h2>
      <p>Resultados, entrevistas, novedades y avisos del servidor.</p>
    </header>
    ${
      items.length
        ? `<ul class="news-grid">
      ${items
        .map(
          (item) => `<li class="news-card">
        <article>
          <div class="news-media">
            ${item.image ? `<img src="${esc(item.image)}" width="320" height="180" alt="${esc(item.title)}" loading="lazy">` : '<span class="news-placeholder" aria-hidden="true">TDL</span>'}
            ${item.pinned ? '<span class="news-flag">Portada</span>' : ''}
          </div>
          <div class="news-body">
            <p class="news-meta"><span>${esc(item.category || 'Noticia')}</span><time datetime="${esc(item.date)}">${esc(
            shortDate(item.date)
          )}</time></p>
            <h3>${esc(item.title)}</h3>
            <p>${esc(item.excerpt)}</p>
            ${item.body ? `<details><summary>Leer más</summary><p>${esc(item.body)}</p></details>` : ''}
            <p class="news-author">${esc(item.author || 'Staff')}</p>
          </div>
        </article>
      </li>`
        )
        .join('')}
    </ul>`
        : '<p class="empty">Todavía no hay noticias publicadas.</p>'
    }
  </div>
</section>`;
}

function anuncios({ data }) {
  const awards = data.awards || [];
  const filters = [
    { id: 'all', label: 'Todo' },
    { id: 'premios', label: 'Premios' },
    { id: 'rankings', label: 'Rankings' },
    { id: 'campeones', label: 'Campeones' },
    { id: 'd1', label: 'División 1' },
    { id: 'd2', label: 'División 2' }
  ];

  return `<section class="section section-alt" id="anuncios" aria-labelledby="anuncios-title">
  <div class="shell">
    <header class="section-head">
      <p class="eyebrow">06 · Anuncios</p>
      <h2 id="anuncios-title">Comunicados de la liga</h2>
      <p>Premios entregados, inscripciones y avisos importantes de cada temporada.</p>
    </header>

    <ul class="ann-list">
      ${data.announcements
        .map(
          (ann) => `<li class="ann">
        <article>
          <div class="ann-side">
            <span class="card-kicker">${esc(ann.season || 'Comunicado')}</span>
            <strong class="ann-day">${esc(ann.day || shortDate(ann.date).slice(0, 2))}</strong>
            <span class="ann-month">${esc(ann.month || shortDate(ann.date).slice(3))}</span>
          </div>
          <div class="ann-body">
            <p class="card-kicker">${esc(ann.kicker || 'Anuncio')}</p>
            <h3>${esc(ann.title)}</h3>
            <p>${esc(ann.text)}</p>
            ${
              ann.bullets?.length
                ? `<ul class="ticks">${ann.bullets.map((b) => `<li>${esc(b)}</li>`).join('')}</ul>`
                : ''
            }
            ${ann.warning ? `<p class="ann-warning">${esc(ann.warning)}</p>` : ''}
            ${ann.closing ? `<p class="card-note">${esc(ann.closing)}</p>` : ''}
          </div>
        </article>
      </li>`
        )
        .join('')}
    </ul>

    ${
      awards.length
        ? `<div class="awards">
      <div class="block-head">
        <h3>Galería de premios</h3>
        <p>Balones, guantes, botas, rankings y clubes campeones.</p>
      </div>
      <div class="chip-row" data-filters>
        ${filters
          .map(
            (filter, index) =>
              `<button type="button" class="chip-btn" data-filter="${esc(filter.id)}" aria-pressed="${
                index === 0
              }">${esc(filter.label)}</button>`
          )
          .join('')}
      </div>
      <ul class="award-grid">
        ${awards
          .map(
            (award) => `<li class="award" data-category="${esc(award.category)}" data-division="${esc(award.division)}">
          <button type="button" data-lightbox="${esc(award.image)}" data-caption="${esc(
              `${award.title} · ${award.team}`
            )}">
            <img src="${esc(award.image)}" width="240" height="240" alt="${esc(award.title)}" loading="lazy">
            <span>Ampliar</span>
          </button>
          <div class="award-caption">
            <small>${esc(award.season || '')} · ${esc(award.division === 'ambas' ? 'General' : award.division.toUpperCase())}</small>
            <strong>${esc(award.title)}</strong>
            <p>${esc(award.team)} · ${esc(award.text)}</p>
          </div>
        </li>`
          )
          .join('')}
      </ul>
    </div>`
        : ''
    }
  </div>
</section>`;
}

function importante({ data }) {
  return `<section class="section" id="importante" aria-labelledby="importante-title">
  <div class="shell">
    <header class="section-head">
      <p class="eyebrow">07 · Importante</p>
      <h2 id="importante-title">Accesos de la liga</h2>
      <p>Estado actual, reglamento, calendario, partners y redes en un solo lugar.</p>
    </header>

    <div class="status-panel">
      <div>
        <p class="eyebrow">Estado de la liga</p>
        <h3>${esc(data.settings.status)}</h3>
        <p>${esc(data.settings.statusNote)}</p>
      </div>
      <dl>
        <div><dt>Temporada</dt><dd>${esc(data.settings.season)}</dd></div>
        <div><dt>Modalidad</dt><dd>${esc(data.settings.modality)}</dd></div>
        <div><dt>Divisiones</dt><dd>${data.divisions.length}</dd></div>
        <div><dt>Servidor</dt><dd>${esc(data.settings.server)}</dd></div>
      </dl>
    </div>

    <ul class="link-grid">
      ${data.important
        .map(
          (item) => `<li>
        <a href="${esc(item.href || '#')}"${
    item.kind === 'external' ? ' target="_blank" rel="noopener noreferrer"' : ''
  }>
          <strong>${esc(item.title)}</strong>
          <small>${esc(item.description)}</small>
          <span>${esc(item.cta || 'Abrir')} <i aria-hidden="true">→</i></span>
        </a>
      </li>`
        )
        .join('')}
    </ul>
  </div>
</section>`;
}

function equipos({ data }) {
  return `<section class="section section-alt" id="equipos" aria-labelledby="equipos-title">
  <div class="shell">
    <header class="section-head">
      <p class="eyebrow">08 · Equipos</p>
      <h2 id="equipos-title">Administración del servidor</h2>
      <p>Owner, master y staff actuales de ${esc(data.settings.leagueName)}.</p>
    </header>
    <ul class="team-grid">
      ${data.staff
        .map(
          (member) => `<li class="member${member.role === 'Owner' ? ' is-owner' : ''}">
        <article>
          <div class="member-banner">
            ${member.banner ? `<img src="${esc(member.banner)}" width="320" height="72" alt="" aria-hidden="true" loading="lazy">` : ''}
          </div>
          <div class="member-body">
            ${
              member.avatar
                ? `<img class="member-avatar" src="${esc(member.avatar)}" width="64" height="64" alt="Foto de ${esc(
                    member.name
                  )}" loading="lazy">`
                : '<span class="member-avatar member-avatar-empty" aria-hidden="true"></span>'
            }
            <div>
              <p class="card-kicker">${esc(member.role)}</p>
              <h3>${esc(member.name)}</h3>
              <p class="member-user">@${esc(member.username || '—')}</p>
              ${member.bio ? `<p class="member-bio">${esc(member.bio)}</p>` : ''}
            </div>
          </div>
        </article>
      </li>`
        )
        .join('')}
    </ul>
  </div>
</section>`;
}

function footer({ data }) {
  return `<footer class="site-footer">
  <div class="shell footer-inner">
    <div class="footer-brand">
      <img src="/assets/logo-mark.png" width="52" height="52" alt="Logo de ${esc(data.settings.leagueName)}" loading="lazy">
      <div>
        <strong>${esc(data.settings.leagueName)}</strong>
        <small>${esc(data.settings.tagline)}</small>
      </div>
    </div>
    <nav aria-label="Módulos">
      <ul>
        ${MODULES.map((module) => `<li><a href="#${module.id}">${esc(module.label)}</a></li>`).join('')}
      </ul>
    </nav>
    <div class="footer-side">
      <p>Compite · Representa · Conquista</p>
      <a href="${esc(data.settings.tiktok)}" target="_blank" rel="noopener noreferrer" class="btn btn-outline btn-sm">TikTok oficial</a>
    </div>
  </div>
  <p class="footer-legal">© ${new Date().getFullYear()} ${esc(data.settings.leagueName)}. Sitio no oficial affiliated a HaxBall.</p>
</footer>`;
}

function lightbox() {
  return `<div class="lightbox" data-lightbox-box hidden role="dialog" aria-modal="true" aria-label="Imagen ampliada">
  <button type="button" data-lightbox-close aria-label="Cerrar">Cerrar</button>
  <figure>
    <img src="" alt="" data-lightbox-img>
    <figcaption data-lightbox-caption></figcaption>
  </figure>
</div>`;
}

function faqJsonLd(data) {
  const d1 = data.divisions[0];
  const answers = [
    {
      q: '¿En qué formato se juega The Diamonds League?',
      a: `La liga se juega en formato ${data.settings.modality} (X5) con ${data.settings.matchDuration.toLowerCase()}, en el mapa ${data.settings.map} del servidor ${data.settings.server}.`
    },
    {
      q: '¿Cuántas divisiones tiene la liga?',
      a: `La ${data.settings.season} tiene ${data.divisions.length} divisiones: ${data.divisions
        .map((division) => division.name)
        .join(' y ')}. ${d1 ? d1.summary : ''}`
    },
    {
      q: '¿Cuántos equipos y jornadas tiene la División 1?',
      a: `La División 1 cuenta con ${d1 ? d1.teams : 0} equipos y ${d1 ? d1.journeys : 0} jornadas de liga regular, seguidas de playoffs por el título.`
    },
    {
      q: '¿Cómo se aplica el W.O.?',
      a: `Existe una tolerancia de ${data.settings.tolerance} y el W.O. se aplica si un equipo no presenta mínimo 4 jugadores al comenzar el partido.`
    },
    {
      q: '¿Cómo se reparten los puntos?',
      a: `Victoria ${data.settings.pointsWin} puntos, empate ${data.settings.pointsDraw} punto y derrota 0 puntos.`
    },
    {
      q: '¿Dónde se juegan los partidos y los Entrenamientos?',
      a: `Los partidos oficiales se juegan en el calendario de la liga y los trainings en las salas públicas de HaxBall enlazadas en la sección Pubs.`
    }
  ];
  return {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: answers.map((item) => ({
      '@type': 'Question',
      name: item.q,
      acceptedAnswer: { '@type': 'Answer', text: item.a }
    }))
  };
}

export function renderHome({ data, siteUrl, isAdmin }) {
  const { settings, teams, matches } = data;
  const standings = {
    d1: computeStandings({ teams, matches, divisionId: 'd1', settings }),
    d2: computeStandings({ teams, matches, divisionId: 'd2', settings })
  };

  const title = `${settings.leagueName} — ${settings.tagline} | ${settings.season}`;
  const description = settings.description;
  const canonical = `${siteUrl}/`;

  const jsonLd = [
    {
      '@context': 'https://schema.org',
      '@graph': [
        {
          '@type': 'SportsOrganization',
          '@id': `${siteUrl}/#liga`,
          name: settings.leagueName,
          alternateName: settings.shortName,
          url: `${siteUrl}/`,
          logo: `${siteUrl}/assets/logo-mark.png`,
          description,
          sport: 'HaxBall',
          foundingDate: settings.founded,
          sameAs: [settings.tiktok]
        },
        {
          '@type': 'WebSite',
          '@id': `${siteUrl}/#web`,
          url: `${siteUrl}/`,
          name: settings.leagueName,
          inLanguage: 'es',
          publisher: { '@id': `${siteUrl}/#liga` }
        },
        {
          '@type': 'ItemList',
          name: 'Módulos de la liga',
          itemListElement: MODULES.map((module, index) => ({
            '@type': 'ListItem',
            position: index + 1,
            name: module.label,
            url: `${siteUrl}/#${module.id}`
          }))
        }
      ]
    },
    faqJsonLd(data)
  ];

  const content = [
    header({ settings, isAdmin }),
    `<div class="scroll-progress" aria-hidden="true"><span data-scroll-bar></span></div>`,
    `<main id="contenido">`,
    hero({ data, standings }),
    modulesGrid(),
    competition({ data, standings }),
    fechas({ data }),
    reglas({ data }),
    pubs({ data }),
    noticias({ data }),
    anuncios({ data }),
    importante({ data }),
    equipos({ data }),
    `</main>`,
    footer({ data }),
    lightbox(),
    `<button class="to-top" type="button" data-to-top aria-label="Volver arriba" hidden>
      <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" focusable="false">
        <path d="M12 19V5M5 12l7-7 7 7" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </button>`,
    `<noscript><style>
      .panel[hidden]{display:block!important}
      .tablist,.chip-row,.nav-toggle,.rooms-note{display:none!important}
      .match{grid-template-columns:1fr!important}
      .match-state{justify-content:flex-start}
      .news-body details[open] summary{margin-bottom:8px}
    </style></noscript>`,
    `<script src="/js/site.js" defer></script>`
  ].join('\n');

  return layout({
    title,
    description,
    canonical,
    content,
    jsonLd,
    bodyAttrs: ` data-team-count="${teams.length}" data-pub-count="${data.pubs.length}" data-staff-count="${data.staff.length}"`
  });
}
