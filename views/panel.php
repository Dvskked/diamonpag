<?php
/* ============================================================================
 * The Diamonds League · shell del panel de administración
 * neptun / andres / Dvskked — github.com/Dvskked
 * Conserva este aviso de autoría.
 *
 * El marcado y las clases siguen el diseño original (css/admin.css).
 * /js/admin.js espera estos data-attributes:
 *   [data-app-scrim] · #app-side · [data-app-menu] · [data-app-nav]
 *   [data-app-search] · [data-view-title] · [data-view-sub] · [data-view-body]
 *   [data-logout] · [data-refresh] · [data-toast] · [data-modal*]
 * ========================================================================== */

/** Iconos del menú lateral del panel. */
function iconos_panel(): array
{
    return [
        'resumen' => '<rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/><rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/>',
        'settings' => '<path d="M4 7.5h8M16.5 7.5H20M4 16.5h3.5M12 16.5h8"/><circle cx="14.2" cy="7.5" r="2.3"/><circle cx="9.7" cy="16.5" r="2.3"/>',
        'divisions' => '<path d="M8 4h8v5a4 4 0 0 1-8 0z"/><path d="M8 6H5.6A2.6 2.6 0 0 0 8 10.6M16 6h2.4A2.6 2.6 0 0 1 16 10.6"/><path d="M12 13v4M9.5 20h5M10.5 17h3"/>',
        'teams' => '<path d="M12 3l7 3v5.5c0 4.2-2.9 7.6-7 9.5-4.1-1.9-7-5.3-7-9.5V6z"/><path d="M9.5 12l1.8 1.8 3.4-3.6"/>',
        'matches' => '<rect x="3" y="5" width="18" height="16" rx="2.5"/><path d="M8 3v4M16 3v4M3 10h18"/>',
        'rules' => '<path d="M4 6.5h16M4 12h16M4 17.5h10"/>',
        'pubs' => '<path d="M10.5 13.5a4 4 0 0 0 5.7 0l2.3-2.3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M13.5 10.5a4 4 0 0 0-5.7 0l-2.3 2.3a4 4 0 0 0 5.7 5.7l1-1"/>',
        'news' => '<path d="M4 5h13v14H5.5A1.5 1.5 0 0 1 4 17.5z"/><path d="M17 9h3v8.5a1.5 1.5 0 0 1-1.5 1.5H17z"/><path d="M7 9h7M7 12.5h7M7 16h4"/>',
        'announcements' => '<path d="M4 10v4a1 1 0 0 0 1 1h3l7 4V5L8 9H5a1 1 0 0 0-1 1z"/><path d="M18 9.5a3.5 3.5 0 0 1 0 5"/>',
        'awards' => '<circle cx="12" cy="14.5" r="4.5"/><path d="M9 10.2L7 3.5h10l-2 6.7"/>',
        'important' => '<path d="M12 3.6l2.6 5.5 5.9.8-4.3 4.2 1.1 6-5.3-2.9-5.3 2.9 1.1-6L3.5 9.9l5.9-.8z"/>',
        'staff' => '<circle cx="12" cy="8" r="3.5"/><path d="M4.8 20a7.2 7.2 0 0 1 14.4 0"/>',
        'alliances' => '<path d="M8.5 12.5l2.8 2.8 4.7-4.7"/><circle cx="10.5" cy="10.5" r="6"/><circle cx="17" cy="15.5" r="4.5"/>',
        'social' => '<circle cx="18" cy="5.5" r="2.8"/><circle cx="6" cy="12" r="2.8"/><circle cx="18" cy="18.5" r="2.8"/><path d="M8.5 10.8l7-3.6M8.5 13.2l7 3.6"/>',
        'live' => '<rect x="2.5" y="6" width="14" height="12" rx="2.5"/><path d="M16.5 11l5-3v8l-5-3z"/>',
        'donations' => '<path d="M12 20.5s-7-4.2-7-9a4 4 0 0 1 7-2.6A4 4 0 0 1 19 11.5c0 4.8-7 9-7 9z"/>'
    ];
}

/** Grupo del menú: título, vistas y sus etiquetas. */
function grupos_panel(): array
{
    return [
        ['titulo' => 'Panel', 'vistas' => [['resumen', 'Resumen']]],
        [
            'titulo' => 'Competición',
            'vistas' => [
                ['settings', 'Ajustes'],
                ['divisions', 'Divisiones'],
                ['teams', 'Equipos'],
                ['matches', 'Partidos'],
                ['rules', 'Reglamento']
            ]
        ],
        [
            'titulo' => 'Contenido',
            'vistas' => [
                ['pubs', 'Salas públicas'],
                ['news', 'Noticias'],
                ['announcements', 'Anuncios'],
                ['awards', 'Museo de premios'],
                ['important', 'Accesos'],
                ['staff', 'Equipo']
            ]
        ],
        [
            'titulo' => 'Comunidad',
            'vistas' => [
                ['alliances', 'Alianzas'],
                ['social', 'Redes sociales'],
                ['live', 'Live fútbol'],
                ['donations', 'Donaciones']
            ]
        ]
    ];
}

/** Icono SVG del menú lateral. */
function icono_panel(string $vista): string
{
    $dibujo = iconos_panel()[$vista] ?? '<circle cx="12" cy="12" r="8"/>';
    return '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor"'
        . ' stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"'
        . ' focusable="false">' . $dibujo . '</svg>';
}

