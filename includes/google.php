<?php
/* ============================================================================
 * The Diamonds League · acceso con Google (opcional, OAuth 2.0)
 * neptun / andres / Dvskked — github.com/Dvskked
 *
 * Si no defines GOOGLE_CLIENT_ID y GOOGLE_CLIENT_SECRET en el .env,
 * google_disponible() devuelve false y toda la opción queda oculta.
 * ========================================================================== */

/** ¿Hay credenciales de Google configuradas? */
function google_disponible(): bool
{
    return GOOGLE_CLIENT_ID !== '' && GOOGLE_CLIENT_SECRET !== '' && GOOGLE_REDIRECT !== '';
}

/** Estado CSRF propio del flujo de Google, guardado en la sesión. */
function google_estado(): string
{
    sesion_iniciar();
    $estado = bin2hex(random_bytes(16));
    $_SESSION['google_estado'] = $estado;
    return $estado;
}

/** Arranca el flujo: recibe el POST, valida CSRF y manda a Google. */
function google_iniciar(string $metodo): never
{
    $destino = '/cuenta/perfil';
    if ($metodo === 'POST') {
        csrf_exigir();
        $entrada = cuerpo_form();
        $candidato = url_interna((string) ($entrada['destino'] ?? ''));
        if ($candidato !== '') {
            $destino = $candidato;
        }
    }
    if (!google_disponible()) {
        $_SESSION['flash'] = 'El acceso con Google no está configurado en este servidor.';
        redirigir($destino);
    }

    $url = 'https://accounts.google.com/o/oauth2/v2/auth?' . http_build_query([
        'client_id' => GOOGLE_CLIENT_ID,
        'redirect_uri' => GOOGLE_REDIRECT,
        'response_type' => 'code',
        'scope' => 'openid email profile',
        'access_type' => 'online',
        'prompt' => 'select_account',
        'state' => google_estado()
    ]);
    redirigir($url);
}

/** Callback de Google: cambia el código por tokens y vincula la cuenta. */
function google_callback(): never
{
    sesion_iniciar();
    $estadoRecibido = (string) ($_GET['state'] ?? '');
    $estadoGuardado = (string) ($_SESSION['google_estado'] ?? '');
    unset($_SESSION['google_estado']);

    if ($estadoGuardado === '' || !hash_equals($estadoGuardado, $estadoRecibido)) {
        google_fallar('La sesión de Google no es válida. Vuelve a intentarlo.');
    }
    if (!google_disponible()) {
        google_fallar('El acceso con Google no está configurado.');
    }
    if (isset($_GET['error'])) {
        google_fallar('Cancelaste el acceso con Google.');
    }
    $codigo = (string) ($_GET['code'] ?? '');
    if ($codigo === '') {
        google_fallar('Google no devolvió un código de acceso.');
    }

    $token = google_token($codigo);
    if ($token === null) {
        google_fallar('No se pudo canjear el código de acceso con Google.');
    }
    $perfil = google_perfil($token);
    if ($perfil === null || ($perfil['email'] ?? '') === '') {
        google_fallar('Google no devolvió un correo válido.');
    }

    $usuario = google_vincular($perfil);
    if ($usuario === null) {
        $_SESSION['flash'] = 'Ese correo ya está registrado con otra cuenta. Entra con tu contraseña y vincula Google desde tu perfil.';
        redirigir('/cuenta');
    }
    usuario_entrar($usuario);
    redirigir('/cuenta/perfil?aviso=google');
}

/** Intercambia el código por un access token. */
function google_token(string $codigo): ?string
{
    $respuesta = @file_get_contents('https://oauth2.googleapis.com/token', false, stream_context_create([
        'http' => [
            'method' => 'POST',
            'header' => 'Content-Type: application/x-www-form-urlencoded',
            'content' => http_build_query([
                'code' => $codigo,
                'client_id' => GOOGLE_CLIENT_ID,
                'client_secret' => GOOGLE_CLIENT_SECRET,
                'redirect_uri' => GOOGLE_REDIRECT,
                'grant_type' => 'authorization_code'
            ]),
            'timeout' => 10,
            'ignore_errors' => true
        ]
    ]));
    if ($respuesta === false) {
        return null;
    }
    $datos = json_decode($respuesta, true);
    return is_array($datos) && isset($datos['access_token']) ? (string) $datos['access_token'] : null;
}

/** Lee el perfil de Google con el token. */
function google_perfil(string $token): ?array
{
    $respuesta = @file_get_contents('https://www.googleapis.com/oauth2/v3/userinfo', false, stream_context_create([
        'http' => [
            'method' => 'GET',
            'header' => 'Authorization: Bearer ' . $token,
            'timeout' => 10,
            'ignore_errors' => true
        ]
    ]));
    if ($respuesta === false) {
        return null;
    }
    $datos = json_decode($respuesta, true);
    return is_array($datos) ? $datos : null;
}

/**
 * Vincula la cuenta de Google a un usuario existente o crea una nueva.
 * Devuelve la fila de usuario o null si el correo ya está en uso.
 */
function google_vincular(array $perfil): ?array
{
    $googleId = str_corta((string) ($perfil['sub'] ?? ''), 64);
    $email = mb_strtolower(trim((string) ($perfil['email'] ?? '')));
    if ($googleId === '' || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
        return null;
    }

    $fila = bd_fila('SELECT * FROM `usuarios` WHERE `google_id` = ?', [$googleId]);
    if ($fila !== null) {
        return $fila;
    }

    $fila = bd_fila('SELECT * FROM `usuarios` WHERE `email` = ?', [$email]);
    if ($fila !== null) {
        if (empty($fila['google_id'])) {
            bd_ejecutar('UPDATE `usuarios` SET `google_id` = ? WHERE `id` = ?', [$googleId, $fila['id']]);
            $fila['google_id'] = $googleId;
        }
        return $fila;
    }

    $base = usuario_normalizado((string) ($perfil['name'] ?? explode('@', $email)[0]));
    $base = preg_match('/^[a-z0-9_.-]{3,32}$/', $base) ? $base : 'jugador';
    $candidato = $base;
    $n = 1;
    while (!usuario_disponible($candidato)) {
        $n++;
        $candidato = $base . '-' . $n;
    }

    $nombre = str_corta((string) ($perfil['name'] ?? ''), 80);
    bd_ejecutar(
        'INSERT INTO `usuarios` (`username`,`email`,`password_hash`,`display_name`,`avatar_url`,`google_id`,'
        . '`newsletter`,`terms_accepted_at`,`created_at`,`last_login_at`) VALUES (?,?,?,?,?,?,?,NOW(),NOW(),NOW())',
        [
            $candidato,
            $email,
            password_hash(bin2hex(random_bytes(24)), PASSWORD_DEFAULT),
            $nombre !== '' ? $nombre : $candidato,
            url_segura((string) ($perfil['picture'] ?? '')),
            $googleId,
            0
        ]
    );
    $nuevoId = (int) bd()->lastInsertId();
    registrar_consentimiento($nuevoId, true, false);
    return bd_fila('SELECT * FROM `usuarios` WHERE `id` = ?', [$nuevoId]);
}

/** Error del flujo de Google con aviso en la sesión. */
function google_fallar(string $mensaje): never
{
    $_SESSION['flash'] = $mensaje;
    redirigir(usuario_logueado() ? '/cuenta/perfil' : '/cuenta');
}
