<?php
/* ============================================================================
 * The Diamonds League · layout del sitio público
 * neptun / andres / Dvskked — github.com/Dvskked
 * Conserva este aviso de autoría.
 * ========================================================================== */

require_once __DIR__ . '/../config.php';
require_once __DIR__ . '/helpers.php';
require_once __DIR__ . '/auth.php';

/**
 * Las 12 entradas de la cabecera, en el orden pedido.
 * 'label'  → texto corto que se ve en la píldora del menú.
 * 'nombre' → nombre completo (title, aria-label, marquesina y mapa de módulos).
 * 'gear'   → la tuerca de configuración se dibuja justo después de este módulo.
 */
function modulos(): array
{
    return [
        ['id' => 'liga', 'label' => 'LIGA', 'nombre' => 'LIGA', 'desc' => 'Reglamento, formato, información y tablas D1 y D2'],
        ['id' => 'fechas', 'label' => 'FECHAS', 'nombre' => 'FECHAS', 'desc' => 'Calendario, jornadas, horarios y formato'],
        ['id' => 'pubs', 'label' => 'PUBS', 'nombre' => 'PUBS', 'desc' => 'Salas de HaxBall de la liga'],
        ['id' => 'museo', 'label' => 'MUSEO', 'nombre' => 'MUSEO', 'desc' => 'Premios entregados antiguos y recientes'],
        ['id' => 'noticias', 'label' => 'NOTICIAS', 'nombre' => 'NOTICIAS', 'desc' => 'Reportajes y noticias recientes'],
        ['id' => 'anuncios', 'label' => 'ANUNCIOS', 'nombre' => 'ANUNCIOS - NOVEDADES', 'desc' => 'Novedades y comunicados de la liga'],
        ['id' => 'alianzas', 'label' => 'ALIANZAS', 'nombre' => 'ALIANZAS', 'desc' => 'Afiliaciones, partners y servidores'],
        ['id' => 'redes', 'label' => 'REDES', 'nombre' => 'REDES SOCIALES', 'desc' => 'Redes de la liga y de los streamers'],
        ['id' => 'equipo', 'label' => 'EQUIPO', 'nombre' => 'EQUIPO ADMINISTRACION - ADMINISTRACION', 'desc' => 'Administración y desarrollo de la liga', 'gear' => true],
        ['id' => 'live', 'label' => 'LIVE', 'nombre' => 'LIVE FUTBOL', 'desc' => 'Fútbol en directo, tipo Kick o Twitch'],
        ['id' => 'donacion', 'label' => 'DONACIÓN', 'nombre' => 'DONACION', 'desc' => 'Información de donaciones y apoyo']
    ];
}

