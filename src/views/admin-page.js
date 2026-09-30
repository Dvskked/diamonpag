import { layout } from './layout.js';
import { esc } from './helpers.js';

export function renderAdmin({ siteUrl, user }) {
  const title = 'Panel de administración | The Diamonds League';

  const content = `<div class="app">
  <aside class="app-side" id="app-side">
    <a class="app-brand" href="/">
      <img src="/assets/logo-mark.png" width="40" height="40" alt="Logo de The Diamonds League">
      <span>
        <strong>The Diamonds League</strong>
        <small>Administración</small>
      </span>
    </a>

    <nav aria-label="Secciones del panel">
      <ul class="app-nav" data-app-nav>
        <li><button type="button" class="is-active" data-view="resumen">Resumen</button></li>
        <li><button type="button" data-view="matches">Partidos</button></li>
        <li><button type="button" data-view="teams">Equipos</button></li>
        <li><button type="button" data-view="divisions">Competición</button></li>
        <li><button type="button" data-view="news">Noticias</button></li>
        <li><button type="button" data-view="announcements">Anuncios</button></li>
        <li><button type="button" data-view="awards">Premios</button></li>
        <li><button type="button" data-view="pubs">Salas públicas</button></li>
        <li><button type="button" data-view="important">Importante</button></li>
        <li><button type="button" data-view="staff">Equipo</button></li>
        <li><button type="button" data-view="rules">Reglas</button></li>
        <li><button type="button" data-view="settings">Ajustes</button></li>
      </ul>
    </nav>

    <div class="app-side-foot">
      <a class="btn btn-ghost btn-sm btn-block" href="/" target="_blank" rel="noopener">Ver sitio público ↗</a>
      <button class="btn btn-outline btn-sm btn-block" type="button" data-logout>Cerrar sesión</button>
    </div>
  </aside>

  <main class="app-main" id="contenido">
    <header class="app-topbar">
      <button class="app-menu" type="button" aria-label="Abrir menú" data-app-menu><span></span><span></span><span></span></button>
      <div>
        <h1 data-view-title>Resumen</h1>
        <p data-view-sub>Todo lo que se publica en el sitio, en un solo lugar.</p>
      </div>
      <p class="app-user"><span data-user>${esc(user)}</span></p>
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
