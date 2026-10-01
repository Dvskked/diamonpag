<?php
/* ============================================================================
 * The Diamonds League · capa de datos
 * neptun / andres / Dvskked — github.com/Dvskked
 * Conserva este aviso de autoría.
 *
 * Todas las consultas usan sentencias preparadas de PDO. El nombre de tabla
 * y el de columna salen de las listas blancas de más abajo, nunca de lo que
 * envíe el visitante: eso es lo que evita la inyección SQL.
 * ========================================================================== */

require_once __DIR__ . '/../conexion.php';
require_once __DIR__ . '/helpers.php';

/* -------------------------------------------------------------------------
 * Definición de colecciones. La misma tabla alimenta al panel y a la API.
 * ---------------------------------------------------------------------- */
function colecciones(): array
{
    return [
        'matches' => [
            'tabla' => 'partidos',
            'prefijo' => 'match',
            'etiqueta' => 'Partidos',
            'orden' => 'division, journey, home',
            'campos' => [
                'division'     => ['d1', 'd2'],
                'stage'        => ['liga', 'playoffs'],
    'journey'      => 'entero_null',
    'journeyLabel' => 'texto:60',
                'range'        => 'texto:40',
                'date'         => 'fecha',
                'time'         => 'hora',
                'home'         => 'texto:80',
                'away'         => 'texto:80',
                'homeGoals'    => 'entero',
                'awayGoals'    => 'entero',
                'status'       => ['programado', 'en-vivo', 'finalizado', 'wo', 'pospuesto', 'por-definir'],
                'replay'       => 'texto:400',
                'notes'        => 'texto:400'
            ],
            'requeridos' => ['home', 'away']
        ],
        'teams' => [
            'tabla' => 'equipos',
            'prefijo' => 'team',
            'etiqueta' => 'Equipos',
            'orden' => 'division, sort_order, name',
            'campos' => [
                'name'     => 'texto:60',
                'division' => ['d1', 'd2'],
                'coach'    => 'texto:80',
                'colors'   => 'texto:80',
                'note'     => 'texto:200'
            ],
            'requeridos' => ['name']
        ],
        'news' => [
            'tabla' => 'noticias',
            'prefijo' => 'news',
            'etiqueta' => 'Noticias',
            'orden' => 'date DESC, id',
            'campos' => [
                'title'    => 'texto:160',
                'category' => 'texto:60',
                'excerpt'  => 'texto:400',
                'body'     => 'texto:4000',
                'date'     => 'fecha',
                'author'   => 'texto:80',
                'image'    => 'ruta:300',
                'pinned'   => 'bool'
            ],
            'requeridos' => ['title']
        ],
        'announcements' => [
            'tabla' => 'anuncios',
            'prefijo' => 'ann',
            'etiqueta' => 'Anuncios',
            'orden' => 'date DESC, id',
            'campos' => [
                'title'   => 'texto:160',
                'kicker'  => 'texto:120',
                'season'  => 'texto:60',
                'kind'    => ['awards', 'registration', 'general'],
                'date'    => 'fecha',
                'day'     => 'entero',
                'month'   => 'entero',
                'year'    => 'entero',
                'text'    => 'texto:2000',
                'bullets' => 'lista',
                'closing' => 'texto:800',
                'warning' => 'texto:400'
            ],
            'requeridos' => ['title']
        ],
        'awards' => [
            'tabla' => 'premios',
            'prefijo' => 'award',
            'etiqueta' => 'Museo de premios',
            'orden' => 'division, category, id',
            'campos' => [
                'title'    => 'texto:160',
                'team'     => 'texto:80',
                'text'     => 'texto:300',
                'season'   => 'texto:60',
                'division' => ['d1', 'd2', 'ambas'],
                'category' => ['premios', 'rankings', 'campeones'],
                'image'    => 'ruta:300',
                'year'     => 'entero'
            ],
            'requeridos' => ['title']
        ],
        'pubs' => [
            'tabla' => 'salas',
            'prefijo' => 'room',
            'etiqueta' => 'Salas públicas',
            'orden' => 'id',
            'campos' => [
                'label'   => 'texto:120',
                'name'    => 'texto:80',
                'url'     => 'url:400',
                'status'  => ['ABIERTA', 'CERRADA', 'MANTENIMIENTO'],
                'players' => 'entero_null',
                'note'    => 'texto:200'
            ],
            'requeridos' => ['url']
        ],
        'important' => [
            'tabla' => 'destacados',
            'prefijo' => 'imp',
            'etiqueta' => 'Accesos de la liga',
            'orden' => 'sort_order, id',
            'campos' => [
                'title'       => 'texto:120',
                'description' => 'texto:240',
                'kind'        => ['link', 'external', 'status'],
                'href'        => 'enlace:400',
                'cta'         => 'texto:40',
                'sort_order'  => 'entero'
            ],
            'requeridos' => ['title']
        ],
        'staff' => [
            'tabla' => 'personal',
            'prefijo' => 'staff',
            'etiqueta' => 'Equipo de administración',
            'orden' => 'id',
            'campos' => [
                'name'      => 'texto:80',
                'username'  => 'texto:80',
                'role'      => ['Owner', 'DESARROLLADOR', 'Master', 'Moderador', 'Staff'],
                'bio'       => 'texto:400',
                'avatar'    => 'ruta:300',
                'banner'    => 'ruta:300',
                'focus'     => 'texto:120',
                'github'    => 'texto:80',
                'instagram' => 'texto:80',
                'discord'   => 'texto:80',
                'available' => 'bool',
                'tags'      => 'lista'
            ],
            'requeridos' => ['name']
        ],
        'alliances' => [
            'tabla' => 'alianzas',
            'prefijo' => 'al',
            'etiqueta' => 'Alianzas y afiliaciones',
            'orden' => 'sort_order, id',
            'campos' => [
                'name'        => 'texto:120',
                'kind'        => ['afiliacion', 'partner', 'proxima', 'servidor'],
                'description' => 'texto:400',
                'href'        => 'url:400',
                'cta'         => 'texto:60',
                'image'       => 'ruta:300',
                'status'      => ['activa', 'proxima', 'inactiva'],
                'sort_order'  => 'entero'
            ],
            'requeridos' => ['name']
        ],
        'social' => [
            'tabla' => 'redes',
            'prefijo' => 'rd',
            'etiqueta' => 'Redes sociales',
            'orden' => 'sort_order, id',
            'campos' => [
                'network'     => ['instagram', 'tiktok', 'twitch', 'youtube', 'discord', 'x', 'facebook', 'otro'],
                'owner_name'  => 'texto:120',
                'handle'      => 'texto:120',
                'url'         => 'url:400',
                'followers'   => 'entero',
                'is_streamer' => 'bool',
                'sort_order'  => 'entero'
            ],
            'requeridos' => ['network']
        ],
        'live' => [
            'tabla' => 'directos',
            'prefijo' => 'live',
            'etiqueta' => 'Directos de fútbol',
            'orden' => 'is_live DESC, starts_at, sort_order',
            'campos' => [
                'league'       => 'texto:120',
                'home'         => 'texto:120',
                'away'         => 'texto:120',
                'home_score'   => 'texto:10',
                'away_score'   => 'texto:10',
                'channel'      => 'texto:40',
                'platform'     => ['twitch', 'youtube', 'kick', 'otro'],
                'url'          => 'url:400',
                'viewer_count' => 'entero',
                'starts_at'    => 'datetime',
                'is_live'      => 'bool',
                'sort_order'   => 'entero'
            ],
            'requeridos' => ['url']
        ],
        'donations' => [
            'tabla' => 'donaciones',
            'prefijo' => 'dn',
            'etiqueta' => 'Donaciones',
            'orden' => 'sort_order, id',
            'campos' => [
                'title'       => 'texto:120',
                'description' => 'texto:400',
                'kind'        => ['info', 'meta', 'metodo'],
                'amount'      => 'decimal',
                'method'      => 'texto:60',
                'account'     => 'texto:120',
                'goal'        => 'decimal',
                'raised'      => 'decimal',
                'is_active'   => 'bool',
                'sort_order'  => 'entero'
            ],
            'requeridos' => ['title']
        ]
    ];
}

