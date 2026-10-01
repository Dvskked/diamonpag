<?php
/* ============================================================================
 * The Diamonds League · páginas de cuenta (registro, acceso, perfil, datos)
 * neptun / andres / Dvskked — github.com/Dvskked
 * ========================================================================== */

/** Datos mínimos para el layout de las páginas de cuenta. */
function ctx_cuenta(): array
{
    return [
        'datos' => cargar_datos(),
        'usuario' => usuario_actual(),
        'body_class' => 'page-account'
    ];
}

/** Recoge un campo de texto del formulario. */
function campo(array $entrada, string $nombre, string $porDefecto = ''): string
{
    return trim((string) ($entrada[$nombre] ?? $porDefecto));
}

/** Muestra la lista de errores de un formulario. */
function lista_errores(array $errores, string $clase = ''): string
{
    if (!$errores) {
        return '';
    }
    $items = '';
    foreach ($errores as $error) {
        $items .= '<li>' . e($error) . '</li>';
    }
    return '<ul class="form-errors ' . e($clase) . '" role="alert">' . $items . '</ul>';
}

/** Aviso de éxito tras una acción. */
function aviso_ok(string $mensaje): string
{
    return $mensaje === '' ? '' : '<p class="form-ok" role="status">' . e($mensaje) . '</p>';
}

/* -------------------------------------------------------------------------
 * Registro
 * ---------------------------------------------------------------------- */
function vista_registro(string $metodo): string
{
    if (usuario_logueado()) {
        redirigir('/cuenta/perfil');
    }

    $errores = [];
    $valores = ['username' => '', 'email' => '', 'acepto' => false, 'boletin' => true];
    $google = google_disponible();

    if ($metodo === 'POST') {
        csrf_exigir();
        $entrada = cuerpo_form();
        $valores = [
            'username' => campo($entrada, 'username'),
            'email' => campo($entrada, 'email'),
            'acepto' => isset($entrada['acepto']),
            'boletin' => isset($entrada['boletin'])
        ];
        [$usuario, $errores] = usuario_registrar(
            $valores['username'],
            $valores['email'],
            (string) ($entrada['password'] ?? ''),
            (string) ($entrada['password_confirm'] ?? ''),
            $valores['acepto'],
            $valores['boletin']
        );
        if ($usuario !== null) {
            usuario_entrar($usuario);
            $destino = (string) ($entrada['volver'] ?? '');
            redirigir(url_interna($destino) !== '' ? $destino : '/cuenta/perfil?aviso=bienvenida');
        }
    }

    $formulario = '<form class="auth-form" method="post" action="/registro" novalidate>
      ' . csrf_campo() . '
      ' . lista_errores($errores) . '

      <label class="field">
        <span>Nombre de usuario <em>único</em></span>
        <input type="text" name="username" value="' . e($valores['username']) . '" required minlength="3" maxlength="32"
               autocomplete="username" pattern="[A-Za-z0-9._-]{3,32}" placeholder="neptun">
        <small>3 a 32 caracteres: letras, números, punto, guion y guion bajo.</small>
      </label>

      <label class="field">
        <span>Correo electrónico</span>
        <input type="email" name="email" value="' . e($valores['email']) . '" required maxlength="190" autocomplete="email"
               placeholder="tu@correo.com">
        <small>Solo se usa para el acceso, el aviso de novedades y la recuperación de cuenta.</small>
      </label>

      <div class="field-row">
        <label class="field">
          <span>Contraseña</span>
          <input type="password" name="password" required minlength="8" autocomplete="new-password" placeholder="Mínimo 8 caracteres">
        </label>
        <label class="field">
          <span>Repite la contraseña</span>
          <input type="password" name="password_confirm" required minlength="8" autocomplete="new-password" placeholder="Repite la clave">
        </label>
      </div>

      <label class="check">
        <input type="checkbox" name="acepto" value="1"' . ($valores['acepto'] ? ' checked' : '') . ' required>
        <span>He leído y acepto la <a href="/privacidad" target="_blank" rel="noopener">política de privacidad y el tratamiento de mis datos</a>.</span>
      </label>

      <label class="check">
        <input type="checkbox" name="boletin" value="1"' . ($valores['boletin'] ? ' checked' : '') . '>
        <span>Quiero recibir novedades y calendario por correo.</span>
      </label>

      <button class="btn btn-primary btn-block" type="submit">Crear mi cuenta</button>
      <p class="form-note">Ya tienes cuenta? <a href="/cuenta">Inicia sesión</a>.</p>
    </form>';

    $google = '<form class="oauth-form" method="post" action="/cuenta/google">'
        . csrf_campo()
        . ($google
            ? '<button class="btn btn-outline btn-block" type="submit">Continuar con Google</button>'
            : '<p class="form-note">El acceso con Google está desactivado hasta configurar las credenciales OAuth.</p>')
        . '</form>';

    $contenido = '<a class="skip-link" href="#contenido">Saltar al contenido</a>'
        . '<main class="auth-page" id="contenido"><div class="auth-card">'
        . '<header class="auth-head">'
        . '<p class="eyebrow">Cuenta de la liga</p>'
        . '<h1>Crea tu cuenta</h1>'
        . '<p>Regístrate para gestionar tu perfil, tu modo premium y tus datos desde la tuerca del sitio.</p>'
        . '</header>'
        . $formulario
        . '<div class="auth-divider"><span>o</span></div>'
        . $google
        . '<p class="auth-links"><a href="/">Volver a la liga</a> · <a href="/privacidad">Política de privacidad</a></p>'
        . '</div></main>';

    return layout(array_merge(ctx_cuenta(), [
        'title' => 'Crear cuenta · ' . APP_NOMBRE,
        'description' => 'Regístrate gratis en ' . APP_NOMBRE . ' para gestionar tu cuenta.',
        'canonical' => APP_URL . '/registro',
        'scripts' => ['/js/site.js']
    ]), $contenido);
}