/** Iconos SVG de las redes sociales. */
function icono_red(string $red): string
{
    $atributos = 'viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" focusable="false"';
    $trazo = 'fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"';
    return match ($red) {
        'instagram' => '<svg ' . $atributos . ' ' . $trazo . '><rect x="3" y="3" width="18" height="18" rx="5.2"/><circle cx="12" cy="12" r="4.1"/><path d="M17.4 6.7h.01" stroke-width="2.4"/></svg>',
        'tiktok' => '<svg ' . $atributos . ' fill="currentColor"><path d="M16.5 3a5.6 5.6 0 0 0 4.5 4.5v3a8.6 8.6 0 0 1-4.5-1.3v6.4a5.9 5.9 0 1 1-5.1-5.8v3a2.9 2.9 0 1 0 2 2.8V3h3.1Z"/></svg>',
        'twitch' => '<svg ' . $atributos . ' fill="currentColor"><path d="M4.3 3 3 6.6v13.9h4.6V23h2.7l2.4-2.5h3.7L21 16V3H4.3Zm14.9 12.3-2.3 2.4h-4.3l-2.3 2.4v-2.4H6.6V4.8h12.6v10.5ZM16 8.4h1.7v5.5H16V8.4Zm-4.7 0H13v5.5h-1.7V8.4Z"/></svg>',
        'youtube' => '<svg ' . $atributos . ' fill="currentColor"><path d="M21.6 7.2a2.5 2.5 0 0 0-1.7-1.8C18.3 5 12 5 12 5s-6.3 0-7.9.4A2.5 2.5 0 0 0 2.4 7.2C2 8.8 2 12 2 12s0 3.2.4 4.8a2.5 2.5 0 0 0 1.7 1.8C5.7 19 12 19 12 19s6.3 0 7.9-.4a2.5 2.5 0 0 0 1.7-1.8C22 15.2 22 12 22 12s0-3.2-.4-4.8ZM10 15.2V8.8L15.5 12 10 15.2Z"/></svg>',
        'discord' => '<svg ' . $atributos . ' fill="currentColor"><path d="M19.3 5.4A16.6 16.6 0 0 0 15.2 4l-.3.6a15.3 15.3 0 0 1 3.7 1.2 12.6 12.6 0 0 0-10.9 0 15.3 15.3 0 0 1 3.7-1.2L11 4a16.6 16.6 0 0 0-4.1 1.4C4.3 9.3 3.5 13 3.8 16.6A16.7 16.7 0 0 0 9 19.1l.7-1.1c-.6-.2-1.2-.5-1.7-.9l.4-.3a11.9 11.9 0 0 0 10.2 0l.4.3c-.5.4-1.1.7-1.7.9l.7 1.1a16.7 16.7 0 0 0 5.2-2.5c.4-4.2-.6-7.8-3.9-11.2ZM9.8 14.6c-1 0-1.8-.9-1.8-2s.8-2 1.8-2 1.8.9 1.8 2-.8 2-1.8 2Zm6.4 0c-1 0-1.8-.9-1.8-2s.8-2 1.8-2 1.8.9 1.8 2-.8 2-1.8 2Z"/></svg>',
        'x' => '<svg ' . $atributos . ' fill="currentColor"><path d="M17.5 3h3.2l-7 8 8.2 10h-6.4l-5-6.1L4.6 21H1.4l7.5-8.6L1 3h6.6l4.5 5.6L17.5 3Zm-1.1 16.1h1.8L6.7 4.8H4.8l11.6 14.3Z"/></svg>',
        'facebook' => '<svg ' . $atributos . ' fill="currentColor"><path d="M13.5 21v-8h2.7l.4-3.1h-3.1V7.9c0-.9.3-1.5 1.6-1.5h1.6V3.6A22 22 0 0 0 14.4 3c-2.4 0-4 1.5-4 4.2v2.7H7.7V13h2.7v8h3.1Z"/></svg>',
        default => '<svg ' . $atributos . ' ' . $trazo . '><circle cx="12" cy="12" r="8"/><path d="M12 8v4M12 16h.01"/></svg>'
    };
}

/** Icono de la tuerca. */
function icono_tuerca(): string
{
    return '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">'
        . '<path d="M4 7.5h8M16.5 7.5H20M4 16.5h3.5M12 16.5h8"/><circle cx="14.2" cy="7.5" r="2.3"/><circle cx="9.7" cy="16.5" r="2.3"/></svg>';
}

/** Menú de la tuerca de configuración. */
function tuerca_configuracion(?array $usuario, bool $esAdmin): string
{
    $salida = '';
    if ($usuario) {
        $premium = $usuario['is_premium'] ? '<span class="gear-badge">Premium</span>' : '';
        $salida .= '<div class="gear-identity">'
            . '<span class="gear-avatar" aria-hidden="true">'
            . ($usuario['avatar_url']
                ? '<img src="' . e($usuario['avatar_url']) . '" width="34" height="34" alt="">'
                : e(mb_strtoupper(mb_substr($usuario['username'], 0, 1))))
            . '</span>'
            . '<span><strong>' . e($usuario['display_name'] ?: $usuario['username']) . '</strong>'
            . '<small>@' . e($usuario['username']) . ' ' . $premium . '</small></span>'
            . '</div>';
        $salida .= '<ul class="gear-menu">';
        $salida .= '<li><a href="/cuenta/perfil">Editar perfil</a></li>';
        $salida .= '<li><a href="/cuenta/password">Cambiar contraseña</a></li>';
        $salida .= '<li><a href="/cuenta/google">Continuar con Google</a></li>';
        $salida .= '<li><a href="/cuenta/datos">Mis datos y privacidad</a></li>';
        $salida .= '</ul>';
        $salida .= '<form class="gear-form" method="post" action="/cuenta/premium">'
            . csrf_campo()
            . '<button class="btn btn-ghost btn-sm btn-block" type="submit">'
            . ($usuario['is_premium'] ? 'Desactivar modo premium' : 'Activar modo premium')
            . '</button></form>';
        if ($esAdmin) {
            $salida .= '<a class="btn btn-outline btn-sm btn-block" href="/panel">Abrir modo admin</a>';
        } else {
            $salida .= '<span class="gear-disabled" title="Necesitas permisos de administrador">Abrir modo admin · sin permisos</span>';
        }
        $salida .= '<form class="gear-form" method="post" action="/salir">'
            . csrf_campo()
            . '<button class="btn btn-primary btn-sm btn-block" type="submit">Cerrar sesión</button></form>';
    } else {
        $salida .= '<ul class="gear-menu">';
        $salida .= '<li><a href="/cuenta">Iniciar sesión</a></li>';
        $salida .= '<li><a href="/registro">Crear cuenta</a></li>';
        $salida .= '</ul>';
        $salida .= '<a class="btn btn-primary btn-sm btn-block" href="/registro">Regístrate gratis</a>';
    }
    $salida .= '<ul class="gear-menu gear-menu-legal"><li><a href="/privacidad">Política de privacidad</a></li></ul>';
    return $salida;
}