/** Devuelve la colección solicitada o null si no existe. */
function coleccion(string $nombre): ?array
{
    $todas = colecciones();
    return $todas[$nombre] ?? null;
}

/* -------------------------------------------------------------------------
 * Saneado de campos
 * ---------------------------------------------------------------------- */

/** Limpia un valor según el tipo declarado en la colección. */
function sanear(mixed $valor, array $reglas): mixed
{
    if (is_array($reglas)) {
        $texto = str_corta($valor, 120);
        return in_array($texto, $reglas, true) ? $texto : $reglas[0];
    }
    [$tipo, $max] = array_pad(explode(':', (string) $reglas, 2), 2, '400');

    return match ($tipo) {
        'entero' => a_entero($valor) ?? 0,
        'entero_null' => a_entero($valor),
        'decimal' => a_decimal($valor) ?? 0.0,
        'bool'   => a_bool($valor) ? 1 : 0,
        'fecha'  => fecha_valida($valor),
        'hora'   => hora_valida($valor),
        'datetime' => sanitize_datetime($valor),
        'url'    => url_segura($valor),
        'ruta'   => ruta_segura($valor, (int) $max),
        'enlace' => enlace_seguro($valor, (int) $max),
        'lista'  => sanear_lista($valor, (int) $max),
        default  => str_corta($valor, (int) $max)
    };
}