/** Menú lateral agrupado. Las vistas se completan en el panel, no aquí. */
function menu_panel(): string
{
    $salida = '';
    foreach (grupos_panel() as $grupo) {
        $botones = '';
        foreach ($grupo['vistas'] as [$vista, $etiqueta]) {
            $botones .= '<li><button type="button"' . ($vista === 'resumen' ? ' class="is-active"' : '')
                . ' data-view="' . e($vista) . '">' . icono_panel($vista)
                . '<span>' . e($etiqueta) . '</span></button></li>';
        }
        $salida .= '<div class="app-nav-group">
        <p class="app-nav-title">' . e($grupo['titulo']) . '</p>
        <ul class="app-nav" data-app-nav data-group="' . e(mb_strtolower($grupo['titulo'])) . '">'
            . $botones . '</ul>
      </div>';
    }
    return $salida;
}

/** Estado de la base de datos para el pie del panel. */
function panel_estado_bd(): string
{
    try {
        return (int) bd_valor('SELECT COUNT(*) FROM `partidos`', [], 0) . ' partidos · '
            . (int) bd_valor('SELECT COUNT(*) FROM `usuarios`', [], 0) . ' cuentas';
    } catch (Throwable $error) {
        return 'Sin conexión: ' . $error->getMessage();
    }
}

/** Estructura del panel. Los datos y el CRUD viajan por /api/admin. */
function vista_panel(): string
{
    $datos = cargar_datos();
    $usuario = usuario_actual();

    $contenido = '<a class="skip-link" href="#contenido">Saltar al contenido</a>'
        . '<div class="app">'
        . '<a class="app-scrim" data-app-scrim href="#contenido" tabindex="-1" aria-hidden="true"></a>'

        . '<aside class="app-side" id="app-side" data-sidebar>'
        . '<a class="app-brand" href="/">'
        . '<img src="/assets/logo-mark.png" width="40" height="40" alt="Logo de ' . e($datos['settings']['leagueName']) . '">'
        . '<span><strong>' . e($datos['settings']['leagueName']) . '</strong><small>Administración</small></span>'
        . '</a>'
        . '<nav class="app-nav-wrap" aria-label="Secciones del panel">' . menu_panel() . '</nav>'
        . '<div class="app-side-foot">'
        . '<p class="app-db-state">' . e(panel_estado_bd()) . '</p>'
        . ($usuario !== null ? '<p class="app-user"><span>' . e('@' . $usuario['username']) . '</span></p>' : '')
        . '<a class="btn btn-ghost btn-sm btn-block" href="/" target="_blank" rel="noopener">Ver sitio público</a>'
        . '<button class="btn btn-outline btn-sm btn-block" type="button" data-logout>Cerrar sesión</button>'
        . '</div>'
        . '</aside>'

        . '<main class="app-main" id="contenido">'
        . '<header class="app-topbar">'
        . '<button class="app-menu" type="button" aria-label="Abrir menú" aria-expanded="false" data-app-menu>'
        . '<span></span><span></span><span></span></button>'
        . '<div class="app-topbar-title">'
        . '<h1 data-view-title>Resumen</h1>'
        . '<p data-view-sub>Todo lo que se publica en el sitio, en un solo lugar.</p>'
        . '</div>'
        . '<div class="app-topbar-tools">'
        . '<label class="app-search" for="app-search">'
        . '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.7"'
        . ' stroke-linecap="round" aria-hidden="true" focusable="false"><circle cx="11" cy="11" r="6.5"/>'
        . '<path d="M16 16l4.5 4.5"/></svg>'
        . '<input id="app-search" type="search" data-app-search placeholder="Buscar" autocomplete="off"'
        . ' spellcheck="false" disabled>'
        . '<kbd aria-hidden="true">/</kbd>'
        . '</label>'
        . '<button class="btn btn-ghost btn-sm" type="button" data-refresh>Recargar</button>'
        . '</div>'
        . '</header>'
        . '<div class="app-view" data-view-body>'
        . '<p class="app-loading">Cargando datos…</p>'
        . '</div>'
        . '</main>'
        . '</div>'

        . '<div class="app-modal" data-modal hidden role="dialog" aria-modal="true" aria-labelledby="modal-title">'
        . '<div class="app-modal-card">'
        . '<header><h2 id="modal-title" data-modal-title>Nuevo registro</h2>'
        . '<button type="button" data-modal-close aria-label="Cerrar">&times;</button></header>'
        . '<form data-modal-form novalidate>'
        . '<div class="app-modal-body" data-modal-fields></div>'
        . '<footer><p class="app-modal-hint">Los cambios se guardan al confirmar · <kbd>Esc</kbd> para cerrar</p>'
        . '<button class="btn btn-ghost" type="button" data-modal-cancel>Cancelar</button>'
        . '<button class="btn btn-primary" type="submit" data-modal-submit>Guardar</button></footer>'
        . '</form>'
        . '</div>'
        . '</div>'

        . '<div class="toast" data-toast hidden role="status" aria-live="polite"><p></p></div>';

    return layout([
        'datos' => $datos,
        'usuario' => $usuario,
        'title' => 'Panel de administración | ' . APP_NOMBRE,
        'description' => 'Panel de administración de ' . APP_NOMBRE . '.',
        'canonical' => APP_URL . '/panel',
        'body_class' => 'is-admin',
        'extra_head' => '<meta name="robots" content="noindex, nofollow">'
            . '<link rel="stylesheet" href="/css/admin.css">',
        'scripts' => ['/js/admin.js']
    ], $contenido);
}