/* -------------------------------------------------------------------------
 * Acceso de usuarios
 * ---------------------------------------------------------------------- */
function vista_cuenta_entrar(string $metodo): string
{
    if (usuario_logueado()) {
        redirigir('/cuenta/perfil');
    }

    $error = '';
    $volver = '';
    $identificador = '';
    $google = google_disponible();

    if ($metodo === 'POST') {
        csrf_exigir();
        $entrada = cuerpo_form();
        $identificador = campo($entrada, 'identificador');
        $volver = url_interna((string) ($entrada['volver'] ?? ''));
        if (!intentos_permitidos('usuario', $identificador)) {
            $error = 'Demasiados intentos. Espera unos minutos antes de volver a probar.';
        } else {
            $fila = usuario_credenciales($identificador, (string) ($entrada['password'] ?? ''));
            registrar_intento('usuario', $identificador, $fila !== null);
            if ($fila !== null) {
                usuario_entrar($fila);
                redirigir($volver !== '' ? $volver : '/cuenta/perfil?aviso=bienvenida');
            }
            $error = 'Usuario o contraseña incorrectos.';
        }
    } else {
        $volver = url_interna((string) ($_GET['volver'] ?? ''));
    }

    $formulario = '<form class="auth-form" method="post" action="/cuenta" novalidate>
      ' . csrf_campo() . '
      ' . ($error !== '' ? '<ul class="form-errors" role="alert"><li>' . e($error) . '</li></ul>' : '') . '
      <input type="hidden" name="volver" value="' . e($volver) . '">

      <label class="field">
        <span>Usuario o correo</span>
        <input type="text" name="identificador" value="' . e($identificador) . '" required autocomplete="username">
      </label>

      <label class="field">
        <span>Contraseña</span>
        <input type="password" name="password" required autocomplete="current-password">
      </label>

      <button class="btn btn-primary btn-block" type="submit">Entrar</button>
      <p class="form-note">¿No tienes cuenta? <a href="/registro">Regístrate gratis</a>.</p>
    </form>';

    $contenido = '<a class="skip-link" href="#contenido">Saltar al contenido</a>'
        . '<main class="auth-page" id="contenido"><div class="auth-card">'
        . '<header class="auth-head">'
        . '<p class="eyebrow">Cuenta de la liga</p>'
        . '<h1>Inicia sesión</h1>'
        . '<p>Accede a tu perfil, tu modo premium y tus datos personales.</p>'
        . '</header>'
        . $formulario
        . '<div class="auth-divider"><span>o</span></div>'
        . ($google
            ? '<form method="post" action="/cuenta/google">' . csrf_campo()
                . '<button class="btn btn-outline btn-block" type="submit">Continuar con Google</button></form>'
            : '<p class="form-note">El acceso con Google está desactivado hasta configurar las credenciales OAuth.</p>')
        . '<p class="auth-links"><a href="/">Volver a la liga</a> · <a href="/privacidad">Política de privacidad</a></p>'
        . '</div></main>';

    return layout(array_merge(ctx_cuenta(), [
        'title' => 'Iniciar sesión · ' . APP_NOMBRE,
        'description' => 'Accede a tu cuenta de ' . APP_NOMBRE . '.',
        'canonical' => APP_URL . '/cuenta',
        'scripts' => ['/js/site.js']
    ]), $contenido);
}