/** URLs externas seguras o anclas internas de la página (#seccion). */
function enlace_seguro(mixed $valor, int $max = 300): string
{
    $valor = str_corta($valor, $max);
    if ($valor === '') {
        return '';
    }
    if (str_starts_with($valor, '#')) {
        return preg_match('/^#[a-z0-9\-]{1,60}$/i', $valor) ? $valor : '';
    }
    if (str_starts_with($valor, '/') && !str_starts_with($valor, '//')) {
        return preg_match('#^/[a-z0-9\-/_.]{0,200}$#i', $valor) ? $valor : '';
    }
    return url_segura($valor);
}

/** Normaliza DATETIME a YYYY-MM-DD HH:MM:SS o cadena vacía. */
function sanitize_datetime(mixed $valor): string
{
    $valor = trim((string) ($valor ?? ''));
    if ($valor === '') {
        return '';
    }
    $valor = str_replace('T', ' ', $valor);
    if (preg_match('/^\d{4}-\d{2}-\d{2}$/', $valor)) {
        $valor .= ' 00:00:00';
    }
    if (preg_match('/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}(:\d{2})?$/', $valor)) {
        $ts = strtotime($valor);
        return $ts === false ? '' : date('Y-m-d H:i:s', $ts);
    }
    return '';
}

/** Solo rutas internas que sirvan un archivo del proyecto. */
function ruta_segura(mixed $valor, int $max = 300): string
{
    $valor = str_corta($valor, $max);
    if ($valor === '') {
        return '';
    }
    if (url_segura($valor) !== '') {
        return $valor;
    }
    if (str_starts_with($valor, '/assets/')) {
        return $valor;
    }
    return '';
}

/** Limpia una lista de textos cortos (etiquetas, puntos). */
function sanear_lista(mixed $valor, int $max = 400): string
{
    if (is_string($valor)) {
        $texto = trim($valor);
        if ($texto === '') {
            return '';
        }
        $pos = strpos($texto, '[');
        if ($pos !== false) {
            $texto = substr($texto, $pos);
        }
        $lista = json_decode($texto, true);
    } else {
        $lista = $valor;
    }
    if (!is_array($lista)) {
        return '';
    }
    $limpia = [];
    foreach ($lista as $item) {
        if (is_array($item)) {
            $item = $item['title'] ?? '';
        }
        $item = str_corta($item, 60);
        if ($item !== '') {
            $limpia[] = $item;
        }
        if (count($limpia) >= 12) {
            break;
        }
    }
    return json_encode($limpia, JSON_UNESCAPED_UNICODE);
}

/**
 * Limpia una lista de objetos con un esquema fijo (label/value, fases, etc.).
 * Conserva solo las claves indicadas y devuelve JSON.
 */
function sanear_objetos(mixed $valor, array $esquema, int $max = 12): string
{
    $lista = sanear_lista_json($valor);
    $limpia = [];
    foreach ($lista as $item) {
        if (!is_array($item)) {
            continue;
        }
        $fila = [];
        foreach ($esquema as $clave => $maximo) {
            $fila[$clave] = str_corta($item[$clave] ?? '', $maximo);
        }
        $limpia[] = $fila;
        if (count($limpia) >= $max) {
            break;
        }
    }
    return json_encode($limpia, JSON_UNESCAPED_UNICODE);
}

/** Decodifica un valor que puede venir como array o como texto JSON. */
function sanear_lista_json(mixed $valor): array
{
    if (is_array($valor)) {
        return $valor;
    }
    $texto = trim((string) ($valor ?? ''));
    if ($texto === '') {
        return [];
    }
    $pos = strpos($texto, '[');
    if ($pos !== false) {
        $texto = substr($texto, $pos);
    }
    $lista = json_decode($texto, true);
    return is_array($lista) ? $lista : [];
}

/**
 * Guarda el bloque de movimiento (ascensos/descensos) de una división.
 * Es un objeto {title, items:[{place,label,text}]}.
 */
function sanear_movimiento(mixed $valor): string
{
    $entrada = sanear_lista_json($valor);
    if (isset($entrada['items']) || isset($entrada['title'])) {
        $objeto = [
            'title' => str_corta($entrada['title'] ?? '', 120),
            'items' => sanear_lista_json($entrada['items'] ?? [])
        ];
    } else {
        $objeto = ['title' => '', 'items' => $entrada];
    }
    $items = [];
    foreach ($objeto['items'] as $item) {
        if (!is_array($item)) {
            continue;
        }
        $items[] = [
            'place' => str_corta($item['place'] ?? '', 60),
            'label' => str_corta($item['label'] ?? '', 120),
            'text' => str_corta($item['text'] ?? '', 400)
        ];
        if (count($items) >= 12) {
            break;
        }
    }
    return json_encode(['title' => $objeto['title'], 'items' => $items], JSON_UNESCAPED_UNICODE);
}

