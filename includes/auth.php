<?php
/* ============================================================================
 * The Diamonds League · sesiones, acceso admin y acceso de usuarios
 * neptun / andres / Dvskked — github.com/Dvskked
 * Conserva este aviso de autoría.
 *
 * - El acceso de administración sigue con usuario y contraseña (variables de
 *   entorno), tal como estaba.
 * - Los usuarios se registran en la tabla `usuarios` con contraseña cifrada
 *   con password_hash() de PHP (bcrypt), nunca en texto plano.
 * - Todas las operaciones que cambian datos exigen un token CSRF.
 * ========================================================================== */

require_once __DIR__ . '/../conexion.php';
require_once __DIR__ . '/helpers.php';
require_once __DIR__ . '/bd.php';

/** Arranca la sesión con cookie segura. */
function sesion_iniciar(): void
{
    if (session_status() === PHP_SESSION_ACTIVE) {
        return;
    }
    session_name(SESION_NOMBRE);
    session_set_cookie_params([
        'lifetime' => 0,
        'path' => '/',
        'domain' => '',
        'secure' => SESION_SEGURA,
        'httponly' => true,
        'samesite' => 'Lax'
    ]);
    session_start();
    if (empty($_SESSION['creado'])) {
        $_SESSION['creado'] = time();
    }
}

/* -------------------------------------------------------------------------
 * Protección CSRF
 * ---------------------------------------------------------------------- */

/** Devuelve (y crea) el token CSRF de la sesión. */
function csrf_token(): string
{
    sesion_iniciar();
    if (empty($_SESSION['csrf']) || !is_string($_SESSION['csrf'])) {
        $_SESSION['csrf'] = bin2hex(random_bytes(32));
    }
    return $_SESSION['csrf'];
}

/** Comprueba el token recibido (form o cabecera X-CSRF-Token). */
function csrf_valido(mixed $token = null): bool
{
    sesion_iniciar();
    if ($token === null) {
        $token = $_POST['csrf'] ?? ($_SERVER['HTTP_X_CSRF_TOKEN'] ?? '');
    }
    $guardado = $_SESSION['csrf'] ?? '';
    return is_string($guardado) && $guardado !== '' && is_string($token)
        && hash_equals($guardado, $token);
}

/** Campo oculto para los formularios. */
function csrf_campo(): string
{
    return '<input type="hidden" name="csrf" value="' . e(csrf_token()) . '">';
}

/** Corta la petición si el token no es válido. */
function csrf_exigir(): void
{
    if (!csrf_valido()) {
        if (wants_json()) {
            responder_json(['ok' => false, 'error' => 'Sesión caducada. Recarga la página.'], 419);
        }
        http_response_code(419);
        exit('Sesión caducada. Vuelve a la página e inténtalo de nuevo.');
    }
}

/** ¿La petición espera JSON? */
function wants_json(): bool
{
    if (isset($_SERVER['HTTP_ACCEPT']) && str_contains($_SERVER['HTTP_ACCEPT'], 'application/json')) {
        return true;
    }
    return str_starts_with((string) ($_SERVER['HTTP_X_REQUESTED_WITH'] ?? ''), 'fetch');
}

/* -------------------------------------------------------------------------
 * Acceso de administración (usuario y contraseña, como antes)
 * ---------------------------------------------------------------------- */

function admin_logueado(): bool
{
    sesion_iniciar();
    $desde = (int) ($_SESSION['admin_desde'] ?? 0);
    if ($desde === 0) {
        return false;
    }
    if (time() - $desde > SESION_HORAS * 3600) {
        unset($_SESSION['admin_desde']);
        return false;
    }
    return true;
}

/** Comprueba las credenciales de administración. */
function admin_credenciales(string $usuario, string $password): bool
{
    if (ADMIN_PASSWORD === '') {
        return false;
    }
    $okUsuario = hash_equals(ADMIN_USUARIO, $usuario);
    $okClave = hash_equals(ADMIN_PASSWORD, $password);
    return $okUsuario && $okClave;
}

function admin_entrar(string $usuario, string $password): bool
{
    sesion_iniciar();
    if (!admin_credenciales($usuario, $password)) {
        return false;
    }
    session_regenerate_id(true);
    $_SESSION['admin_desde'] = time();
    return true;
}

function admin_cerrar(): void
{
    sesion_iniciar();
    unset($_SESSION['admin_desde']);
}