/* -------------------------------------------------------------------------
 * Perfil
 * ---------------------------------------------------------------------- */
function vista_perfil(string $metodo): string
{
    $usuario = usuario_exigir();
    $errores = [];
    $aviso = '';
    if (isset($_GET['aviso'])) {
        $aviso = match ((string) $_GET['aviso']) {
            'bienvenida' => '¡Cuenta creada! Ya puedes gestionar tu perfil desde la tuerca.',
            'premium' => $usuario['is_premium']
                ? 'Modo premium activado.'
                : 'Modo premium desactivado.',
            'perfil' => 'Perfil actualizado.',
            'google' => 'Cuenta de Google vinculada correctamente.',
            default => ''
        };
    }

    $valores = [
        'username' => (string) ($usuario['username'] ?? ''),
        'email' => (string) ($usuario['email'] ?? ''),
        'display_name' => (string) ($usuario['display_name'] ?? ''),
        'bio' => (string) ($usuario['bio'] ?? ''),
        'avatar_url' => (string) ($usuario['avatar_url'] ?? ''),
        'country' => (string) ($usuario['country'] ?? ''),
        'favorite_team' => (string) ($usuario['favorite_team'] ?? ''),
        'newsletter' => !empty($usuario['newsletter'])
    ];

    if ($metodo === 'POST') {
        csrf_exigir();
        $entrada = cuerpo_form();
        $entrada['newsletter'] = isset($entrada['newsletter']);
        foreach (['username', 'email', 'display_name', 'bio', 'avatar_url', 'country', 'favorite_team'] as $nombre) {
            $valores[$nombre] = campo($entrada, $nombre);
        }
        $valores['newsletter'] = isset($entrada['newsletter']);
        $errores = usuario_perfil_actualizar($usuario, $entrada);
        if (!$errores) {
            redirigir('/cuenta/perfil?aviso=perfil');
        }
    }

    $datos = cargar_datos();
    $opcionesEquipo = '';
    foreach ($datos['teams'] as $equipo) {
        $opcionesEquipo .= '<option value="' . e($equipo['name']) . '"'
            . ($valores['favorite_team'] === $equipo['name'] ? ' selected' : '') . '>' . e($equipo['name']) . '</option>';
    }

    $tarjetaPremium = '<div class="plan-card' . ($usuario['is_premium'] ? ' is-active' : '') . '">
      <span class="card-kicker">Modo premium</span>
      <h3>' . ($usuario['is_premium'] ? 'Premium activo' : 'Aún no eres premium') . '</h3>
      <p>El modo premium marca tu perfil en la liga y desbloquea los distintivos de la comunidad.</p>
      <form method="post" action="/cuenta/premium">' . csrf_campo()
        . '<button class="btn ' . ($usuario['is_premium'] ? 'btn-outline' : 'btn-primary') . ' btn-sm" type="submit">'
        . ($usuario['is_premium'] ? 'Desactivar premium' : 'Activar premium') . '</button></form>
    </div>';

    $contenido = '<a class="skip-link" href="#contenido">Saltar al contenido</a>'
        . '<main class="account-page" id="contenido"><div class="shell">'
        . '<header class="account-head">
          <div class="account-identity">
            <span class="account-avatar" aria-hidden="true">'
            . ($usuario['avatar_url']
                ? '<img src="' . e($usuario['avatar_url']) . '" width="72" height="72" alt="">'
                : e(mb_strtoupper(mb_substr($usuario['username'], 0, 1))))
            . '</span>
            <div>
              <p class="eyebrow">Mi cuenta</p>
              <h1>' . e($usuario['display_name'] ?: $usuario['username']) . '</h1>
              <p>@' . e($usuario['username'])
                . ($usuario['is_premium'] ? ' · <span class="chip chip-live">Premium</span>' : '')
                . ' · Miembro desde ' . e(fecha_larga($usuario['created_at'] ?: null)) . '</p>'
                . (!empty($usuario['google_id']) ? '<p class="form-note">Cuenta vinculada con Google.</p>' : '')
                . '</div>
          </div>
          <div class="account-actions">
            <a class="btn btn-outline btn-sm" href="/cuenta/password">Cambiar contraseña</a>'
            . (usuario_es_admin($usuario)
                ? '<a class="btn btn-primary btn-sm" href="/panel">Abrir modo admin</a>' : '')
            . '<form method="post" action="/salir">' . csrf_campo()
                . '<button class="btn btn-ghost btn-sm" type="submit">Cerrar sesión</button></form>'
            . '</div>
        </header>'
        . aviso_ok($aviso)
        . '<div class="account-grid">'
        . '<section class="account-panel"><h2>Editar perfil</h2>'
        . '<form class="auth-form" method="post" action="/cuenta/perfil" novalidate>'
        . csrf_campo() . lista_errores($errores) . '
            <div class="field-row">
              <label class="field">
                <span>Nombre de usuario</span>
                <input type="text" name="username" value="' . e($valores['username']) . '" required minlength="3" maxlength="32"
                       pattern="[A-Za-z0-9._-]{3,32}" autocomplete="username">
                <small>Es el nombre que ven los demás usuarios.</small>
              </label>
              <label class="field">
                <span>Nombre visible</span>
                <input type="text" name="display_name" value="' . e($valores['display_name']) . '" maxlength="60"
                       placeholder="' . e($valores['username']) . '">
              </label>
            </div>
            <div class="field-row">
              <label class="field">
                <span>Correo electrónico</span>
                <input type="email" name="email" value="' . e($valores['email']) . '" required maxlength="190" autocomplete="email">
              </label>
              <label class="field">
                <span>País</span>
                <input type="text" name="country" value="' . e($valores['country']) . '" maxlength="60" placeholder="Colombia">
              </label>
            </div>
            <label class="field">
              <span>Biografía</span>
              <textarea name="bio" rows="4" maxlength="400" placeholder="Cuéntanos de ti en la liga.">' . e($valores['bio']) . '</textarea>
            </label>
            <label class="field">
              <span>Foto de perfil (URL)</span>
              <input type="url" name="avatar_url" value="' . e($valores['avatar_url']) . '" maxlength="300" placeholder="https://…">
            </label>
            <label class="field">
              <span>Equipo favorito</span>
              <select name="favorite_team"><option value="">Sin preferencia</option>' . $opcionesEquipo . '</select>
            </label>
            <label class="check">
              <input type="checkbox" name="newsletter" value="1"' . ($valores['newsletter'] ? ' checked' : '') . '>
              <span>Quiero recibir novedades y calendario por correo.</span>
            </label>
            <button class="btn btn-primary" type="submit">Guardar cambios</button>
          </form>
        </section>'
        . '<aside class="account-side">'
        . $tarjetaPremium
        . '<div class="plan-card">
            <span class="card-kicker">Cuenta</span>
            <h3>Acceso con Google</h3>'
        . google_tarjeta_cuenta($usuario)
        . '</div>'
        . '<div class="plan-card">
            <span class="card-kicker">Privacidad</span>
            <h3>Tus datos</h3>
            <p>Descarga una copia de tus datos o elimina la cuenta cuando quieras.</p>
            <p class="chip-row"><a class="btn btn-outline btn-sm" href="/cuenta/datos">Ver mis datos</a>'
            . '<a class="btn btn-ghost btn-sm" href="/cuenta/eliminar">Eliminar cuenta</a></p>
            <p class="form-note"><a href="/privacidad">Leer la política completa</a></p>
          </div>'
        . '</aside>'
        . '</div>'
        . '</div></main>';

    return layout(array_merge(ctx_cuenta(), [
        'title' => 'Mi perfil · ' . APP_NOMBRE,
        'description' => 'Gestiona tu perfil de ' . APP_NOMBRE . '.',
        'canonical' => APP_URL . '/cuenta/perfil',
        'scripts' => ['/js/site.js']
    ]), $contenido);
}