/** Convierte un campo de la colección en columna SQL, con su saneado. */
function sanear_campo(string $campo, mixed $valor, array $def): ?array
{
    if (!array_key_exists($campo, $def['campos'])) {
        return null;
    }
    $columna = bd_columna($campo);
    if ($columna === null) {
        return null;
    }
    $valor = sanear($valor, $def['campos'][$campo]);
    if (in_array($columna, ['tags', 'bullets'], true)) {
        return [$columna, is_string($valor) ? $valor : json_encode($valor, JSON_UNESCAPED_UNICODE)];
    }
    return [$columna, $valor];
}

/** Comprueba los campos obligatorios y devuelve la lista de errores. */
function validar_registro(array $registro, array $def): array
{
    $errores = [];
    foreach ($def['requeridos'] as $campo) {
        $valor = $registro[$campo] ?? null;
        if ($valor === null || trim((string) $valor) === '') {
            $errores[] = 'El campo "' . $campo . '" es obligatorio.';
        }
    }
    return $errores;
}

/* -------------------------------------------------------------------------
 * Lectura
 * ---------------------------------------------------------------------- */

/** Ajustes de la liga (fila única). */
function leer_ajustes(): array
{
    $fila = bd_fila('SELECT * FROM `ajustes` WHERE `id` = 1') ?? [];
    $ajustes = [
        'leagueName' => $fila['league_name'] ?? 'The Diamonds League',
        'shortName' => $fila['short_name'] ?? 'TDL',
        'tagline' => $fila['tagline'] ?? '',
        'description' => $fila['description'] ?? '',
        'season' => $fila['season'] ?? '',
        'seasonNumber' => (int) ($fila['season_number'] ?? 1),
        'modality' => $fila['modality'] ?? '',
        'status' => $fila['status'] ?? '',
        'statusNote' => $fila['status_note'] ?? '',
        'server' => $fila['server'] ?? '',
        'map' => $fila['map'] ?? '',
        'matchDuration' => $fila['match_duration'] ?? '',
        'tolerance' => $fila['tolerance'] ?? '',
        'pointsWin' => (int) ($fila['points_win'] ?? 3),
        'pointsDraw' => (int) ($fila['points_draw'] ?? 1),
        'tiktok' => $fila['tiktok'] ?? '',
        'tiktokHandle' => $fila['tiktok_handle'] ?? '',
        'founded' => (int) ($fila['founded'] ?? 0) ?: null,
        'donationNote' => $fila['donation_note'] ?? '',
        'donationKey' => $fila['donation_key'] ?? '',
        'donationGoal' => (float) ($fila['donation_goal'] ?? 0)
    ];
    $ajustes['matchConfig'] = array_map(
        static fn(array $p): array => ['label' => (string) ($p['label'] ?? ''), 'value' => (string) ($p['value'] ?? '')],
        json_seguro($fila['match_config'] ?? '')
    );
    return $ajustes;
}

/** Divisiones ordenadas. */
function leer_divisiones(): array
{
    $filas = bd_todas('SELECT * FROM `divisiones` ORDER BY sort_order, name');
    return array_map(static function (array $f): array {
        return [
            'id' => $f['id'],
            'name' => $f['name'],
            'code' => $f['code'],
            'season' => $f['season'],
            'summary' => $f['summary'] ?? '',
            'teams' => (int) $f['teams'],
            'journeys' => (int) $f['journeys'],
            'playoffs' => $f['playoffs'],
            'relegation' => $f['relegation'],
            'promotion' => $f['promotion'],
            'phases' => json_seguro($f['phases'] ?? ''),
            'movement' => json_seguro($f['movement'] ?? ''),
            'rules' => json_seguro($f['rules'] ?? '')
        ];
    }, $filas);
}

/** Filas de una tabla con el mapeo a los nombres que usa el panel. */
function leer_coleccion(string $nombre): array
{
    $def = coleccion($nombre);
    if ($def === null) {
        return [];
    }
    $filas = bd_todas('SELECT * FROM `' . $def['tabla'] . '` ORDER BY ' . $def['orden']);
    return array_map(
        static fn(array $f): array => fila_a_json($f, $nombre),
        $filas
    );
}

/** Traduce una fila de la tabla al formato JSON del panel. */
function fila_a_json(array $fila, string $coleccion): array
{
    $def = coleccion($coleccion);
    $json = [];
    foreach (array_keys($def['campos'] ?? []) as $campo) {
        $columna = bd_columna($campo);
        if ($columna === null || !array_key_exists($columna, $fila)) {
            continue;
        }
        $valor = $fila[$columna];
        if (in_array($columna, ['tags', 'bullets'], true)) {
            $json[$campo] = json_seguro((string) $valor);
            continue;
        }
        $json[$campo] = $valor;
    }
    $json['id'] = $fila['id'] ?? '';
    return $json;
}

