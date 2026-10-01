<?php
/* ============================================================================
 * The Diamonds League · funciones de apoyo
 * neptun / andres / Dvskked — github.com/Dvskked
 * Conserva este aviso de autoría.
 * ========================================================================== */

/** Escapa texto para HTML. Úsalo SIEMPRE al imprimir datos. */
function e(mixed $valor): string
{
    return htmlspecialchars((string) ($valor ?? ''), ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

/** Escapa para atributo y para JS embebido. */
function e_json(mixed $valor): string
{
    return htmlspecialchars(
        json_encode($valor, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_HEX_TAG | JSON_HEX_AMP),
        ENT_QUOTES,
        'UTF-8'
    );
}

/** Recorta un texto a un máximo de caracteres sin cortar palabras. */
function texto_corto(mixed $valor, int $max = 140, string $sufijo = '…'): string
{
    $texto = trim(preg_replace('/\s+/u', ' ', (string) ($valor ?? '')) ?? '');
    if ($texto === '' || mb_strlen($texto) <= $max) {
        return $texto;
    }
    $corte = mb_substr($texto, 0, $max);
    $espacio = mb_strrpos($corte, ' ');
    if ($espacio !== false && $espacio > $max * 0.6) {
        $corte = mb_substr($corte, 0, $espacio);
    }
    return rtrim($corte, " ,.;:") . $sufijo;
}

/** Fecha larga en español: "14 de marzo de 2026". */
function fecha_larga(?string $fecha): string
{
    if (!$fecha) {
        return '';
    }
    $ts = strtotime($fecha);
    if ($ts === false) {
        return '';
    }
    $meses = [
        1 => 'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
        'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
    ];
    return (int) date('j', $ts) . ' de ' . $meses[(int) date('n', $ts)] . ' de ' . date('Y', $ts);
}

/** Fecha corta: "14 mar". */
function fecha_corta(?string $fecha): string
{
    if (!$fecha) {
        return '';
    }
    $ts = strtotime($fecha);
    if ($ts === false) {
        return '';
    }
    $meses = [1 => 'ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];
    return date('j', $ts) . ' ' . $meses[(int) date('n', $ts)];
}

/** "Jornada 3" o etiqueta propia. */
function etiqueta_jornada(array $partido): string
{
    $label = trim((string) ($partido['journeyLabel'] ?? ''));
    return $label !== '' ? $label : 'Jornada ' . (int) ($partido['journey'] ?? 0);
}

/** Hora HH:MM o cadena vacía. */
function hora(?string $hora): string
{
    return $hora && preg_match('/^\d{2}:\d{2}/', $hora) ? substr($hora, 0, 5) : '';
}

/** Texto del estado de un partido. */
function estado_texto(string $estado): string
{
    return [
        'programado' => 'Programado',
        'en-vivo' => 'En vivo',
        'finalizado' => 'Finalizado',
        'wo' => 'W.O.',
        'pospuesto' => 'Pospuesto',
        'por-definir' => 'Por definir'
    ][$estado] ?? ucfirst(str_replace('-', ' ', $estado));
}

/** Texto de la fase del partido. */
function fase_texto(string $fase): string
{
    return ['liga' => 'Liga regular', 'playoffs' => 'Playoffs'][$fase] ?? ucfirst($fase);
}

/** Plural sencillo: plural(2, 'equipo', 'equipos'). */
function plural(int $n, string $singular, string $plural): string
{
    return $n === 1 ? $singular : $plural;
}

/** Decodifica un JSON guardado en TEXT; devuelve array vacío si falla. */
function json_seguro(?string $json, array $porDefecto = []): array
{
    if ($json === null || trim($json) === '') {
        return $porDefecto;
    }
    $datos = json_decode($json, true);
    return is_array($datos) ? $datos : $porDefecto;
}

/** Normaliza un usuario (@, espacios, mayúsculas) a 3-32 caracteres. */
function usuario_normalizado(string $valor): string
{
    $valor = strtolower(trim($valor));
    $valor = ltrim($valor, '@');
    $valor = preg_replace('/[^a-z0-9_.-]+/', '', $valor) ?? '';
    return substr($valor, 0, 32);
}

/** Quita acentos y baja a minúsculas: para buscar. */
function buscar_normalizado(string $valor): string
{
    $valor = mb_strtolower(trim($valor));
    $valor = preg_replace('/[áéíóúüñ]/u', ['a', 'e', 'i', 'o', 'u', 'u', 'n'], $valor) ?? $valor;
    return preg_replace('/\s+/u', ' ', $valor) ?? '';
}

/** IP del visitante. */
function ip_cliente(): string
{
    $ip = $_SERVER['REMOTE_ADDR'] ?? '0.0.0.0';
    return substr((string) $ip, 0, 45);
}

/** User agent recortado. */
function agente_cliente(): string
{
    return substr((string) ($_SERVER['HTTP_USER_AGENT'] ?? ''), 0, 255);
}

/** Envía JSON y termina. */
function responder_json(array $datos, int $codigo = 200): never
{
    http_response_code($codigo);
    header('Content-Type: application/json; charset=utf-8');
    header('Cache-Control: no-store');
    echo json_encode($datos, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

/** Redirige y termina. */
function redirigir(string $url, int $codigo = 302): never
{
    header('Location: ' . $url, true, $codigo);
    exit;
}

/** Lee el cuerpo JSON de la petición. */
function cuerpo_json(): array
{
    $crudo = file_get_contents('php://input');
    if (!$crudo) {
        return [];
    }
    $datos = json_decode($crudo, true);
    return is_array($datos) ? $datos : [];
}

/** Lee el cuerpo en formato formulario. */
function cuerpo_form(): array
{
    return $_POST;
}

/** Normaliza un valor a entero o null. */
function a_entero(mixed $valor): ?int
{
    if ($valor === '' || $valor === null) {
        return null;
    }
    return is_numeric($valor) ? (int) $valor : null;
}

/** Normaliza a float o null. */
function a_decimal(mixed $valor): ?float
{
    if ($valor === '' || $valor === null || !is_numeric($valor)) {
        return null;
    }
    return (float) $valor;
}

/** Normaliza a bool de campo de formulario o JSON. */
function a_bool(mixed $valor): bool
{
    return $valor === true || $valor === 1 || $valor === '1' || $valor === 'on'
        || $valor === 'true' || $valor === 'yes';
}

/** Valida una fecha YYYY-MM-DD. */
function fecha_valida(mixed $valor): string
{
    $valor = trim((string) ($valor ?? ''));
    if (!preg_match('/^\d{4}-\d{2}-\d{2}$/', $valor)) {
        return '';
    }
    [$a, $m, $d] = array_map('intval', explode('-', $valor));
    return checkdate($m, $d, $a) ? $valor : '';
}

/** Valida una hora HH:MM o HH:MM:SS. */
function hora_valida(mixed $valor): string
{
    $valor = trim((string) ($valor ?? ''));
    return preg_match('/^([01]\d|2[0-3]):([0-5]\d)(:[0-5]\d)?$/', $valor) ? $valor : '';
}

/** Recorta un texto a N caracteres. */
function str_corta(mixed $valor, int $max = 400): string
{
    return mb_substr(trim((string) ($valor ?? '')), 0, $max);
}

/** Deja solo una URL https (o http) válida; vacío si no. */
function url_segura(mixed $valor): string
{
    $valor = trim((string) ($valor ?? ''));
    if ($valor === '') {
        return '';
    }
    if (!preg_match('~^https?://[^\s"\'<>]+$~i', $valor)) {
        return '';
    }
    return $valor;
}

/** Id nuevo con prefijo: nuevo_id('match', 8). */
function nuevo_id(string $prefijo, int $largo = 6): string
{
    return $prefijo . '-' . substr(bin2hex(random_bytes(8)), 0, $largo);
}

/**
 * Normaliza una ruta interna usada en redirecciones, para no aceptar
 * URLs externas (open redirect). Devuelve vacío si no es válida.
 */
function url_interna(mixed $valor): string
{
    $valor = trim((string) ($valor ?? ''));
    if ($valor === '' || $valor === '/') {
        return '';
    }
    if (!str_starts_with($valor, '/') || str_starts_with($valor, '//') || str_starts_with($valor, '/\\')) {
        return '';
    }
    if (preg_match('/[\s"\'<>\\\\]/', $valor)) {
        return '';
    }
    if (!preg_match('#^/[a-zA-Z0-9\-/_.\-]*(?:\?[a-zA-Z0-9\-_=&%.]*)?$#', $valor)) {
        return '';
    }
    return $valor;
}

/** Comprueba que un id no tenga barras ni rutas. */
function id_valido(mixed $id): bool
{
    return is_string($id) && preg_match('/^[a-zA-Z0-9_-]{1,64}$/', $id) === 1;
}

/** Marca "https://www.tiktok.com/@x?foo" comoExternal para rel="noopener". */
function es_externo(string $url): bool
{
    return (bool) preg_match('~^https?://~i', $url);
}
