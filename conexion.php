<?php
/* ============================================================================
 * The Diamonds League · conexión a la base de datos
 * neptun / andres / Dvskked — github.com/Dvskked
 * Conserva este aviso de autoría.
 *
 * Usa PDO con excepciones y SIN emular prepares: todas las consultas del
 * proyecto van preparadas (bind), así que un valor de usuario nunca se
 * concatena en el SQL. Esa es la defensa real contra inyección SQL.
 *
 * Variables que lee: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD,
 * DB_CHARSET (ver .env.example).
 * ========================================================================== */

require_once __DIR__ . '/config.php';

/**
 * Devuelve la única instancia de PDO de la aplicación.
 */
function bd(): PDO
{
    static $pdo = null;
    if ($pdo instanceof PDO) {
        return $pdo;
    }

    $host = DB_HOST;
    $puerto = DB_PORT;
    $nombre = DB_NAME;
    $charset = DB_CHARSET;

    // Host que viene con el puerto dentro (p.ej. "mysql.uh.com:3306")
    if (str_contains($host, ':')) {
        [$host, $hostPort] = explode(':', $host, 2);
        if ($hostPort !== '') {
            $puerto = $hostPort;
        }
    }

    $dsn = "mysql:host={$host};port={$puerto};dbname={$nombre};charset={$charset}";

    try {
        $pdo = new PDO($dsn, DB_USER, DB_PASSWORD, [
            PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES   => false,
            PDO::ATTR_STRINGIFY_FETCHES  => false,
        ]);
        $pdo->exec("SET NAMES '{$charset}' COLLATE 'utf8mb4_unicode_ci'");
    } catch (PDOException $e) {
        error_log('The Diamonds League · error de conexión: ' . $e->getMessage());
        if (PHP_SAPI === 'cli') {
            fwrite(STDERR, "No se pudo conectar con la base de datos: " . $e->getMessage() . PHP_EOL);
            exit(1);
        }
        http_response_code(503);
        header('Content-Type: text/html; charset=utf-8');
        echo '<!doctype html><meta charset="utf-8"><title>Sin conexión</title>';
        echo '<div style="font:16px/1.6 system-ui;max-width:44rem;margin:12vh auto;padding:0 1.5rem">';
        echo '<h1>No pudimos conectar con la base de datos</h1>';
        echo '<p>Revisa las variables <code>DB_HOST</code>, <code>DB_PORT</code>, <code>DB_NAME</code>, ';
        echo '<code>DB_USER</code> y <code>DB_PASSWORD</code> del archivo <code>.env</code>.</p></div>';
        exit;
    }

    return $pdo;
}

/** Ejecuta una consulta preparada y devuelve el statement. */
function bd_ejecutar(string $sql, array $params = []): PDOStatement
{
    $stmt = bd()->prepare($sql);
    $stmt->execute($params);
    return $stmt;
}

/** Devuelve la primera fila o null. */
function bd_fila(string $sql, array $params = []): ?array
{
    $fila = bd_ejecutar($sql, $params)->fetch();
    return $fila === false ? null : $fila;
}

/** Devuelve todas las filas. */
function bd_todas(string $sql, array $params = []): array
{
    return bd_ejecutar($sql, $params)->fetchAll();
}

/** Devuelve la primera columna de la primera fila. */
function bd_valor(string $sql, array $params = [], mixed $porDefecto = null): mixed
{
    $valor = bd_ejecutar($sql, $params)->fetchColumn();
    return $valor === false ? $porDefecto : $valor;
}

/**
 * Traduce un nombre de campo de la API (camelCase) a su columna real.
 * Solo se usan nombres de una lista blanca, nunca texto del usuario.
 */