/** Reglamento con sus puntos, bloques y tarjetas. */
function leer_reglas(): array
{
    $reglas = bd_todas('SELECT * FROM `reglas` ORDER BY sort_order, id');
    $puntos = bd_todas('SELECT * FROM `regla_items` ORDER BY rule_id, sort_order, id');
    $porRegla = [];
    foreach ($puntos as $p) {
        $porRegla[$p['rule_id']][] = $p;
    }
    $salida = [];
    foreach ($reglas as $regla) {
        $items = [];
        $bloques = [];
        $tarjetas = [];
        foreach ($porRegla[$regla['id']] ?? [] as $p) {
            $lista = json_seguro($p['list'] ?? '');
            $texto = (string) ($p['text'] ?? '');
            $titulo = (string) ($p['title'] ?? '');
            if ($p['kind'] === 'bloque') {
                $bloques[] = array_filter([
                    'title' => $titulo,
                    'subtitle' => (string) ($p['subtitle'] ?? ''),
                    'text' => $texto,
                    'list' => $lista
                ], static fn($v) => $v !== '' && $v !== []);
            } elseif ($p['kind'] === 'tarjeta') {
                $tarjetas[] = array_filter([
                    'title' => $titulo,
                    'kicker' => (string) ($p['kicker'] ?? ''),
                    'tone' => (string) ($p['tone'] ?? 'info'),
                    'list' => $lista,
                    'text' => $texto
                ], static fn($v) => $v !== '' && $v !== []);
            } else {
                $items[] = array_filter([
                    'title' => $titulo,
                    'text' => $texto
                ], static fn($v) => $v !== '');
            }
        }
        $salida[] = array_filter([
            'id' => $regla['id'],
            'title' => $regla['title'],
            'summary' => $regla['summary'],
            'items' => $items,
            'blocks' => $bloques,
            'cards' => $tarjetas
        ], static fn($v) => $v !== '' && $v !== []);
    }
    return $salida;
}

/** Estructura completa que consumen el panel y las vistas. */
function cargar_datos(): array
{
    return [
        'version' => 3,
        'updatedAt' => date('c'),
        'settings' => leer_ajustes(),
        'divisions' => leer_divisiones(),
        'matchConfig' => leer_ajustes()['matchConfig'],
        'teams' => leer_coleccion('teams'),
        'matches' => leer_coleccion('matches'),
        'rules' => leer_reglas(),
        'pubs' => leer_coleccion('pubs'),
        'news' => leer_coleccion('news'),
        'announcements' => leer_coleccion('announcements'),
        'awards' => leer_coleccion('awards'),
        'important' => leer_coleccion('important'),
        'staff' => leer_coleccion('staff'),
        'alliances' => leer_coleccion('alliances'),
        'social' => leer_coleccion('social'),
        'live' => leer_coleccion('live'),
        'donations' => leer_coleccion('donations')
    ];
}

/* -------------------------------------------------------------------------
 * Escritura
 * ---------------------------------------------------------------------- */

/** Crea un registro y devuelve la fila guardada. */
function crear_registro(string $nombre, array $entrada): array
{
    $def = coleccion($nombre);
    if ($def === null) {
        throw new RuntimeException('Colección desconocida.');
    }
    $registro = [];
    foreach ($entrada as $campo => $valor) {
        $saneado = sanear_campo((string) $campo, $valor, $def);
        if ($saneado !== null) {
            $registro[$saneado[0]] = $saneado[1];
        }
    }
    $errores = validar_registro(entrada_a_campos($registro, $def), $def);
    if ($errores) {
        throw new RuntimeException(implode(' ', $errores));
    }
    $registro['id'] = nuevo_id($def['prefijo']);
    $columnas = array_keys($registro);
    $sql = 'INSERT INTO `' . $def['tabla'] . '` (`' . implode('`, `', $columnas) . '`) VALUES ('
        . implode(', ', array_fill(0, count($columnas), '?')) . ')';
    bd_ejecutar($sql, array_values($registro));
    return fila_a_json(bd_fila('SELECT * FROM `' . $def['tabla'] . '` WHERE `id` = ?', [$registro['id']]) ?? [], $nombre);
}

/** Actualiza un registro existente (solo campos permitidos). */
function actualizar_registro(string $nombre, string $id, array $entrada): array
{
    $def = coleccion($nombre);
    if ($def === null || !id_valido($id)) {
        throw new RuntimeException('Registro no válido.');
    }
    $actual = bd_fila('SELECT * FROM `' . $def['tabla'] . '` WHERE `id` = ?', [$id]);
    if ($actual === null) {
        throw new RuntimeException('El registro no existe.');
    }
    $cambios = [];
    foreach ($entrada as $campo => $valor) {
        $saneado = sanear_campo((string) $campo, $valor, $def);
        if ($saneado !== null) {
            $cambios[$saneado[0]] = $saneado[1];
        }
    }
    unset($cambios['id']);
    if ($cambios) {
        $sets = [];
        foreach (array_keys($cambios) as $columna) {
            $sets[] = '`' . $columna . '` = ?';
        }
        bd_ejecutar(
            'UPDATE `' . $def['tabla'] . '` SET ' . implode(', ', $sets) . ' WHERE `id` = ?',
            array_merge(array_values($cambios), [$id])
        );
    }
    $final = bd_fila('SELECT * FROM `' . $def['tabla'] . '` WHERE `id` = ?', [$id]) ?? [];
    $errores = validar_registro(fila_a_json($final, $nombre), $def);
    if ($errores) {
        throw new RuntimeException(implode(' ', $errores));
    }
    return fila_a_json($final, $nombre);
}

