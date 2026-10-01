<?php
/* ============================================================================
 * The Diamonds League · front controller
 * neptun / andres / Dvskked — github.com/Dvskked
 * ========================================================================== */

declare(strict_types=1);

require_once __DIR__ . '/config.php';
require_once __DIR__ . '/conexion.php';
require_once __DIR__ . '/includes/helpers.php';
require_once __DIR__ . '/includes/bd.php';
require_once __DIR__ . '/includes/auth.php';
require_once __DIR__ . '/includes/layout.php';
require_once __DIR__ . '/includes/google.php';
require_once __DIR__ . '/views/inicio.php';
require_once __DIR__ . '/views/cuenta.php';
require_once __DIR__ . '/views/acceso.php';
require_once __DIR__ . '/views/panel.php';
require_once __DIR__ . '/views/privacidad.php';
require_once __DIR__ . '/views/informacion.php';

sesion_iniciar();

/** Rutas admitidas por el front controller. */
$ruta = parse_url((string) ($_SERVER['REQUEST_URI'] ?? '/'), PHP_URL_PATH) ?: '/';
$ruta = '/' . trim(rawurldecode($ruta), '/');
if ($ruta === '//') {
    $ruta = '/';
}
$metodo = strtoupper((string) ($_SERVER['REQUEST_METHOD'] ?? 'GET'));
$esApi = str_starts_with($ruta, '/api/');

/** Envía la respuesta de API y corta la ejecución. */
function salir_json(array $datos, int $codigo = 200): never
{
    responder_json($datos, $codigo);
}

/* --- Ficheros estáticos servidos por el servidor --- */
if (PHP_SAPI === 'cli-server') {
    $archivo = __DIR__ . $ruta;
    if ($ruta !== '/' && is_file($archivo) && !str_ends_with($archivo, '.php')) {
        return false;
    }
}

try {
    switch (true) {
        /* ------------------------------------------------------------------
         * API
         * --------------------------------------------------------------- */
        case $esApi:
            require __DIR__ . '/api/router.php';
            salir_json(['ok' => false, 'error' => 'Ruta de API desconocida.'], 404);

        /* ------------------------------------------------------------------
         * Páginas públicas
         * --------------------------------------------------------------- */
        case $ruta === '/':
        case $ruta === '/index.php':
            $datos = cargar_datos();
            $tablas = clasificaciones($datos);
            $proximo = proximo_partido($datos['matches'], $datos['divisions']);
            echo vista_inicio($datos, $tablas, usuario_actual(), $proximo);
            break;

        case $ruta === '/privacidad':
        case $ruta === '/politicas':
            echo vista_privacidad();
            break;

        case $ruta === '/entrar':
            echo vista_entrar($metodo);
            break;

        case $ruta === '/registro':
            echo vista_registro($metodo);
            break;

        case $ruta === '/cuenta':
            echo vista_cuenta_entrar($metodo);
            break;

        case $ruta === '/cuenta/perfil':
            echo vista_perfil($metodo);
            break;

        case $ruta === '/cuenta/password':
            echo vista_password($metodo);
            break;

        case $ruta === '/cuenta/premium':
            usuario_exigir();
            csrf_exigir();
            usuario_premium_actualizar(usuario_actual(), !usuario_actual()['is_premium']);
            redirigir('/cuenta/perfil?aviso=premium');
            break;

        case $ruta === '/cuenta/datos':
            echo vista_datos();
            break;

        case $ruta === '/cuenta/eliminar':
            usuario_exigir();
            csrf_exigir();
            echo vista_eliminar($metodo);
            break;

        case $ruta === '/cuenta/google':
            google_iniciar($metodo);
            break;

        case $ruta === '/cuenta/google/callback':
            google_callback();
            break;

        case $ruta === '/salir':
            usuario_exigir();
            csrf_exigir();
            usuario_cerrar();
            redirigir('/');
            break;

        /* Salir del panel: cierra la sesión de administración, no la de usuario. */
        case $ruta === '/panel/salir':
            admin_exigir();
            csrf_exigir();
            admin_cerrar();
            redirigir('/entrar?salida=1');
            break;

        case $ruta === '/panel':
            admin_exigir();
            echo vista_panel();
            break;

        case $ruta === '/robots.txt':
            header('Content-Type: text/plain; charset=utf-8');
            echo "User-agent: *\nAllow: /\nDisallow: /panel\nDisallow: /api/\nSitemap: " . APP_URL . "/sitemap.xml\n";
            break;

        case $ruta === '/sitemap.xml':
            echo vista_sitemap();
            break;

        default:
            http_response_code(404);
            echo vista_404();
    }
} catch (Throwable $error) {
    if (APP_DEBUG) {
        throw $error;
    }
    error_log('[tdl] ' . $error->getMessage() . ' @ ' . $error->getFile() . ':' . $error->getLine());
    http_response_code(500);
    if (str_starts_with($ruta, '/api/')) {
        salir_json(['ok' => false, 'error' => 'Error interno del servidor.'], 500);
    }
    echo vista_error();
}