/** Corta la petición si no hay sesión de administración. */
function admin_exigir(): void
{
    if (!admin_logueado()) {
        if (wants_json()) {
            responder_json(['ok' => false, 'error' => 'Necesitas iniciar sesión en el panel.'], 401);
        }
        redirigir('/entrar');
    }
}

/* -------------------------------------------------------------------------
 * Usuarios registrados
 * ---------------------------------------------------------------------- */

/** Datos del usuario en sesión, o null. */
function usuario_actual(): ?array
{
    sesion_iniciar();
    $id = (int) ($_SESSION['usuario_id'] ?? 0);
    if ($id === 0) {
        return null;
    }
    $fila = bd_fila(
        'SELECT id, username, email, display_name, bio, avatar_url, country, favorite_team,'
        . ' is_premium, is_admin, google_id, newsletter, created_at, last_login_at'
        . ' FROM `usuarios` WHERE `id` = ?',
        [$id]
    );
    if ($fila === null) {
        unset($_SESSION['usuario_id']);
        return null;
    }
    $fila['id'] = (int) $fila['id'];
    $fila['is_premium'] = (bool) $fila['is_premium'];
    $fila['is_admin'] = (bool) $fila['is_admin'];
    return $fila;
}

function usuario_logueado(): bool
{
    return usuario_actual() !== null;
}

/** Corta la petición si no hay usuario registrado, guardando el destino. */
function usuario_exigir(): array
{
    $usuario = usuario_actual();
    if ($usuario === null) {
        if (wants_json()) {
            responder_json(['ok' => false, 'error' => 'Necesitas iniciar sesión.'], 401);
        }
        $destino = (string) ($_SERVER['REQUEST_URI'] ?? '/');
        redirigir('/cuenta?volver=' . rawurlencode($destino));
    }
    return $usuario;
}

/** ¿Puede este usuario abrir el panel? */
function usuario_es_admin(array $usuario): bool
{
    return $usuario['is_admin'] || hash_equals(ADMIN_USUARIO, (string) $usuario['username']);
}

/** Username libre. */
function usuario_disponible(string $usuario): bool
{
    return bd_valor('SELECT COUNT(*) FROM `usuarios` WHERE `username` = ?', [$usuario], 0) === 0;
}

/** Correo libre. */
function correo_disponible(string $email): bool
{
    return bd_valor('SELECT COUNT(*) FROM `usuarios` WHERE `email` = ?', [$email], 0) === 0;
}

/**
 * Registra un usuario. Devuelve [usuario|null, lista de errores].
 * El boletín es opcional y solo se guarda si el usuario lo marcó.
 */
function usuario_registrar(string $usuario, string $email, string $password, string $confirmar, bool $acepta, bool $boletin = false): array
{
    $errores = [];
    $usuario = usuario_normalizado($usuario);
    $email = mb_strtolower(trim($email));

    if (strlen($usuario) < 3 || strlen($usuario) > 32) {
        $errores[] = 'El nombre de usuario debe tener entre 3 y 32 caracteres.';
    }
    if (!preg_match('/^[a-z0-9_.-]+$/', $usuario)) {
        $errores[] = 'El nombre de usuario solo admite letras, números, punto, guion y guion bajo.';
    }
    if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
        $errores[] = 'Escribe un correo electrónico válido.';
    }
    if (mb_strlen($password) < 8) {
        $errores[] = 'La contraseña debe tener al menos 8 caracteres.';
    }
    if (!hash_equals($password, $confirmar)) {
        $errores[] = 'Las contraseñas no coinciden.';
    }
    if (!$acepta) {
        $errores[] = 'Tienes que aceptar la política de privacidad y el tratamiento de datos.';
    }
    if ($errores) {
        return [null, $errores];
    }
    if (!usuario_disponible($usuario)) {
        return [null, ['Ese nombre de usuario ya está en uso.']];
    }
    if (!correo_disponible($email)) {
        return [null, ['Ese correo electrónico ya está registrado.']];
    }

    $hash = password_hash($password, PASSWORD_DEFAULT);
    if ($hash === false) {
        return [null, ['No se pudo cifrar la contraseña. Inténtalo de nuevo.']];
    }

    $stmt = bd_ejecutar(
        'INSERT INTO `usuarios` (`username`,`email`,`password_hash`,`display_name`,`newsletter`,`terms_accepted_at`,`created_at`)'
        . ' VALUES (?,?,?,?,?,NOW(),NOW())',
        [$usuario, $email, $hash, $usuario, a_bool($boletin) ? 1 : 0]
    );
    $id = (int) bd()->lastInsertId();
    registrar_consentimiento($id);

    return [[
        'id' => $id,
        'username' => $usuario,
        'email' => $email,
        'display_name' => $usuario,
        'bio' => '',
        'avatar_url' => '',
        'country' => '',
        'favorite_team' => '',
        'is_premium' => false,
        'is_admin' => false,
        'google_id' => null,
        'newsletter' => a_bool($boletin),
        'created_at' => date('Y-m-d H:i:s'),
        'last_login_at' => null
    ], []];
}