/** Borra un registro. */
function borrar_registro(string $nombre, string $id): bool
{
    $def = coleccion($nombre);
    if ($def === null || !id_valido($id)) {
        return false;
    }
    $stmt = bd_ejecutar('DELETE FROM `' . $def['tabla'] . '` WHERE `id` = ?', [$id]);
    return $stmt->rowCount() > 0;
}

/** Convierte columnas saneadas a nombres de campo para validar. */
function entrada_a_campos(array $columnas, array $def): array
{
    $salida = [];
    foreach (array_keys($def['campos']) as $campo) {
        $columna = bd_columna($campo);
        if ($columna !== null && array_key_exists($columna, $columnas)) {
            $salida[$campo] = $columnas[$columna];
        }
    }
    return $salida;
}

/**
 * Restaura el contenido de referencia (sql/datos.sql) sin tocar las cuentas
 * de usuario. Solo funciona si el archivo está disponible en el servidor.
 */
function reiniciar_datos(): array
{
    $archivo = APP_RAIZ . DIRECTORY_SEPARATOR . 'sql' . DIRECTORY_SEPARATOR . 'datos.sql';
    if (!is_file($archivo) || !is_readable($archivo)) {
        return ['ok' => false, 'error' => 'No se encontró sql/datos.sql en el servidor.'];
    }
    $sql = (string) file_get_contents($archivo);
    if (trim($sql) === '') {
        return ['ok' => false, 'error' => 'sql/datos.sql está vacío.'];
    }

    $tablas = [
        'anuncios', 'noticias', 'premios', 'destacados', 'alianzas', 'redes', 'directos',
        'donaciones', 'salas', 'personal', 'regla_items', 'reglas', 'partidos', 'equipos',
        'divisiones', 'ajustes'
    ];
    bd()->beginTransaction();
    try {
        bd_ejecutar('SET FOREIGN_KEY_CHECKS = 0');
        foreach ($tablas as $tabla) {
            bd_ejecutar('TRUNCATE TABLE `' . $tabla . '`');
        }
        bd_ejecutar('SET FOREIGN_KEY_CHECKS = 1');

        $sentencias = preg_split('/;\s*\R/', $sql) ?: [];
        $ejecutadas = 0;
        foreach ($sentencias as $sentencia) {
            $sentencia = trim(preg_replace('/^\s*--.*$/m', '', $sentencia) ?? '');
            if ($sentencia === '' || !preg_match('/^(INSERT|REPLACE|UPDATE)\b/i', $sentencia)) {
                continue;
            }
            bd_ejecutar($sentencia);
            $ejecutadas++;
        }
        bd()->commit();
    } catch (Throwable $error) {
        bd()->rollBack();
        if (APP_DEBUG) {
            throw $error;
        }
        return ['ok' => false, 'error' => 'Falló la restauración: ' . $error->getMessage()];
    }
    return ['ok' => true, 'sentencias' => $ejecutadas];
}

/** Guarda los ajustes generales. */
function guardar_ajustes(array $entrada): array
{
    $mapa = [
        'leagueName' => 'league_name', 'shortName' => 'short_name', 'tagline' => 'tagline',
        'description' => 'description', 'season' => 'season', 'seasonNumber' => 'season_number',
        'modality' => 'modality', 'status' => 'status', 'statusNote' => 'status_note',
        'server' => 'server', 'map' => 'map', 'matchDuration' => 'match_duration',
        'tolerance' => 'tolerance', 'pointsWin' => 'points_win', 'pointsDraw' => 'points_draw',
        'tiktok' => 'tiktok', 'tiktokHandle' => 'tiktok_handle', 'founded' => 'founded',
        'matchConfig' => 'match_config', 'donationNote' => 'donation_note',
        'donationKey' => 'donation_key', 'donationGoal' => 'donation_goal'
    ];
    $sets = [];
    $params = [];
    foreach ($mapa as $campo => $columna) {
        if (!array_key_exists($campo, $entrada)) {
            continue;
        }
        $valor = $entrada[$campo];
        if ($campo === 'matchConfig') {
            $valor = sanear_objetos($valor, ['label' => 60, 'value' => 120]);
        } elseif (in_array($campo, ['tiktok'], true)) {
            $valor = url_segura($valor);
        } elseif (in_array($campo, ['donationKey'], true)) {
            $valor = str_corta($valor, 120);
        } elseif (in_array($campo, ['pointsWin', 'pointsDraw', 'seasonNumber'], true)) {
            $valor = max(0, (int) $valor);
        } elseif ($campo === 'founded') {
            $valor = (int) $valor ?: 0;
        } elseif ($campo === 'donationGoal') {
            $valor = max(0.0, (float) $valor);
        } else {
            $valor = str_corta($valor, 800);
        }
        $sets[] = '`' . $columna . '` = ?';
        $params[] = $valor;
    }
    if ($sets) {
        bd_ejecutar('UPDATE `ajustes` SET ' . implode(', ', $sets) . ' WHERE `id` = 1', $params);
    }
    return leer_ajustes();
}