/** Cabecera con las 12 entradas: 11 anclas + la tuerca, en el orden pedido. */
function cabecera(array $datos, ?array $usuario, bool $esAdmin): string
{
    $ajustes = $datos['settings'];

    $iniciales = $usuario
        ? ($usuario['avatar_url']
            ? '<img src="' . e($usuario['avatar_url']) . '" width="26" height="26" alt="">'
            : e(mb_strtoupper(mb_substr($usuario['username'], 0, 1))))
        : '';

    /* La tuerca se dibuja dentro de la lista, justo después de EQUIPO. */
    $tuerca = '<li class="site-nav-gear">'
        . '<details class="gear" id="tuerca">'
        . '<summary aria-label="Tuerca de configuración: acceso, cuenta y ajustes"'
        . ' title="TUERCA DE CONFIGURACION">'
        . icono_tuerca()
        . '<span class="gear-avatar-inline">' . $iniciales . '</span>'
        . '</summary>'
        . '<div class="gear-panel">' . tuerca_configuracion($usuario, $esAdmin) . '</div>'
        . '</details>'
        . '</li>';

    $enlaces = '';
    foreach (modulos() as $modulo) {
        $enlaces .= '<li><a href="#' . e($modulo['id']) . '" data-nav="' . e($modulo['id']) . '"'
            . ' title="' . e($modulo['nombre'] . ' · ' . $modulo['desc']) . '"'
            . ' aria-label="' . e($modulo['nombre']) . '">'
            . e($modulo['label']) . '</a></li>';
        if (!empty($modulo['gear'])) {
            $enlaces .= $tuerca;
        }
    }

    return '<header class="site-header">
  <div class="shell header-inner">
    <a class="brand" href="#inicio" aria-label="' . e($ajustes['leagueName']) . ', ir al inicio">
      <img src="/assets/logo-mark.png" width="44" height="44" alt="Logo de ' . e($ajustes['leagueName']) . '" fetchpriority="high">
      <span class="brand-text">
        <strong>' . e($ajustes['leagueName']) . '</strong>
        <small>' . e($ajustes['tagline']) . '</small>
      </span>
    </a>
    <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav" aria-label="Abrir menú">
      <span></span><span></span><span></span>
    </button>
    <nav class="site-nav" id="site-nav" aria-label="Secciones de la liga">
      <ul>' . $enlaces . '</ul>
    </nav>
    <div class="header-actions">
      <a class="btn btn-outline btn-sm" href="/cuenta">' . ($usuario ? 'Mi cuenta' : 'Acceder') . '</a>
    </div>
  </div>
</header>';
}

/** Pie de página. */
function pie(array $datos): string
{
    $ajustes = $datos['settings'];
    $enlaces = '';
    foreach (modulos() as $modulo) {
        $enlaces .= '<li><a href="#' . e($modulo['id']) . '">' . e($modulo['label']) . '</a></li>';
    }
    $tiktok = url_segura($ajustes['tiktok']);
    return '<footer class="site-footer">
  <div class="shell footer-inner">
    <div class="footer-brand">
      <img src="/assets/logo-mark.png" width="52" height="52" alt="Logo de ' . e($ajustes['leagueName']) . '" loading="lazy">
      <div>
        <strong>' . e($ajustes['leagueName']) . '</strong>
        <small>' . e($ajustes['tagline']) . '</small>
      </div>
    </div>
    <nav aria-label="Secciones">
      <ul>' . $enlaces . '</ul>
    </nav>
    <div class="footer-side">
      <p>Compite · Representa · Conquista</p>
      ' . ($tiktok !== ''
        ? '<a href="' . e($tiktok) . '" target="_blank" rel="noopener noreferrer" class="btn btn-outline btn-sm">TikTok oficial</a>'
        : '') . '
    </div>
  </div>
  <p class="footer-legal">© ' . date('Y') . ' ' . e($ajustes['leagueName'])
        . '. Sitio no oficial affiliated a HaxBall. · <a href="/privacidad">Política de privacidad y tratamiento de datos</a></p>
</footer>';
}

