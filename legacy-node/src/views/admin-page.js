/* ============================================================================
 * The Diamonds League · marca de agua de autoría
 * neptun / andres / Dvskked — github.com/Dvskked
 * Copyright (c) The Diamonds League. Conserva este aviso de autoría.
 * ========================================================================== */
import { layout } from './layout.js';
import { esc } from './helpers.js';

const icon = (path) =>
  `<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">${path}</svg>`;

const ICONS = {
  resumen:
    '<rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/><rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/>',
  matches: '<rect x="3" y="5" width="18" height="16" rx="2.5"/><path d="M8 3v4M16 3v4M3 10h18"/>',
  teams: '<path d="M12 3l7 3v5.5c0 4.2-2.9 7.6-7 9.5-4.1-1.9-7-5.3-7-9.5V6z"/><path d="M9.5 12l1.8 1.8 3.4-3.6"/>',
  divisions:
    '<path d="M8 4h8v5a4 4 0 0 1-8 0z"/><path d="M8 6H5.6A2.6 2.6 0 0 0 8 10.6M16 6h2.4A2.6 2.6 0 0 1 16 10.6"/><path d="M12 13v4M9.5 20h5M10.5 17h3"/>',
  news: '<path d="M4 5h13v14H5.5A1.5 1.5 0 0 1 4 17.5z"/><path d="M17 9h3v8.5a1.5 1.5 0 0 1-1.5 1.5H17z"/><path d="M7 9h7M7 12.5h7M7 16h4"/>',
  announcements:
    '<path d="M4 10v4a1 1 0 0 0 1 1h3l7 4V5L8 9H5a1 1 0 0 0-1 1z"/><path d="M18 9.5a3.5 3.5 0 0 1 0 5"/>',
  awards: '<circle cx="12" cy="14.5" r="4.5"/><path d="M9 10.2L7 3.5h10l-2 6.7"/>',
  pubs: '<path d="M10.5 13.5a4 4 0 0 0 5.7 0l2.3-2.3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M13.5 10.5a4 4 0 0 0-5.7 0l-2.3 2.3a4 4 0 0 0 5.7 5.7l1-1"/>',
  important: '<path d="M12 3.6l2.6 5.5 5.9.8-4.3 4.2 1.1 6-5.3-2.9-5.3 2.9 1.1-6L3.5 9.9l5.9-.8z"/>',
  staff: '<circle cx="12" cy="8" r="3.5"/><path d="M4.8 20a7.2 7.2 0 0 1 14.4 0"/>',
  rules: '<path d="M4 6.5h16M4 12h16M4 17.5h10"/>',
  settings:
    '<path d="M4 7.5h8M16.5 7.5H20M4 16.5h3.5M12 16.5h8"/><circle cx="14.2" cy="7.5" r="2.3"/><circle cx="9.7" cy="16.5" r="2.3"/>'
};

const GROUPS = [
  {
    title: 'Panel',
    items: [{ view: 'resumen', label: 'Resumen' }]
  },
  {
    title: 'Competición',
    items: [
      { view: 'matches', label: 'Partidos' },
      { view: 'teams', label: 'Equipos' },
      { view: 'divisions', label: 'Competición' },
      { view: 'rules', label: 'Reglas' }
    ]
  },
  {
    title: 'Contenido',
    items: [
      { view: 'news', label: 'Noticias' },
      { view: 'announcements', label: 'Anuncios' },
      { view: 'awards', label: 'Premios' },
      { view: 'pubs', label: 'Salas públicas' },
      { view: 'important', label: 'Importante' }
    ]
  },
  {
    title: 'Administración',
    items: [
      { view: 'staff', label: 'Equipo' },
      { view: 'settings', label: 'Ajustes' }
    ]
  }
];

export function renderAdmin({ siteUrl, user }) {
  const title = 'Panel de administración | The Diamonds League';

  const content = `<div class="app">
  <a class="app-scrim" data-app-scrim href="#contenido" tabindex="-1" aria-hidden="true"></a>

  <aside class="app-side" id="app-side">
    <a class="app-brand" href="/">
      <img src="/assets/logo-mark.png" width="40" height="40" alt="Logo de The Diamonds League">
      <span>
        <strong>The Diamonds League</strong>
        <small>Administración</small>
      </span>
    </a>

    <nav class="app-nav-wrap" aria-label="Secciones del panel">
      ${GROUPS.map(
        (group) => `<div class="app-nav-group">
        <p class="app-nav-title">${esc(group.title)}</p>
        <ul class="app-nav" data-app-nav>
          ${group.items
            .map(
              (item) => `<li><button type="button"${
                item.view === 'resumen' ? ' class="is-active"' : ''
              } data-view="${item.view}">${icon(ICONS[item.view])}<span>${esc(item.label)}</span></button></li>`
            )
            .join('')}
        </ul>
      </div>`
      ).join('')}
    </nav>

    <div class="app-side-foot">
      <a class="btn btn-ghost btn-sm btn-block" href="/" target="_blank" rel="noopener">Ver sitio público ↗</a>
      <button class="btn btn-outline btn-sm btn-block" type="button" data-logout>Cerrar sesión</button>
    </div>
  </aside>

  <main class="app-main" id="contenido">
    <header class="app-topbar">
      <button class="app-menu" type="button" aria-label="Abrir menú" aria-expanded="false" data-app-menu><span></span><span></span><span></span></button>
      <div class="app-topbar-title">
        <h1 data-view-title>Resumen</h1>
        <p data-view-sub>Todo lo que se publica en el sitio, en un solo lugar.</p>
      </div>
      <div class="app-topbar-tools">
        <label class="app-search" for="app-search">
          ${icon('<circle cx="11" cy="11" r="6.5"/><path d="M16 16l4.5 4.5"/>')}
          <input id="app-search" type="search" data-app-search placeholder="Buscar" autocomplete="off" spellcheck="false">
          <kbd aria-hidden="true">/</kbd>
        </label>
        <p class="app-user"><span data-user>${esc(user)}</span></p>
      </div>
    </header>

    <div class="app-view" data-view-body>
      <p class="app-loading">Cargando datos…</p>
    </div>
  </main>
</div>

<div class="app-modal" data-modal hidden role="dialog" aria-modal="true" aria-labelledby="modal-title">
  <div class="app-modal-card">
    <header>
      <h2 id="modal-title" data-modal-title>Nuevo registro</h2>
      <button type="button" data-modal-close aria-label="Cerrar">×</button>
    </header>
    <form data-modal-form novalidate>
      <div class="app-modal-body" data-modal-fields></div>
      <footer>
        <p class="app-modal-hint">Los cambios se guardan al confirmar · <kbd>Esc</kbd> para cerrar</p>
        <button class="btn btn-ghost" type="button" data-modal-cancel>Cancelar</button>
        <button class="btn btn-primary" type="submit" data-modal-submit>Guardar</button>
      </footer>
    </form>
  </div>
</div>

<div class="toast" data-toast hidden role="status" aria-live="polite"><p></p></div>
<script src="/js/admin.js" type="module"></script>`;

  return layout({
    title,
    description: 'Panel de administración de The Diamonds League.',
    canonical: `${siteUrl}/panel`,
    content,
    noindex: true,
    bodyClass: 'is-admin',
    stylesheets: ['/css/site.css', '/css/admin.css']
  });
}
