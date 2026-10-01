<?php
/* ============================================================================
 * The Diamonds League · API del panel de administración
 * neptun / andres / Dvskked — github.com/Dvskked
 *
 * Contrato que consume /js/admin.js:
 *   GET    /api/admin/session
 *   POST   /api/admin/login | /api/admin/logout | /api/admin/reset
 *   GET    /api/admin/data | /api/admin/standings
 *   POST   /api/admin/{coleccion}
 *   PUT    /api/admin/{coleccion}/{id}
 *   DELETE /api/admin/{coleccion}/{id}
 *   PUT    /api/admin/settings | /match-config | /rules | /divisions
 * ========================================================================== */

$rutaApi = substr($ruta, strlen('/api/admin'));
$segmentos = array_values(array_filter(explode('/', $rutaApi), static fn(string $s): bool => $s !== ''));
$accion = $segmentos[0] ?? '';
$idApi = isset($segmentos[1]) ? rawurldecode($segmentos[1]) : '';

/** Colecciones que el panel puede editar. */
$coleccionesApi = [
    'matches' => 'matches',
    'teams' => 'teams',
    'news' => 'news',
    'announcements' => 'announcements',
    'awards' => 'awards',
    'pubs' => 'pubs',
    'important' => 'important',
    'staff' => 'staff',
    'alliances' => 'alliances',
    'social' => 'social',
    'live' => 'live',
    'donations' => 'donations'
];

/** ¿El método actual modifica datos y por lo tanto exige token CSRF? */
$esMutacion = in_array($metodo, ['POST', 'PUT', 'PATCH', 'DELETE'], true);

try {
    /* --- Sesión: cualquiera puede consultarla --- */
    if ($accion === 'session' && $metodo === 'GET') {
        salir_json([
            'ok' => true,
            'admin' => admin_logueado(),
            'usuario' => usuario_actual()
        ]);
    }

    /* --- Entrar y salir --- */
    if ($accion === 'login' && $metodo === 'POST') {
        $entrada = cuerpo_json();
        $usuario = trim((string) ($entrada['usuario'] ?? ''));
        $clave = (string) ($entrada['password'] ?? '');
        if (!intentos_permitidos('admin', $usuario)) {
            salir_json(['ok' => false, 'error' => 'Demasiados intentos fallidos.'], 429);
        }
        $ok = admin_entrar($usuario, $clave);
        registrar_intento('admin', $usuario, $ok);
        if (!$ok) {
            salir_json(['ok' => false, 'error' => 'Usuario o contraseña incorrectos.'], 401);
        }
        salir_json(['ok' => true]);
    }

    if ($accion === 'logout' && $metodo === 'POST') {
        admin_exigir();
        csrf_exigir();
        admin_cerrar();
        salir_json(['ok' => true]);
    }

    /* --- A partir de aquí, sesión de administración obligatoria --- */
    admin_exigir();

    /* Toda escritura pasa por el token anti-CSRF. Los GET no lo requieren. */
    if ($esMutacion) {
        csrf_exigir();
    }

    if ($accion === 'data' && $metodo === 'GET') {
        salir_json(array_merge(['ok' => true], cargar_datos()));
    }

    if ($accion === 'standings' && $metodo === 'GET') {
        $datos = cargar_datos();
        $tablas = clasificaciones($datos);
        $salida = ['ok' => true];
        foreach ($tablas as $idDivision => $filas) {
            $salida[$idDivision] = $filas;
        }
        salir_json($salida);
    }

    if ($accion === 'reset' && $metodo === 'POST') {
        $entrada = cuerpo_json();
        if (($entrada['confirm'] ?? '') !== 'RESTABLECER') {
            salir_json(['ok' => false, 'error' => 'Falta la confirmación RESTABLECER.'], 422);
        }
        $resultado = reiniciar_datos();
        if (!($resultado['ok'] ?? false)) {
            salir_json(['ok' => false, 'error' => (string) ($resultado['error'] ?? 'No se pudo restaurar.')], 500);
        }
        salir_json(['ok' => true, 'restaurado' => $resultado['sentencias'] ?? 0]);
    }

    if ($accion === 'settings' && $metodo === 'PUT') {
        $entrada = cuerpo_json();
        unset($entrada['id'], $entrada['matchConfig']);
        salir_json(['ok' => true, 'settings' => guardar_ajustes($entrada)]);
    }

    if ($accion === 'match-config' && $metodo === 'PUT') {
        $entrada = cuerpo_json();
        $lista = is_array($entrada) ? $entrada : ($entrada['config'] ?? []);
        salir_json(['ok' => true, 'settings' => guardar_ajustes(['matchConfig' => $lista])]);
    }

    if ($accion === 'rules' && $metodo === 'PUT') {
        $entrada = cuerpo_json();
        $lista = $entrada['rules'] ?? $entrada;
        if (!is_array($lista)) {
            salir_json(['ok' => false, 'error' => 'Formato de reglamento no válido.'], 422);
        }
        salir_json(['ok' => true, 'rules' => guardar_reglas($lista)]);
    }

    if ($accion === 'divisions' && $metodo === 'PUT') {
        $entrada = cuerpo_json();
        $lista = $entrada['divisions'] ?? $entrada;
        if (!is_array($lista)) {
            salir_json(['ok' => false, 'error' => 'Formato de divisiones no válido.'], 422);
        }
        salir_json(['ok' => true, 'divisions' => guardar_divisiones($lista)]);
    }

    /* --- CRUD de colecciones --- */
    if (isset($coleccionesApi[$accion])) {
        $nombre = $coleccionesApi[$accion];

        if ($metodo === 'GET') {
            salir_json(['ok' => true, 'items' => leer_coleccion($nombre)]);
        }
        if ($metodo === 'POST' && $idApi === '') {
            salir_json(['ok' => true, 'item' => crear_registro($nombre, cuerpo_json())], 201);
        }
        if ($metodo === 'PUT' && $idApi !== '') {
            salir_json(['ok' => true, 'item' => actualizar_registro($nombre, $idApi, cuerpo_json())]);
        }
        if ($metodo === 'DELETE' && $idApi !== '') {
            salir_json(['ok' => true, 'deleted' => borrar_registro($nombre, $idApi)]);
        }
    }
} catch (Throwable $error) {
    if (APP_DEBUG) {
        throw $error;
    }
    error_log('[tdl-api] ' . $error->getMessage() . ' @ ' . $error->getFile() . ':' . $error->getLine());
    responder_json(['ok' => false, 'error' => 'No se pudo completar la operación.'], 500);
}