/** Guarda el reglamento completo (bloques de borrador del panel). */
function guardar_reglas(array $entrada): array
{
    bd()->beginTransaction();
    try {
        foreach ($entrada as $regla) {
            $id = str_corta($regla['id'] ?? '', 40);
            if ($id === '') {
                continue;
            }
            bd_ejecutar(
                'INSERT INTO `reglas` (`id`,`title`,`summary`,`sort_order`) VALUES (?,?,?,?)'
                . ' ON DUPLICATE KEY UPDATE `title` = VALUES(`title`), `summary` = VALUES(`summary`), `sort_order` = VALUES(`sort_order`)',
                [$id, str_corta($regla['title'] ?? '', 120), str_corta($regla['summary'] ?? '', 255), (int) ($regla['sort_order'] ?? 0)]
            );
            bd_ejecutar('DELETE FROM `regla_items` WHERE `rule_id` = ?', [$id]);
            $orden = 0;
            foreach (['items', 'blocks', 'cards'] as $grupo) {
                foreach ((array) ($regla[$grupo] ?? []) as $item) {
                    $lista = $item['list'] ?? [];
                    bd_ejecutar(
                        'INSERT INTO `regla_items` (`rule_id`,`kind`,`title`,`subtitle`,`kicker`,`tone`,`text`,`list`,`sort_order`)'
                        . ' VALUES (?,?,?,?,?,?,?,?,?)',
                        [
                            $id,
                            $grupo === 'items' ? 'item' : ($grupo === 'blocks' ? 'bloque' : 'tarjeta'),
                            str_corta($item['title'] ?? '', 160),
                            str_corta($item['subtitle'] ?? '', 160),
                            str_corta($item['kicker'] ?? '', 60),
                            str_corta($item['tone'] ?? 'info', 20),
                            str_corta($item['text'] ?? '', 800),
                            json_encode(sanear_lista($lista), JSON_UNESCAPED_UNICODE),
                            $orden++
                        ]
                    );
                }
            }
        }
        bd()->commit();
    } catch (Throwable $e) {
        bd()->rollBack();
        throw $e;
    }
    return leer_reglas();
}

/** Guarda las divisiones completas. */
function guardar_divisiones(array $entrada): array
{
    bd()->beginTransaction();
    try {
        $orden = 0;
        foreach ($entrada as $division) {
            $id = str_corta($division['id'] ?? '', 24);
            if ($id === '') {
                continue;
            }
            bd_ejecutar(
                'INSERT INTO `divisiones` (`id`,`name`,`code`,`season`,`summary`,`teams`,`journeys`,`playoffs`,'
                . '`relegation`,`promotion`,`phases`,`movement`,`rules`,`sort_order`)'
                . ' VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)'
                . ' ON DUPLICATE KEY UPDATE `name` = VALUES(`name`), `code` = VALUES(`code`), `season` = VALUES(`season`),'
                . ' `summary` = VALUES(`summary`), `teams` = VALUES(`teams`), `journeys` = VALUES(`journeys`),'
                . ' `playoffs` = VALUES(`playoffs`), `relegation` = VALUES(`relegation`), `promotion` = VALUES(`promotion`),'
                . ' `phases` = VALUES(`phases`), `movement` = VALUES(`movement`), `rules` = VALUES(`rules`),'
                . ' `sort_order` = VALUES(`sort_order`)',
                [
                    $id,
                    str_corta($division['name'] ?? $id, 80),
                    str_corta($division['code'] ?? strtoupper($id), 24),
                    str_corta($division['season'] ?? '', 60),
                    str_corta($division['summary'] ?? '', 800),
                    max(0, (int) ($division['teams'] ?? 0)),
                    max(0, (int) ($division['journeys'] ?? 0)),
                    str_corta($division['playoffs'] ?? '', 200),
                    str_corta($division['relegation'] ?? '', 200),
                    str_corta($division['promotion'] ?? '', 200),
                    sanear_objetos($division['phases'] ?? [], ['label' => 60, 'title' => 160, 'text' => 800, 'note' => 400]),
                    sanear_movimiento($division['movement'] ?? []),
                    sanear_objetos($division['rules'] ?? [], ['title' => 160, 'text' => 800]),
                    $orden++
                ]
            );
        }
        bd()->commit();
    } catch (Throwable $e) {
        bd()->rollBack();
        throw $e;
    }
    return leer_divisiones();
}

