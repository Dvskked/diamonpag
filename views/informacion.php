<?php
/* ============================================================================
 * The Diamonds League · páginas auxiliares (404, 500, sitemap)
 * neptun / andres / Dvskked — github.com/Dvskked
 * ========================================================================== */

/** 404 con búsqueda en la liga. */
function vista_404(): string
{
    $datos = cargar_datos();
    $contenido = '<main class="error-page" id="contenido"><div class="shell">'
        . '<p class="eyebrow">Error 404</p>'
        . '<h1>Esa página no está en el diamante</h1>'
        . '<p>La dirección que buscas no existe o cambió de sitio. Estas son las secciones disponibles:</p>'
        . '<ul class="error-links">';
    foreach (modulos() as $modulo) {
        $contenido .= '<li><a href="#' . e($modulo['id']) . '">' . e($modulo['label']) . '</a></li>';
    }
    $contenido .= '<li><a href="/privacidad">Privacidad</a></li><li><a href="/">Volver al inicio</a></li>'
        . '</ul></div></main>';

    return layout([
        'datos' => $datos,
        'usuario' => usuario_actual(),
        'title' => 'Página no encontrada · ' . APP_NOMBRE,
        'canonical' => APP_URL . '/',
        'body_class' => 'page-error',
        'scripts' => ['/js/site.js']
    ], $contenido);
}

/** 500 sin detalles técnicos. */
function vista_error(): string
{
    $contenido = '<main class="error-page" id="contenido"><div class="shell">'
        . '<p class="eyebrow">Error 500</p>'
        . '<h1>Algo falló en el diamante</h1>'
        . '<p>El servidor no pudo responder ahora mismo. Inténtalo de nuevo en unos segundos.</p>'
        . '<p class="error-links"><a class="btn btn-primary" href="/">Volver al inicio</a></p>'
        . '</div></main>';

    return layout([
        'datos' => ['settings' => ['leagueName' => APP_NOMBRE, 'tagline' => '', 'description' => '', 'tiktok' => '']],
        'usuario' => null,
        'title' => 'Error del servidor · ' . APP_NOMBRE,
        'body_class' => 'page-error',
        'scripts' => ['/js/site.js']
    ], $contenido);
}

/** Sitemap XML con las secciones y las noticias. */
function vista_sitemap(): string
{
    $datos = cargar_datos();
    $urls = [
        ['loc' => APP_URL . '/', 'priority' => '1.0', 'freq' => 'daily'],
        ['loc' => APP_URL . '/privacidad', 'priority' => '0.2', 'freq' => 'yearly'],
        ['loc' => APP_URL . '/registro', 'priority' => '0.3', 'freq' => 'monthly'],
        ['loc' => APP_URL . '/cuenta', 'priority' => '0.3', 'freq' => 'monthly']
    ];
    foreach (modulos() as $modulo) {
        $urls[] = ['loc' => APP_URL . '/#' . $modulo['id'], 'priority' => '0.8', 'freq' => 'weekly'];
    }
    foreach ($datos['news'] as $noticia) {
        $urls[] = [
            'loc' => APP_URL . '/#noticias',
            'priority' => '0.6',
            'freq' => 'monthly',
            'lastmod' => (string) ($noticia['date'] ?? '')
        ];
    }

    $xml = '<?xml version="1.0" encoding="UTF-8"?>' . "\n"
        . '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' . "\n";
    foreach ($urls as $url) {
        $xml .= "  <url>\n    <loc>" . e($url['loc']) . "</loc>\n";
        if (!empty($url['lastmod'])) {
            $xml .= '    <lastmod>' . e(date('Y-m-d', (int) strtotime((string) $url['lastmod']))) . "</lastmod>\n";
        }
        $xml .= '    <changefreq>' . e($url['freq']) . "</changefreq>\n"
            . '    <priority>' . e($url['priority']) . "</priority>\n  </url>\n";
    }
    $xml .= '</urlset>';

    header('Content-Type: application/xml; charset=utf-8');
    return $xml;
}