function bd_columna(string $campo): ?string
{
    static $mapa = [
        'name' => 'name', 'nombre' => 'name',
        'coach' => 'coach', 'entrenador' => 'coach',
        'colors' => 'colors', 'colores' => 'colors',
        'note' => 'note', 'nota' => 'note',
        'division' => 'division', 'division' => 'division',
        'stage' => 'stage', 'fase' => 'stage',
        'journey' => 'journey', 'jornada' => 'journey',
        'journeyLabel' => 'journey_label', 'journey_label' => 'journey_label',
        'range' => 'range', 'rango' => 'range',
        'date' => 'date', 'fecha' => 'date',
        'time' => 'time', 'hora' => 'time',
        'home' => 'home', 'local' => 'home',
        'away' => 'away', 'visitante' => 'away',
        'homeGoals' => 'home_goals', 'home_goals' => 'home_goals',
        'awayGoals' => 'away_goals', 'away_goals' => 'away_goals',
        'status' => 'status', 'estado' => 'status',
        'replay' => 'replay', 'replay' => 'replay',
        'notes' => 'notes', 'notas' => 'notes',
        'title' => 'title', 'titulo' => 'title',
        'category' => 'category', 'categoria' => 'category',
        'excerpt' => 'excerpt', 'entradilla' => 'excerpt',
        'body' => 'body', 'cuerpo' => 'body',
        'author' => 'author', 'autor' => 'author',
        'image' => 'image', 'imagen' => 'image',
        'pinned' => 'pinned', 'portada' => 'pinned',
        'kind' => 'kind', 'tipo' => 'kind',
        'kicker' => 'kicker', 'subtitulo' => 'kicker',
        'season' => 'season', 'temporada' => 'season',
        'text' => 'text', 'texto' => 'text',
        'closing' => 'closing', 'cierre' => 'closing',
        'warning' => 'warning', 'aviso' => 'warning',
        'day' => 'day', 'dia' => 'day',
        'month' => 'month', 'mes' => 'month',
        'year' => 'year', 'anio' => 'year',
        'team' => 'team', 'equipo' => 'team',
        'label' => 'label', 'etiqueta' => 'label',
        'url' => 'url', 'enlace' => 'url',
        'players' => 'players', 'jugadores' => 'players',
        'description' => 'description', 'descripcion' => 'description',
        'href' => 'href', 'cta' => 'cta',
        'username' => 'username', 'usuario' => 'username',
        'role' => 'role', 'rol' => 'role',
        'bio' => 'bio', 'biografia' => 'bio',
        'avatar' => 'avatar', 'banner' => 'banner',
        'focus' => 'focus', 'especialidad' => 'focus',
        'github' => 'github', 'instagram' => 'instagram', 'discord' => 'discord',
        'available' => 'available', 'disponible' => 'available',
        'network' => 'network', 'red' => 'network',
        'owner_name' => 'owner_name', 'ownerName' => 'owner_name',
        'handle' => 'handle', 'usuario_red' => 'handle',
        'followers' => 'followers', 'seguidores' => 'followers',
        'is_streamer' => 'is_streamer', 'isStreamer' => 'is_streamer',
        'method' => 'method', 'metodo' => 'method',
        'account' => 'account', 'cuenta' => 'account',
        'amount' => 'amount', 'monto' => 'amount',
        'goal' => 'goal', 'meta' => 'goal',
        'raised' => 'raised', 'recaudado' => 'raised',
        'is_active' => 'is_active', 'isActive' => 'is_active',
        'is_live' => 'is_live', 'isLive' => 'is_live',
        'league' => 'league', 'competicion' => 'league',
        'channel' => 'channel', 'canal' => 'channel',
        'platform' => 'platform', 'plataforma' => 'platform',
        'viewer_count' => 'viewer_count', 'viewerCount' => 'viewer_count',
        'home_score' => 'home_score', 'homeScore' => 'home_score',
        'away_score' => 'away_score', 'awayScore' => 'away_score',
        'starts_at' => 'starts_at', 'startsAt' => 'starts_at',
        'sort_order' => 'sort_order', 'sortOrder' => 'sort_order',
    ];
    return $mapa[$campo] ?? null;
}