/** Tarjeta del acceso con Google dentro del perfil. */
function google_tarjeta_cuenta(array $usuario): string
{
    if (!google_disponible()) {
        return '<p class="form-note">El acceso con Google está desactivado hasta configurar las credenciales OAuth.</p>';
    }
    if (!empty($usuario['google_id'])) {
        return '<p>Tu cuenta ya está vinculada a Google. Puedes entrar con Google o con tu contraseña.</p>';
    }
    return '<p>Vincula tu cuenta de Google para entrar sin contraseña.</p>'
        . '<form method="post" action="/cuenta/google">' . csrf_campo()
        . '<button class="btn btn-outline btn-sm" type="submit">Vincular Google</button></form>';
}

/* -------------------------------------------------------------------------
 * Cambio de contraseña
 * ---------------------------------------------------------------------- */
function vista_password(string $metodo): string
{
    $usuario = usuario_exigir();
    $errores = [];
    $tieneGoogle = !empty($usuario['google_id']);

    if ($metodo === 'POST') {
        csrf_exigir();
        $entrada = cuerpo_form();
        $tieneGoogle = !empty($usuario['google_id']);
        $errores = usuario_password_actualizar(
            $usuario,
            (string) ($entrada['actual'] ?? ''),
            (string) ($entrada['nueva'] ?? ''),
            (string) ($entrada['nueva_confirm'] ?? ''),
            !$tieneGoogle
        );
        if (!$errores) {
            redirigir('/cuenta/perfil?aviso=perfil');
        }
    }

    $tieneGoogle = !empty($usuario['google_id']);

    $formulario = '<form class="auth-form" method="post" action="/cuenta/password" novalidate>'
        . csrf_campo() . lista_errores($errores)
        . ($tieneGoogle
            ? '<p class="form-note">Tu cuenta está vinculada con Google, por eso no pedimos la contraseña actual.</p>'
            : '<label class="field">
                  <span>Contraseña actual</span>
                  <input type="password" name="actual" required autocomplete="current-password">
                </label>')
        . '<div class="field-row">'
        . '<label class="field">'
        . '<span>Nueva contraseña</span>'
        . '<input type="password" name="nueva" required minlength="8" autocomplete="new-password">'
        . '</label>'
        . '<label class="field">'
        . '<span>Repite la nueva contraseña</span>'
        . '<input type="password" name="nueva_confirm" required minlength="8" autocomplete="new-password">'
        . '</label>'
        . '</div>'
        . '<button class="btn btn-primary" type="submit">Actualizar contraseña</button>'
        . '</form>';

    $contenido = '<a class="skip-link" href="#contenido">Saltar al contenido</a>'
        . '<main class="account-page" id="contenido"><div class="shell">'
        . '<header class="account-head">
          <div class="account-identity">
            <div>
              <p class="eyebrow">Seguridad</p>
              <h1>Cambiar contraseña</h1>
              <p>Las contraseñas se guardan cifradas con <code>password_hash</code> y nunca se muestran.</p>
            </div>
          </div>
          <div class="account-actions"><a class="btn btn-outline btn-sm" href="/cuenta/perfil">Volver al perfil</a></div>
        </header>'
        . '<div class="account-grid"><section class="account-panel"><h2>Nueva contraseña</h2>'
        . $formulario . '</section></div>'
        . '</div></main>';

    return layout(array_merge(ctx_cuenta(), [
        'title' => 'Cambiar contraseña · ' . APP_NOMBRE,
        'canonical' => APP_URL . '/cuenta/password',
        'scripts' => ['/js/site.js']
    ]), $contenido);
}

/* -------------------------------------------------------------------------
 * Mis datos
 * ---------------------------------------------------------------------- */
function vista_datos(): string
{
    $usuario = usuario_exigir();
    $export = usuario_exportar($usuario);

    if (isset($_GET['formato']) && $_GET['formato'] === 'json') {
        header('Content-Type: application/json; charset=utf-8');
        header('Content-Disposition: attachment; filename="tdl-datos-' . e($usuario['username']) . '.json"');
        echo e_json($export);
        exit;
    }

    $tabla = '';
    foreach ((array) $export['cuenta'] as $clave => $valor) {
        if (is_array($valor) || is_bool($valor)) {
            $valor = json_encode($valor, JSON_UNESCAPED_UNICODE);
        }
        $tabla .= '<tr><th scope="row">' . e(str_replace('_', ' ', (string) $clave)) . '</th><td>'
            . e((string) ($valor === '' || $valor === null ? '—' : $valor)) . '</td></tr>';
    }

    $consents = '';
    foreach ((array) $export['consentimientos'] as $consent) {
        $consents .= '<li><strong>' . e($consent['doc_version'] ?? '') . '</strong> · '
            . e(fecha_larga($consent['created_at'] ?? null)) . ' · '
            . (!empty($consent['accepted']) ? 'Aceptado' : 'No aceptado') . ' · IP ' . e($consent['ip'] ?? '—') . '</li>';
    }

    $contenido = '<a class="skip-link" href="#contenido">Saltar al contenido</a>'
        . '<main class="account-page" id="contenido"><div class="shell">'
        . '<header class="account-head">
          <div class="account-identity"><div>
            <p class="eyebrow">Privacidad</p>
            <h1>Mis datos</h1>
            <p>Esto es exactamente lo que guardamos sobre tu cuenta.</p>
          </div></div>
          <div class="account-actions">
            <a class="btn btn-primary btn-sm" href="/cuenta/datos?formato=json">Descargar JSON</a>
            <a class="btn btn-outline btn-sm" href="/cuenta/perfil">Volver al perfil</a>
          </div>
        </header>'
        . '<div class="account-grid"><section class="account-panel">'
        . '<h2>Datos de la cuenta</h2>'
        . '<table class="data-table"><tbody>' . $tabla . '</tbody></table>'
        . ($consents !== '' ? '<h2>Consentimientos</h2><ul class="kv-list">' . $consents . '</ul>' : '')
        . '<h2>Documento</h2><ul class="kv-list"><li>Exportado el ' . e(fecha_larga($export['exportado_el'] ?? null))
            . '</li><li>Documento aplicado: ' . e((string) ($export['documento'] ?? '')) . '</li></ul>'
        . '</section>'
        . '<aside class="account-side">'
        . '<div class="plan-card">
            <span class="card-kicker">Tus derechos</span>
            <h3>Acceso, rectificación y borrado</h3>
            <p>Puedes editar tu perfil cuando quieras, exportar tus datos en JSON y eliminar la cuenta.</p>
            <p class="chip-row"><a class="btn btn-primary btn-sm" href="/cuenta/datos?formato=json">Exportar</a>'
            . '<a class="btn btn-ghost btn-sm" href="/cuenta/eliminar">Eliminar cuenta</a></p>
          </div>'
        . '<div class="plan-card">
            <span class="card-kicker">Documento</span>
            <h3>Política de privacidad</h3>
            <p>Versión ' . e(POLITICA_VERSION) . '. Última revisión: ' . e(fecha_larga(POLITICA_FECHA)) . '.</p>
            <p class="form-note"><a href="/privacidad">Leer la política completa</a></p>
          </div>'
        . '</aside></div>'
        . '</div></main>';

    return layout(array_merge(ctx_cuenta(), [
        'title' => 'Mis datos · ' . APP_NOMBRE,
        'canonical' => APP_URL . '/cuenta/datos',
        'scripts' => ['/js/site.js']
    ]), $contenido);
}

/* -------------------------------------------------------------------------
 * Eliminar cuenta
 * ---------------------------------------------------------------------- */
function vista_eliminar(string $metodo): string
{
    $usuario = usuario_exigir();
    $error = '';
    $hecho = false;

    if ($metodo === 'POST') {
        csrf_exigir();
        $entrada = cuerpo_form();
        $conGoogle = !empty($usuario['google_id']);
        if (campo($entrada, 'confirmar') !== 'ELIMINAR') {
            $error = 'Escribe ELIMINAR en mayúsculas para confirmar.';
        } elseif (!$conGoogle && usuario_credenciales($usuario['username'], (string) ($entrada['password'] ?? '')) === null) {
            $error = 'La contraseña no coincide.';
        } else {
            usuario_eliminar($usuario);
            $hecho = true;
        }
    }

    if ($hecho) {
        $contenido = '<main class="auth-page" id="contenido"><div class="auth-card">
          <header class="auth-head"><p class="eyebrow">Cuenta eliminada</p><h1>Hasta pronto</h1>
          <p>Tu cuenta y tus datos se han eliminado. Puedes volver a registrarte cuando quieras.</p></header>
          <a class="btn btn-primary btn-block" href="/">Volver a la liga</a>
        </div></main>';
        return layout(array_merge(ctx_cuenta(), [
            'title' => 'Cuenta eliminada · ' . APP_NOMBRE,
            'canonical' => APP_URL . '/'
        ]), $contenido);
    }

    $formulario = '<form class="auth-form danger" method="post" action="/cuenta/eliminar" novalidate>'
        . csrf_campo()
        . ($error !== '' ? '<ul class="form-errors" role="alert"><li>' . e($error) . '</li></ul>' : '')
        . '<p>Se borrarán tu perfil, tu contraseña, tu vinculación con Google y todos tus consentimientos. '
        . 'Esta acción no se puede deshacer.</p>'
        . (empty($usuario['google_id'])
            ? '<label class="field"><span>Tu contraseña</span>'
                . '<input type="password" name="password" required autocomplete="current-password"></label>'
            : '')
        . '<label class="field">
              <span>Escribe ELIMINAR para confirmar</span>
              <input type="text" name="confirmar" required pattern="ELIMINAR" placeholder="ELIMINAR">
            </label>'
        . '<button class="btn btn-danger" type="submit">Eliminar mi cuenta definitivamente</button>'
        . '<p class="form-note"><a href="/cuenta/datos">Antes de irte, descarga mis datos</a></p>'
        . '</form>';

    $contenido = '<a class="skip-link" href="#contenido">Saltar al contenido</a>'
        . '<main class="account-page" id="contenido"><div class="shell">'
        . '<header class="account-head"><div class="account-identity"><div>
            <p class="eyebrow">Privacidad</p>
            <h1>Eliminar cuenta</h1>
            <p>Borrado real de tus datos, sin dejar rastro en la base de datos.</p>
          </div></div>
          <div class="account-actions"><a class="btn btn-outline btn-sm" href="/cuenta/perfil">Cancelar</a></div>
        </header>'
        . '<div class="account-grid"><section class="account-panel"><h2>Borrado definitivo</h2>'
        . $formulario . '</section></div>'
        . '</div></main>';

    return layout(array_merge(ctx_cuenta(), [
        'title' => 'Eliminar cuenta · ' . APP_NOMBRE,
        'canonical' => APP_URL . '/cuenta/eliminar',
        'scripts' => ['/js/site.js']
    ]), $contenido);
}
