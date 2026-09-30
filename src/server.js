import path from 'node:path';
import express from 'express';
import { config, rootDir } from './config.js';
import { getData } from './db.js';
import {
  getSession,
  requireAdmin,
  verifyCredentials,
  createToken,
  clearCookie,
  sessionCookie,
  checkRateLimit,
  clearRateLimit
} from './auth.js';
import { adminRouter } from './routes/admin.js';
import { renderHome } from './views/home.js';
import { renderLogin, renderLoggedOut } from './views/login.js';
import { renderAdmin } from './views/admin-page.js';

const app = express();
const PUBLIC_DIR = path.join(rootDir, 'public');
const YEAR = new Date().getFullYear();

app.disable('x-powered-by');
app.set('trust proxy', 1);

app.use(express.json({ limit: '256kb' }));
app.use(express.urlencoded({ extended: false, limit: '256kb' }));

app.use((req, res, next) => {
  res.set({
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Permissions-Policy': 'geolocation=(), microphone=(), camera=(), interest-cohort=()',
    'Cross-Origin-Opener-Policy': 'same-origin'
  });
  if (req.secure || config.admin.cookieSecure) {
    res.set('Strict-Transport-Security', 'max-age=15552000; includeSubDomains');
  }
  next();
});

const staticOptions = {
  maxAge: config.env === 'production' ? '30d' : 0,
  setHeaders(res, filePath) {
    if (/\.(png|jpe?g|webp|svg|ico|woff2?)$/i.test(filePath)) {
      res.set('Cache-Control', 'public, max-age=604800, stale-while-revalidate=86400');
    }
  }
};
app.use(express.static(PUBLIC_DIR, { ...staticOptions, index: false }));

const noStore = (req, res, next) => {
  res.set('Cache-Control', 'no-store');
  next();
};

app.get('/', noStore, async (req, res, next) => {
  try {
    const data = await getData();
    res.type('html').send(
      renderHome({ data, siteUrl: config.siteUrl, isAdmin: Boolean(getSession(req)) })
    );
  } catch (error) {
    next(error);
  }
});

const safeNext = (value) =>
  typeof value === 'string' && value.startsWith('/') && !value.startsWith('//') && !value.includes('\\')
    ? value
    : '/panel';

app.get('/entrar', noStore, (req, res) => {
  if (getSession(req)) return res.redirect(303, safeNext(req.query.next));
  res
    .type('html')
    .send(renderLogin({ siteUrl: config.siteUrl, next: safeNext(req.query.next) }));
});

app.post('/entrar', noStore, (req, res) => {
  const key = req.ip || 'desconocido';
  const limit = checkRateLimit(key);
  const next = safeNext(req.body?.next);
  const respond = (status, error) =>
    res.status(status).type('html').send(renderLogin({ siteUrl: config.siteUrl, error, next }));

  if (!limit.allowed) {
    return respond(429, `Demasiados intentos. Espera ${Math.ceil(limit.retryAfter / 60)} minuto(s).`);
  }
  if (!verifyCredentials(req.body?.username, req.body?.password)) {
    return respond(401, 'Usuario o contraseña incorrectos.');
  }
  clearRateLimit(key);
  res.setHeader('Set-Cookie', sessionCookie(createToken(config.admin.user)));
  res.redirect(303, next);
});

app.post('/salir', (req, res) => {
  res.setHeader('Set-Cookie', clearCookie());
  res.redirect(303, '/entrar?salida=1');
});

app.get('/salir', (req, res) => {
  res.setHeader('Set-Cookie', clearCookie());
  res.type('html').send(
    renderLoggedOut({ siteUrl: config.siteUrl, message: 'Tu sesión de administrador se cerró correctamente.' })
  );
});

app.use('/api/admin', adminRouter);

app.get('/panel', noStore, requireAdmin, (req, res) => {
  res.type('html').send(renderAdmin({ siteUrl: config.siteUrl, user: req.admin.u }));
});