/** Registra la aceptación del documento de privacidad. */
function registrar_consentimiento(int $usuarioId, bool $aceptado = true, bool $boletin = false): void
{
    if ($usuarioId <= 0) {
        return;
    }
    bd_ejecutar(
        'INSERT INTO `consentimientos` (`user_id`,`doc_version`,`accepted`,`newsletter`,`ip`,`user_agent`)'
        . ' VALUES (?,?,?,?,?,?)',
        [$usuarioId, POLITICA_VERSION, $aceptado ? 1 : 0, $boletin ? 1 : 0, ip_cliente(), agente_cliente()]
    );
}

/** Valida las credenciales de un usuario (usuario o correo). */
function usuario_credenciales(string $identificador, string $password): ?array
{
    $identificador = trim($identificador);
    if ($identificador === '' || $password === '') {
        return null;
    }
    $fila = bd_fila(
        'SELECT * FROM `usuarios` WHERE `username` = ? OR `email` = ? LIMIT 1',
        [$identificador, mb_strtolower($identificador)]
    );
    if ($fila === null) {
        // hashing falso para no filtrar por tiempo si el usuario existe
        password_verify($password, '$2y$10$usKixp1gBqU7Hr5Z5b3Zz7OY0kk9y8vXa1nE0oHq0oOaJmZ9l5Qq');
        return null;
    }
    if (!password_verify($password, (string) $fila['password_hash'])) {
        return null;
    }
    if (password_needs_rehash((string) $fila['password_hash'], PASSWORD_DEFAULT)) {
        $nuevo = password_hash($password, PASSWORD_DEFAULT);
        if ($nuevo !== false) {
            bd_ejecutar('UPDATE `usuarios` SET `password_hash` = ? WHERE `id` = ?', [$nuevo, $fila['id']]);
        }
    }
    return $fila;
}

function usuario_entrar(array $fila): void
{
    sesion_iniciar();
    session_regenerate_id(true);
    $_SESSION['usuario_id'] = (int) $fila['id'];
    bd_ejecutar('UPDATE `usuarios` SET `last_login_at` = NOW() WHERE `id` = ?', [$fila['id']]);
}

function usuario_cerrar(): void
{
    sesion_iniciar();
    $id = (int) ($_SESSION['usuario_id'] ?? 0);
    unset($_SESSION['usuario_id']);
    if ($id > 0) {
        session_regenerate_id(true);
    }
}

/** Guarda el perfil del usuario. Devuelve [errores]. */
function usuario_perfil_actualizar(array $usuario, array $entrada): array
{
    $errores = [];
    $nuevoUsuario = usuario_normalizado((string) ($entrada['username'] ?? $usuario['username']));
    $email = mb_strtolower(trim((string) ($entrada['email'] ?? $usuario['email'])));

    if (strlen($nuevoUsuario) < 3 || !preg_match('/^[a-z0-9_.-]+$/', $nuevoUsuario)) {
        $errores[] = 'El nombre de usuario debe tener entre 3 y 32 caracteres válidos.';
    } elseif ($nuevoUsuario !== $usuario['username'] && !usuario_disponible($nuevoUsuario)) {
        $errores[] = 'Ese nombre de usuario ya está en uso.';
    }
    if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
        $errores[] = 'Escribe un correo electrónico válido.';
    } elseif ($email !== $usuario['email'] && !correo_disponible($email)) {
        $errores[] = 'Ese correo electrónico ya está registrado.';
    }
    if ($errores) {
        return $errores;
    }

    bd_ejecutar(
        'UPDATE `usuarios` SET `username` = ?, `email` = ?, `display_name` = ?, `bio` = ?,'
        . ' `avatar_url` = ?, `country` = ?, `favorite_team` = ?, `newsletter` = ? WHERE `id` = ?',
        [
            $nuevoUsuario,
            $email,
            str_corta($entrada['display_name'] ?? $usuario['username'], 80),
            str_corta($entrada['bio'] ?? '', 400),
            url_segura($entrada['avatar_url'] ?? ''),
            str_corta($entrada['country'] ?? '', 60),
            str_corta($entrada['favorite_team'] ?? '', 80),
            a_bool($entrada['newsletter'] ?? false) ? 1 : 0,
            $usuario['id']
        ]
    );
    return [];
}

