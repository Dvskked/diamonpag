<?php
/* ============================================================================
 * The Diamonds League · acceso del panel de administración
 * neptun / andres / Dvskked — github.com/Dvskked
 * ========================================================================== */

/** Inicio de sesión del staff. El acceso admin sigue siendo independiente. */
function vista_entrar(string $metodo): string
{
    if (admin_logueado()) {
        redirigir('/panel');
    }

    $error = '';
    $usuario = '';
    $google = google_disponible();
    $pendiente = !empty($_SESSION['admin_mensaje']) ? (string) $_SESSION['admin_mensaje'] : '';
    unset($_SESSION['admin_mensaje']);

    if ($metodo === 'POST') {
        csrf_exigir();
        $entrada = cuerpo_form();
        $usuario = campo($entrada, 'usuario');
        $clave = (string) ($entrada['password'] ?? '');
        if (!intentos_permitidos('admin', $usuario)) {
            $error = 'Demasiados intentos fallidos. Espera ' . LOGIN_BLOQUEO_MINUTOS . ' minutos.';
        } else {
            $ok = admin_entrar($usuario, $clave);
            registrar_intento('admin', $usuario, $ok);
            if ($ok) {
                redirigir('/panel');
            }
            $error = 'Usuario o contraseña de administración incorrectos.';
        }
    }

    $formulario = '<form class="auth-form" method="post" action="/entrar" novalidate>'
        . csrf_campo()
        . ($error !== '' ? '<ul class="form-errors" role="alert"><li>' . e($error) . '</li></ul>' : '')
        . ($pendiente !== '' ? '<p class="form-ok" role="status">' . e($pendiente) . '</p>' : '')
        . '<label class="field">
              <span>Usuario del staff</span>
              <input type="text" name="usuario" value="' . e($usuario) . '" required autocomplete="username" autofocus>
            </label>'
        . '<label class="field">
              <span>Contraseña</span>
              <input type="password" name="password" required autocomplete="current-password">
            </label>'
        . '<button class="btn btn-primary btn-block" type="submit">Entrar al panel</button>'
        . '<p class="form-note">' . plural(LOGIN_MAX_INTENTOS, 'intento disponible', 'intentos disponibles')
            . ' antes del bloqueo temporal.</p>'
        . '</form>';

    $extras = '';
    if ($google) {
        $extras = '<div class="auth-divider"><span>o</span></div>'
            . '<form method="post" action="/cuenta/google">' . csrf_campo()
            . '<input type="hidden" name="destino" value="/panel">'
            . '<button class="btn btn-outline btn-block" type="submit">Continuar con Google</button></form>';
    }

    $contenido = '<a class="skip-link" href="#contenido">Saltar al contenido</a>'
        . '<main class="auth-page is-admin" id="contenido"><div class="auth-card">'
        . '<header class="auth-head">
          <img src="/assets/logo-mark.png" width="56" height="56" alt="" aria-hidden="true" class="auth-logo">
          <p class="eyebrow">Staff</p>
          <h1>Panel de administración</h1>
          <p>Acceso exclusivo del staff. Las cuentas de usuario no entran aquí.</p>
        </header>'
        . $formulario
        . $extras
        . '<p class="auth-links"><a href="/">Volver al sitio</a> · <a href="/cuenta">Soy usuario registrado</a>'
        . ' · <a href="/privacidad">Privacidad</a></p>'
        . '</div></main>';

    return layout([
        'datos' => cargar_datos(),
        'usuario' => usuario_actual(),
        'title' => 'Acceso staff · ' . APP_NOMBRE,
        'description' => 'Acceso privado del panel de administración de ' . APP_NOMBRE . '.',
        'canonical' => APP_URL . '/entrar',
        'body_class' => 'page-login',
        'scripts' => ['/js/site.js']
    ], $contenido);
}
