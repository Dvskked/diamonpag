<?php
/* ============================================================================
 * The Diamonds League · política de privacidad y protección de datos
 * neptun / andres / Dvskked — github.com/Dvskked
 * ========================================================================== */

/** Documento legal integrado en el sitio. */
function vista_privacidad(): string
{
    $actualizado = POLITICA_FECHA;
    $contacto = POLITICA_CONTACTO;

    $secciones = [
        [
            'id' => 'responsable',
            'titulo' => '1. Quién es el responsable',
            'html' => '<p>Este sitio es una publicación no oficial de la comunidad de HaxBall. El responsable del '
                . 'tratamiento es <strong>' . e(POLITICA_EMPRESA) . '</strong>, que lo opera '
                . 'de forma voluntaria y sin ánimo de lucro.</p>'
                . '<p>Para cualquier consulta sobre datos personales puedes escribir a '
                . '<a href="mailto:' . e($contacto) . '">' . e($contacto) . '</a>.</p>'
        ],
        [
            'id' => 'datos',
            'titulo' => '2. Qué datos recogemos',
            'html' => '<p>Si solo navegas el sitio no recogemos datos personales: no hay cookies de seguimiento, '
                . 'ni analítica, ni publicidad de terceros.</p>'
                . '<p>Si te registras en el área de usuario guardamos:</p>'
                . '<ul class="ticks">'
                . '<li><strong>Nombre de usuario</strong> y nombre visible, para mostrar tu perfil en la liga.</li>'
                . '<li><strong>Correo electrónico</strong>, para el acceso a la cuenta y para avisar de novedades si lo pides.</li>'
                . '<li><strong>Contraseña</strong>, cifrada de forma irreversible con <code>password_hash</code> (bcrypt). '
                . 'Nunca almacenamos ni podemos leer tu contraseña.</li>'
                . '<li><strong>Biografía, país, equipo favorito y foto de perfil</strong>, solo si los rellenas.</li>'
                . '<li><strong>Identificador de Google</strong>, únicamente si vinculas tu cuenta con Google.</li>'
                . '<li><strong>Dirección IP y navegador</strong> del intento de acceso, durante un máximo de '
                . e((string) LOGIN_BLOQUEO_MINUTOS) . ' minutos, como protección frente a ataques de fuerza bruta.</li>'
                . '<li><strong>Consentimientos</strong>: versión del documento, fecha, IP y navegador.</li>'
                . '</ul>'
        ],
        [
            'id' => 'finalidad',
            'titulo' => '3. Para qué usamos los datos',
            'html' => '<ul class="ticks">'
                . '<li>Crear y mantener tu cuenta de usuario.</li>'
                . '<li>Iniciar sesión de forma segura.</li>'
                . '<li>Enseñarte el contenido público de la liga, como standings, calendario y noticias.</li>'
                . '<li>Enviarte el boletín de novedades si lo aceptas.</li>'
                . '<li>Proteger el sitio y el panel de administración.</li>'
                . '</ul>'
                . '<p>No vendemos, alquilamos ni cedemos tus datos a terceros con fines comerciales.</p>'
        ],
        [
            'id' => 'base',
            'titulo' => '4. Base jurídica',
            'html' => '<p>Tratamos tus datos con tu <strong>consentimiento</strong> al registrarte y aceptar este '
                . 'documento, y con tu <strong>interés legítimo</strong> para mantener la seguridad del sitio '
                . '(registro de accesos y límite de intentos).</p>'
        ],
        [
            'id' => 'conservacion',
            'titulo' => '5. Cuánto tiempo conservamos los datos',
            'html' => '<p>Los datos de la cuenta se conservan mientras la cuenta esté activa. El registro de intentos '
                . 'de acceso se borra automáticamente pasado un plazo breve. Al eliminar la cuenta, tus datos se '
                . 'borran de la base de datos en el momento.</p>'
        ],
        [
            'id' => 'destinatarios',
            'titulo' => '6. Destinatarios y transferencia internacional',
            'html' => '<p>Los datos se guardan en la base de datos MySQL del servidor que aloja este sitio. Si usas el '
                . 'inicio de sesión con Google, Google trata tus datos según su propia política para autenticar la '
                . 'sesión; en ese caso la transferencia se rige por las garantías del proveedor.</p>'
        ],
        [
            'id' => 'derechos',
            'titulo' => '7. Tus derechos',
            'html' => '<p>Puedes ejercer en cualquier momento los derechos de <strong>acceso, rectificación, supresión, '
                . 'oposición, portabilidad y limitación</strong>:</p>'
                . '<ul class="ticks">'
                . '<li><a href="/cuenta/datos">Descargar todos tus datos</a> en un archivo JSON.</li>'
                . '<li><a href="/cuenta/perfil">Editar tu perfil</a> y cambiar tu correo o contraseña.</li>'
                . '<li><a href="/cuenta/eliminar">Eliminar tu cuenta</a> y con ella todos tus datos.</li>'
                . '<li>Escribir a <a href="mailto:' . e($contacto) . '">' . e($contacto) . '</a> para cualquier otra solicitud.</li>'
                . '</ul>'
        ],
        [
            'id' => 'cookies',
            'titulo' => '8. Cookies',
            'html' => '<p>Solo usamos una cookie técnica de sesión, imprescindible para mantener tu sesión iniciada y '
                . 'proteger los formularios. No se instalan cookies publicitarias ni de seguimiento. Puedes rechazar '
                . 'todo salvo la sesión y seguir viendo todo el contenido público.</p>'
        ],
        [
            'id' => 'menores',
            'titulo' => '9. Menores de edad',
            'html' => '<p>Este sitio está dirigido a mayores de 13 años. No registramos de forma intencionada a '
                . 'menores; si crees que una cuenta corresponde a un menor, escríbenos y la eliminaremos.</p>'
        ],
        [
            'id' => 'seguridad',
            'titulo' => '10. Seguridad',
            'html' => '<p>Usamos consultas preparadas, cifrado de contraseñas con bcrypt, tokens anti-CSRF en todos los '
                . 'formularios y limitación de intentos de acceso. Ningún sistema es infalible: si ocurre una brecha que '
                . 'afecte a tus datos, te avisaremos lo antes posible.</p>'
        ],
        [
            'id' => 'derecho',
            'titulo' => '11. Tus derechos como usuario y cómo reclamar',
            'html' => '<p>Puedes reclamar ante la autoridad de control competente si consideras que no tratamos '
                . 'correctamente tus datos. Cuantos más datos nos facilites, <strong>más rápido</strong> podremos '
                . 'ayudarte, y puedes ejercer tus derechos sin tener cuenta registrada.</p>'
        ],
        [
            'id' => 'cambios',
            'titulo' => '12. Cambios en esta política',
            'html' => '<p>Si actualizamos este documento cambiaremos la fecha de la parte superior. Los cambios '
                . 'importantes se anunciarán en la web. Versión actual: <strong>' . e(POLITICA_VERSION) . '</strong>, '
                . 'vigente desde el <strong>' . e(fecha_larga($actualizado)) . '</strong>.</p>'
        ]
    ];

    $indice = '';
    foreach ($secciones as $seccion) {
        $indice .= '<li><a href="#' . e($seccion['id']) . '">' . e($seccion['titulo']) . '</a></li>';
    }
    $cuerpo = '';
    foreach ($secciones as $seccion) {
        $cuerpo .= '<section class="legal-block" id="' . e($seccion['id']) . '">'
            . '<h2>' . e($seccion['titulo']) . '</h2>'
            . $seccion['html']
            . '</section>';
    }

    $contenido = '<a class="skip-link" href="#contenido">Saltar al contenido</a>'
        . '<main class="legal-page" id="contenido"><div class="shell">'
        . '<header class="legal-head">
          <p class="eyebrow">Legal</p>
          <h1>Política de privacidad y protección de datos</h1>
          <p>' . e(POLITICA_EMPRESA) . ' · versión ' . e(POLITICA_VERSION) . ' · vigente desde el '
            . e(fecha_larga($actualizado)) . '</p>
        </header>'
        . '<div class="legal-layout">
          <nav class="legal-toc" aria-label="Índice del documento"><ul>' . $indice . '</ul></nav>'
          . '<div class="legal-body">' . $cuerpo . '</div>'
        . '</div>'
        . '<p class="legal-foot"><a class="btn btn-outline btn-sm" href="/">Volver al sitio</a> · '
            . '<a href="mailto:' . e($contacto) . '">' . e($contacto) . '</a></p>'
        . '</div></main>';

    return layout([
        'datos' => cargar_datos(),
        'usuario' => usuario_actual(),
        'title' => 'Política de privacidad · ' . APP_NOMBRE,
        'description' => 'Política de privacidad y protección de datos de ' . APP_NOMBRE . '.',
        'canonical' => APP_URL . '/privacidad',
        'body_class' => 'page-legal',
        'scripts' => ['/js/site.js']
    ], $contenido);
}