/**
 * Cambia la contraseña. Devuelve la lista de errores (vacía si todo fue bien).
 * Las cuentas vinculadas con Google pueden fijar la primera contraseña sin
 * teclear la anterior, porque nunca se guardó una contraseña local.
 */
function usuario_password_actualizar(array $usuario, string $actual, string $nueva, string $confirmar, bool $exigirActual = true): array
{
    if ($exigirActual) {
        $fila = bd_fila('SELECT password_hash FROM `usuarios` WHERE `id` = ?', [$usuario['id']]);
        if ($fila === null || !password_verify($actual, (string) $fila['password_hash'])) {
            return ['La contraseña actual no es correcta.'];
        }
    }
    if (mb_strlen($nueva) < 8) {
        return ['La nueva contraseña debe tener al menos 8 caracteres.'];
    }
    if (!hash_equals($nueva, $confirmar)) {
        return ['Las contraseñas no coinciden.'];
    }
    if (hash_equals($actual, $nueva)) {
        return ['La nueva contraseña debe ser distinta de la actual.'];
    }
    $hash = password_hash($nueva, PASSWORD_DEFAULT);
    if ($hash === false) {
        return ['No se pudo cifrar la contraseña.'];
    }
    bd_ejecutar('UPDATE `usuarios` SET `password_hash` = ? WHERE `id` = ?', [$hash, $usuario['id']]);
    return [];
}

/** Activa o desactiva el modo premium. */
function usuario_premium_actualizar(array $usuario, bool $activo): void
{
    bd_ejecutar('UPDATE `usuarios` SET `is_premium` = ? WHERE `id` = ?', [$activo ? 1 : 0, $usuario['id']]);
}

/** Datos del usuario listos para exportar (derechos de acceso y portabilidad). */
function usuario_exportar(array $usuario): array
{
    $fila = bd_fila('SELECT * FROM `usuarios` WHERE `id` = ?', [$usuario['id']]) ?? [];
    unset($fila['password_hash']);
    $consentimientos = bd_todas(
        'SELECT doc_version, accepted, ip, user_agent, created_at FROM `consentimientos` WHERE `user_id` = ? ORDER BY created_at',
        [$usuario['id']]
    );
    return [
        'exportado_el' => date('c'),
        'documento' => 'privacidad-v' . POLITICA_VERSION,
        'cuenta' => $fila,
        'consentimientos' => $consentimientos
    ];
}

/** Elimina la cuenta y todos sus datos. */
function usuario_eliminar(array $usuario): void
{
    $id = $usuario['id'];
    bd_ejecutar('DELETE FROM `usuarios` WHERE `id` = ?', [$id]);
    usuario_cerrar();
}

/* -------------------------------------------------------------------------
 * Limitación de intentos (fuerza bruta)
 * ---------------------------------------------------------------------- */

/** ¿Se puede intentar? Bloquea 10 minutos tras 8 fallos desde la misma IP. */
function intentos_permitidos(string $scope, string $identificador = ''): bool
{
    return !login_bloqueado($scope, $identificador);
}

function login_bloqueado(string $scope, string $identificador = ''): bool
{
    $fallos = bd_valor(
        'SELECT COUNT(*) FROM `intentos` WHERE `scope` = ? AND `ip` = ? AND `ok` = 0 AND `created_at` > (NOW() - INTERVAL '
        . LOGIN_BLOQUEO_MINUTOS . ' MINUTE)',
        [$scope, ip_cliente()],
        0
    );
    return (int) $fallos >= LOGIN_MAX_INTENTOS;
}

function registrar_intento(string $scope, string $identificador, bool $ok): void
{
    bd_ejecutar(
        'INSERT INTO `intentos` (`scope`,`ip`,`identifier`,`ok`) VALUES (?,?,?,?)',
        [$scope, ip_cliente(), str_corta($identificador, 190), $ok ? 1 : 0]
    );
    if ($ok) {
        bd_ejecutar('DELETE FROM `intentos` WHERE `scope` = ? AND `ip` = ? AND `ok` = 0', [$scope, ip_cliente()]);
    }
}