/** Datos estructurados para buscadores. */
function json_ld(array $datos): string
{
    $ajustes = $datos['settings'];
    $url = APP_URL;
    $preguntas = [
        ['¿Cuántos equipos y jornadas tiene la División 1?', 'La División 1 cuenta con 12 equipos y 11 jornadas de liga regular, seguidas de playoffs por el título.'],
        ['¿Dónde se juegan los partidos?', 'Los partidos oficiales se juegan en el calendario de la liga y los entrenamientos en las salas públicas de HaxBall enlazadas en la sección Pubs.'],
        ['¿Cómo se reparten los puntos?', 'Victoria 3 puntos, empate 1 punto y derrota 0 puntos.'],
        ['¿Cómo se aplica el W.O.?', 'Existe una tolerancia de 15 minutos y el W.O. se aplica si un equipo no presenta mínimo 4 jugadores al comenzar el partido.']
    ];
    $datosLd = [
        [
            '@context' => 'https://schema.org',
            '@graph' => [
                [
                    '@type' => 'Organization',
                    '@id' => $url . '/#liga',
                    'name' => $ajustes['leagueName'],
                    'url' => $url,
                    'logo' => $url . '/assets/logo-mark.png',
                    'description' => $ajustes['description'],
                    'sameAs' => array_values(array_filter([
                        url_segura($ajustes['tiktok'])
                    ]))
                ],
                [
                    '@type' => 'WebSite',
                    '@id' => $url . '/#web',
                    'url' => $url,
                    'name' => $ajustes['leagueName'],
                    'inLanguage' => 'es',
                    'publisher' => ['@id' => $url . '/#liga'],
                    'potentialAction' => [
                        '@type' => 'SearchAction',
                        'target' => $url . '/?q={search_term_string}',
                        'query-input' => 'required name=search_term_string'
                    ]
                ],
                [
                    '@type' => 'FAQPage',
                    'mainEntity' => array_map(static fn(array $p): array => [
                        '@type' => 'Question',
                        'name' => $p[0],
                        'acceptedAnswer' => ['@type' => 'Answer', 'text' => $p[1]]
                    ], $preguntas)
                ]
            ]
        ]
    ];
    return '<script type="application/ld+json">' . e_json($datosLd) . '</script>';
}

/**
 * Envuelve el contenido en la página completa.
 * $opciones: title, description, canonical, body_class, extra_head, scripts, premium
 */
function layout(array $opciones, string $contenido): string
{
    $datos = $opciones['datos'];
    $usuario = $opciones['usuario'] ?? null;
    $esAdmin = $usuario ? usuario_es_admin($usuario) : admin_logueado();
    $titulo = $opciones['title'] ?? $datos['settings']['leagueName'];
    $descripcion = $opciones['description'] ?? $datos['settings']['description'];
    $canonica = $opciones['canonical'] ?? APP_URL . '/';
    $premium = !empty($usuario['is_premium']) ? ' is-premium' : '';
    $scripts = $opciones['scripts'] ?? ['/js/site.js'];

    $html = '<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>' . e($titulo) . '</title>
  <meta name="description" content="' . e($descripcion) . '">
  <link rel="canonical" href="' . e($canonica) . '">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="' . e($datos['settings']['leagueName']) . '">
  <meta property="og:title" content="' . e($titulo) . '">
  <meta property="og:description" content="' . e($descripcion) . '">
  <meta property="og:url" content="' . e($canonica) . '">
  <meta property="og:image" content="' . e(APP_URL) . '/assets/logo-mark.png">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="theme-color" content="#050912">
  <link rel="icon" href="/assets/favicon.png" sizes="any">
  <link rel="apple-touch-icon" href="/assets/logo-mark.png">
  <link rel="preload" as="image" href="/assets/logo-mark.png" fetchpriority="high">
  <link rel="stylesheet" href="/css/site.css">
  <meta name="csrf-token" content="' . e(csrf_token()) . '">
  ' . ($opciones['extra_head'] ?? '') . '
  ' . json_ld($datos) . '
</head>
<body class="' . e(trim(($opciones['body_class'] ?? '') . $premium)) . '">
  ' . $contenido . '
';
    foreach ($scripts as $script) {
        $html .= '<script src="' . e($script) . '" defer></script>' . "\n";
    }
    return $html . "</body>\n</html>\n";
}

/** Aviso rojo reutilizable. */
function aviso_rojo(string $titulo, string $texto = '', string $clase = ''): string
{
    return '<p class="alert-red ' . e($clase) . '"><strong>' . e($titulo) . '</strong>'
        . ($texto !== '' ? '<span>' . e($texto) . '</span>' : '') . '</p>';
}