app.get('/api/salud', (req, res) => {
  res.json({ ok: true, uptime: Math.round(process.uptime()) });
});

app.get('/sitemap.xml', async (req, res, next) => {
  try {
    const data = await getData();
    const urls = ['', 'competencia', 'fechas', 'reglas', 'pubs', 'noticias', 'anuncios', 'importante', 'equipos']
      .map((anchor) => {
        const loc = anchor ? `${config.siteUrl}/#${anchor}` : `${config.siteUrl}/`;
        const priority = anchor === '' ? '1.0' : anchor === 'competencia' || anchor === 'fechas' ? '0.9' : '0.7';
        return `  <url><loc>${loc}</loc><changefreq>${anchor ? 'weekly' : 'daily'}</changefreq><priority>${priority}</priority></url>`;
      })
      .join('\n');
    res
      .type('application/xml')
      .set('Cache-Control', 'public, max-age=3600')
      .send(`<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls}\n</urlset>`);
  } catch (error) {
    next(error);
  }
});

app.get('/robots.txt', (req, res) => {
  res
    .type('text/plain')
    .set('Cache-Control', 'public, max-age=86400')
    .send(
      [
        'User-agent: *',
        'Allow: /',
        'Disallow: /panel',
        'Disallow: /entrar',
        'Disallow: /api/',
        '',
        `Sitemap: ${config.siteUrl}/sitemap.xml`,
        ''
      ].join('\n')
    );
});

app.get('/manifest.webmanifest', (req, res) => {
  res.type('application/manifest+json').send(
    JSON.stringify(
      {
        name: 'The Diamonds League',
        short_name: 'TDL',
        description: 'Liga competitiva de HaxBall X5.',
        lang: 'es',
        start_url: '/',
        display: 'standalone',
        background_color: '#050912',
        theme_color: '#050912',
        icons: [
          { src: '/assets/favicon.png', sizes: '512x512', type: 'image/png', purpose: 'any' },
          { src: '/assets/logo-mark.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' }
        ]
      },
      null,
      2
    )
  );
});

app.use((req, res) => {
  if (req.path.startsWith('/api/')) {
    return res.status(404).json({ error: 'Recurso no encontrado.' });
  }
  res.status(404).type('html').send(
    layout404({ siteUrl: config.siteUrl })
  );
});

app.use((error, req, res, next) => {
  console.error('[error]', error);
  if (res.headersSent) return next(error);
  const status = Number(error.status) || 500;
  if (req.path.startsWith('/api/')) {
    return res.status(status).json({ error: status === 500 ? 'Error interno del servidor.' : error.message });
  }
  res.status(status).type('html').send(layout404({ siteUrl: config.siteUrl, status }));
});

function layout404({ siteUrl, status = 404 }) {
  return `<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Página no encontrada · The Diamonds League</title>
<meta name="robots" content="noindex, follow">
<link rel="icon" href="/assets/favicon.png">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Sora:wght@600;800&family=Inter:wght@400;500&display=swap">
<link rel="stylesheet" href="/css/site.css">
</head>
<body class="is-error">
<main class="error-page" id="contenido">
  <img src="/assets/logo-mark.png" width="72" height="72" alt="Logo de The Diamonds League">
  <p class="eyebrow">Error ${status}</p>
  <h1>${status === 404 ? 'Esta página no existe' : 'Algo salió mal'}</h1>
  <p>Vuelve al inicio para ver la información de la liga.</p>
  <a class="btn btn-primary" href="/">Ir al inicio</a>
</main>
</body>
</html>
<!-- ${siteUrl} · ${YEAR} -->
`;
}

const server = app.listen(config.port, () => {
  console.log(`\n  The Diamonds League`);
  console.log(`  → http://localhost:${config.port}`);
  console.log(`  → panel: http://localhost:${config.port}/entrar`);
  console.log(`  → datos: ${config.dataFile}\n`);
});

for (const signal of ['SIGINT', 'SIGTERM']) {
  process.on(signal, () => {
    server.close(() => process.exit(0));
  });
}

export default app;
