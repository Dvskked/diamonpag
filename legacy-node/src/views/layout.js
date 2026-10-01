import { esc, json } from './helpers.js';

const themeColor = '#050912';

export function layout({
  title,
  description,
  canonical,
  bodyClass = '',
  head = '',
  content,
  jsonLd = null,
  noindex = false,
  bodyAttrs = '',
  stylesheets = ['/css/site.css']
}) {
  return `<!DOCTYPE html>
<html lang="es" prefix="og: https://ogp.me/ns#">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>${esc(title)}</title>
<meta name="description" content="${esc(description)}">
<meta name="theme-color" content="${themeColor}">
<meta name="color-scheme" content="dark">
<link rel="canonical" href="${esc(canonical)}">
${noindex ? '<meta name="robots" content="noindex, nofollow">' : '<meta name="robots" content="index, follow, max-image-preview:large">'}
<meta property="og:type" content="website">
<meta property="og:site_name" content="The Diamonds League">
<meta property="og:locale" content="es_ES">
<meta property="og:title" content="${esc(title)}">
<meta property="og:description" content="${esc(description)}">
<meta property="og:url" content="${esc(canonical)}">
<meta property="og:image" content="${esc(new URL('/assets/diamonds-logo.webp', canonical).href)}">
<meta property="og:image:alt" content="Logo de The Diamonds League">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="${esc(title)}">
<meta name="twitter:description" content="${esc(description)}">
<meta name="twitter:image" content="${esc(new URL('/assets/diamonds-logo.webp', canonical).href)}">
<link rel="icon" href="/assets/favicon.png" sizes="any">
<link rel="apple-touch-icon" href="/assets/favicon.png">
<link rel="manifest" href="/manifest.webmanifest">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preload" as="image" href="/assets/logo-mark.png" fetchpriority="high">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700;800&family=Inter:wght@400;500;600;700&display=swap">
<link rel="stylesheet" href="/css/site.css">
${stylesheets
  .filter((href) => href !== '/css/site.css')
  .map((href) => `<link rel="stylesheet" href="${esc(href)}">`)
  .join('\n')}
${jsonLd ? `<script type="application/ld+json">${json(jsonLd)}</script>` : ''}
${head}
</head>
<body class="${esc(bodyClass)}"${bodyAttrs}>
<a class="skip-link" href="#contenido">Saltar al contenido</a>
${content}
</body>
</html>
`;
}
