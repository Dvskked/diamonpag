<?php
/* ============================================================================
 * The Diamonds League · configuración de la aplicación
 * neptun / andres / Dvskked — github.com/Dvskked
 * Conserva este aviso de autoría.
 *
 * Las credenciales se leen de variables de entorno (ver .env.example).
 * En hosting compartido puedes definirlas también en el panel del hosting
 * o editar SOLO este bloque si lo prefieres.
 * ========================================================================== */

/** Carga un .env sencillo (clave=valor, líneas comentadas ignoradas). */
function cargar_env(string $archivo): void
{
    if (!is_file($archivo) || !is_readable($archivo)) {
        return;
    }
    $lineas = file($archivo, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lineas as $linea) {
        $linea = trim($linea);
        if ($linea === '' || str_starts_with($linea, '#')) {
            continue;
        }
        $pos = strpos($linea, '=');
        if ($pos === false) {
            continue;
        }
        $clave = trim(substr($linea, 0, $pos));
        $valor = trim(substr($linea, $pos + 1));
        $valor = trim($valor, "\"'");
        if ($clave === '' || getenv($clave) !== false) {
            continue;
        }
        putenv($clave . '=' . $valor);
        $_ENV[$clave] = $valor;
        $_SERVER[$clave] = $valor;
    }
}

cargar_env(__DIR__ . DIRECTORY_SEPARATOR . '.env');

/** Lee una variable de entorno con valor por defecto. */
function entorno(string $clave, ?string $porDefecto = null): ?string
{
    $valor = getenv($clave);
    if ($valor === false || $valor === '') {
        $valor = $_SERVER[$clave] ?? $_ENV[$clave] ?? null;
    }
    if ($valor === false || $valor === null || $valor === '') {
        return $porDefecto;
    }
    return (string) $valor;
}

define('APP_NOMBRE', entorno('APP_NAME', 'The Diamonds League'));
define('APP_RAIZ', __DIR__);
define('APP_URL', rtrim((string) entorno('SITE_URL', 'http://localhost:8000'), '/'));
define('APP_IDIOMA', 'es');
define('APP_ZONA', entorno('APP_TIMEZONE', 'America/Bogota'));
define('APP_DEBUG', entorno('APP_DEBUG', '0') === '1');

/* --- Base de datos (variables exigidas por conexion.php) --- */
define('DB_HOST', entorno('DB_HOST', '127.0.0.1'));
define('DB_PORT', entorno('DB_PORT', '3306'));
define('DB_NAME', entorno('DB_NAME', 'diamonds_league'));
define('DB_USER', entorno('DB_USER', 'root'));
define('DB_PASSWORD', entorno('DB_PASSWORD', ''));
define('DB_CHARSET', entorno('DB_CHARSET', 'utf8mb4'));

/* --- Sesiones --- */
define('SESION_NOMBRE', entorno('SESSION_NAME', 'tld_sesion'));
define('SESION_HORAS', (int) entorno('SESSION_HOURS', '8'));
define('SESION_SEGURA', entorno('SESSION_SECURE', '') === '1' || !empty($_SERVER['HTTPS']));

/* --- Administración (el acceso admin sigue con usuario y contraseña) --- */
define('ADMIN_USUARIO', entorno('ADMIN_USER', 'admin'));
define('ADMIN_PASSWORD', entorno('ADMIN_PASSWORD', ''));
define('LOGIN_MAX_INTENTOS', (int) entorno('LOGIN_MAX_ATTEMPTS', '8'));
define('LOGIN_BLOQUEO_MINUTOS', (int) entorno('LOGIN_LOCK_MINUTES', '10'));

/* --- Documento legal --- */
define('POLITICA_VERSION', entorno('POLICY_VERSION', '1.0'));
define('POLITICA_FECHA', entorno('POLICY_DATE', '2026-09-30'));
define('POLITICA_CONTACTO', entorno('POLICY_CONTACT', 'admin@diamondsleague.app'));
define('POLITICA_EMPRESA', entorno('POLICY_OWNER', 'The Diamonds League'));

/* --- Google (opcional) --- */
define('GOOGLE_CLIENT_ID', entorno('GOOGLE_CLIENT_ID', ''));
define('GOOGLE_CLIENT_SECRET', entorno('GOOGLE_CLIENT_SECRET', ''));
define('GOOGLE_REDIRECT', entorno('GOOGLE_REDIRECT', APP_URL . '/cuenta/google/callback'));

date_default_timezone_set(APP_ZONA);
mb_internal_encoding('UTF-8');