/* -------------------------------------------------------------------------
 * Clasificaciones
 * ---------------------------------------------------------------------- */

/**
 * Tabla de posiciones de una división a partir de los partidos finalizados.
 */
function calcular_clasificacion(array $equipos, array $partidos, string $divisionId, array $ajustes): array
{
    $victoria = (int) ($ajustes['pointsWin'] ?? 3);
    $empate = (int) ($ajustes['pointsDraw'] ?? 1);
    $filas = [];

    $asegurar = static function (string $nombre) use (&$filas): ?array {
        $clave = mb_strtoupper(trim($nombre));
        if ($clave === '') {
            return null;
        }
        if (!isset($filas[$clave])) {
            $filas[$clave] = [
                'key' => $clave,
                'name' => trim($nombre),
                'played' => 0, 'won' => 0, 'drawn' => 0, 'lost' => 0,
                'goalsFor' => 0, 'goalsAgainst' => 0, 'points' => 0
            ];
        }
        return [$clave];
    };

    foreach ($equipos as $equipo) {
        if (($equipo['division'] ?? '') === $divisionId) {
            $asegurar((string) $equipo['name']);
        }
    }

    foreach ($partidos as $partido) {
        if (($partido['division'] ?? '') !== $divisionId || ($partido['status'] ?? '') !== 'finalizado') {
            continue;
        }
        $local = $asegurar((string) ($partido['home'] ?? ''));
        $visitante = $asegurar((string) ($partido['away'] ?? ''));
        if ($local === null || $visitante === null || $local[0] === $visitante[0]) {
            continue;
        }
        $gl = (int) ($partido['homeGoals'] ?? 0);
        $gv = (int) ($partido['awayGoals'] ?? 0);

        $filas[$local[0]]['played']++;
        $filas[$visitante[0]]['played']++;
        $filas[$local[0]]['goalsFor'] += $gl;
        $filas[$local[0]]['goalsAgainst'] += $gv;
        $filas[$visitante[0]]['goalsFor'] += $gv;
        $filas[$visitante[0]]['goalsAgainst'] += $gl;

        if ($gl > $gv) {
            $filas[$local[0]]['won']++;
            $filas[$local[0]]['points'] += $victoria;
            $filas[$visitante[0]]['lost']++;
        } elseif ($gl < $gv) {
            $filas[$visitante[0]]['won']++;
            $filas[$visitante[0]]['points'] += $victoria;
            $filas[$local[0]]['lost']++;
        } else {
            $filas[$local[0]]['drawn']++;
            $filas[$visitante[0]]['drawn']++;
            $filas[$local[0]]['points'] += $empate;
            $filas[$visitante[0]]['points'] += $empate;
        }
    }

    $tabla = array_values($filas);
    foreach ($tabla as &$fila) {
        $fila['goalDiff'] = $fila['goalsFor'] - $fila['goalsAgainst'];
    }
    unset($fila);

    usort($tabla, static function (array $a, array $b): int {
        return $b['points'] <=> $a['points']
            ?: $b['goalDiff'] <=> $a['goalDiff']
            ?: $b['goalsFor'] <=> $a['goalsFor']
            ?: strcmp($a['name'], $b['name']);
    });

    foreach ($tabla as $i => $fila) {
        $tabla[$i]['position'] = $i + 1;
    }
    return $tabla;
}

/** Próximo partido programado. */
function proximo_partido(array $partidos, array $divisiones): ?array
{
    $ahora = time();
    $candidatos = [];
    foreach ($partidos as $partido) {
        if (($partido['status'] ?? '') !== 'programado' || empty($partido['date'])) {
            continue;
        }
        $ts = strtotime($partido['date'] . ' ' . ((string) ($partido['time'] ?? '')) ?: '00:00');
        if ($ts === false || $ts < $ahora - 3 * 3600) {
            continue;
        }
        $partido['stamp'] = $ts;
        $candidatos[] = $partido;
    }
    if (!$candidatos) {
        return null;
    }
    usort($candidatos, static fn(array $a, array $b): int => $a['stamp'] <=> $b['stamp']);
    $partido = $candidatos[0];
    foreach ($divisiones as $division) {
        if ($division['id'] === $partido['division']) {
            $partido['divisionName'] = $division['name'];
            break;
        }
    }
    $partido['divisionName'] ??= '';
    return $partido;
}

/** Clasificaciones de todas las divisiones. */
function clasificaciones(array $datos): array
{
    $salida = [];
    foreach ($datos['divisions'] as $division) {
        $salida[$division['id']] = calcular_clasificacion(
            $datos['teams'],
            $datos['matches'],
            $division['id'],
            $datos['settings']
        );
    }
    return $salida;
}
