import { layout } from './layout.js';
import { esc } from './helpers.js';

export function renderLogin({ siteUrl, error = '', next = '/panel' }) {
  const title = 'Iniciar sesión · Panel de administración | The Diamonds League';

  const content = `<main class="auth" id="contenido">
  <div class="auth-card">
    <a class="auth-brand" href="/">
      <img src="/assets/logo-mark.png" width="56" height="56" alt="Logo de The Diamonds League">
      <span>
        <strong>The Diamonds League</strong>
        <small>Panel de administración</small>
      </span>
    </a>

    <h1>Iniciar sesión</h1>
    <p class="auth-lead">Acceso exclusivo del administrador de la liga. Desde aquí gestionas equipos, fechas, reglas, salas y comunicados.</p>

    ${
      error
        ? `<p class="alert" role="alert" data-error>${esc(error)}</p>`
        : '<p class="alert" role="alert" data-error hidden></p>'
    }

    <form method="post" action="/entrar" novalidate>
      <input type="hidden" name="next" value="${esc(next)}">
      <div class="field">
        <label for="username">Usuario</label>
        <input id="username" name="username" type="text" autocomplete="username" required autocapitalize="none" spellcheck="false" placeholder="admin">
      </div>
      <div class="field">
        <label for="password">Contraseña</label>
        <div class="field-row">
          <input id="password" name="password" type="password" autocomplete="current-password" required placeholder="••••••••">
          <button type="button" class="ghost-btn" data-toggle-password>Ver</button>
        </div>
      </div>
      <button class="btn btn-primary btn-block" type="submit">Entrar al panel</button>
    </form>

    <p class="auth-foot"><a href="/">← Volver al sitio público</a></p>
  </div>
</main>
<script src="/js/site.js" defer></script>
<noscript><style>.auth form .field-row .ghost-btn{display:none}</style></noscript>`;

  return layout({
    title,
    description: 'Acceso privado al panel de administración de The Diamonds League.',
    canonical: `${siteUrl}/entrar`,
    content,
    noindex: true,
    bodyClass: 'is-auth'
  });
}

export function renderLoggedOut({ siteUrl, message, next = '/panel' }) {
  const title = 'Sesión cerrada | The Diamonds League';
  const content = `<main class="auth" id="contenido">
  <div class="auth-card">
    <a class="auth-brand" href="/">
      <img src="/assets/logo-mark.png" width="56" height="56" alt="Logo de The Diamonds League">
      <span><strong>The Diamonds League</strong><small>Panel de administración</small></span>
    </a>
    <h1>Sesión cerrada</h1>
    <p class="auth-lead">${esc(message)}</p>
    <p><a class="btn btn-primary btn-block" href="/entrar?next=${encodeURIComponent(next)}">Volver a iniciar sesión</a></p>
    <p class="auth-foot"><a href="/">← Volver al sitio público</a></p>
  </div>
</main>`;
  return layout({
    title,
    description: 'Panel de administración de The Diamonds League.',
    canonical: `${siteUrl}/entrar`,
    content,
    noindex: true,
    bodyClass: 'is-auth'
  });
}
