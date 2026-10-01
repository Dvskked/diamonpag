<?php
/* ============================================================================
 * The Diamonds League · portada pública con las 12 entradas
 * neptun / andres / Dvskked — github.com/Dvskked
 * ========================================================================== */

/** Banda de marquesina del hero: recorre los nombres completos de las entradas. */
function banda_hero(): string
{
    $nombres = [];
    foreach (modulos() as $modulo) {
        $nombres[] = $modulo['nombre'];
        if (!empty($modulo['gear'])) {
            $nombres[] = 'TUERCA DE CONFIGURACION';
        }
    }
    $items = '';
    foreach ($nombres as $nombre) {
        $items .= '<span class="marquee-item">' . e($nombre) . '</span>'
            . '<i class="marquee-dot" aria-hidden="true"></i>';
    }
    /* Dos grupos idénticos para que el bucle de la animación sea continuo. */
    $grupos = '<div class="marquee-group">' . $items . '</div>';
    return '<div class="marquee" aria-hidden="true">
  <div class="marquee-track">' . $grupos . $grupos . '</div>
</div>';
}

/** Cómo se juega: formato, puntos y configuración. */
function como_se_juega(array $datos): string
{
    $ajustes = $datos['settings'];
    $puntos = [
        ['Victoria', $ajustes['pointsWin'] . ' pts'],
        ['Empate', $ajustes['pointsDraw'] . ' pt'],
        ['Derrota', '0 pts'],
        ['Tolerancia', $ajustes['tolerance']],
        ['W.O.', 'Mínimo 4 jugadores']
    ];
    $filas = '';
    foreach ($puntos as [$etiqueta, $valor]) {
        $filas .= '<div><dt>' . e($etiqueta) . '</dt><dd>' . e($valor) . '</dd></div>';
    }
    $config = '';
    foreach ($datos['matchConfig'] as $item) {
        $config .= '<li><small>' . e($item['label']) . '</small><strong>' . e($item['value']) . '</strong></li>';
    }
    return '<div class="how-to-play">
    <h3>Cómo se juega</h3>
    <p>Formato oficial <strong>' . e($ajustes['modality']) . '</strong> sobre el mapa <strong>'
        . e($ajustes['map']) . '</strong> en el servidor <strong>' . e($ajustes['server']) . '</strong>. '
        . e($ajustes['matchDuration']) . '. Cada equipo debe presentar mínimo 4 jugadores o se aplica el W.O.</p>
    <dl class="rule-points">' . $filas . '</dl>
    ' . ($config !== '' ? '<ul class="config-list">' . $config . '</ul>' : '') . '
  </div>';
}

/** Tabla de posiciones. */
function tabla_clasificacion(array $division, array $filas): string
{
    if (!$filas) {
        return '<p class="empty">Todavía no hay equipos cargados en ' . e($division['name']) . '.</p>';
    }
    $cuerpo = '';
    foreach ($filas as $fila) {
        $dif = (int) $fila['goalDiff'];
        $cuerpo .= '<tr' . ($fila['position'] <= 4 ? ' class="is-qualified"' : '') . '>'
            . '<td>' . (int) $fila['position'] . '</td>'
            . '<th scope="row">' . e($fila['name']) . '</th>'
            . '<td>' . (int) $fila['played'] . '</td>'
            . '<td>' . (int) $fila['won'] . '</td>'
            . '<td>' . (int) $fila['drawn'] . '</td>'
            . '<td>' . (int) $fila['lost'] . '</td>'
            . '<td>' . (int) $fila['goalsFor'] . '</td>'
            . '<td>' . (int) $fila['goalsAgainst'] . '</td>'
            . '<td>' . ($dif > 0 ? '+' : '') . $dif . '</td>'
            . '<td class="is-points">' . (int) $fila['points'] . '</td>'
            . '</tr>';
    }
    return '<div class="table-wrap">
    <table class="standings">
      <caption class="sr-only">Clasificación de ' . e($division['name']) . '</caption>
      <thead><tr>
        <th scope="col">#</th><th scope="col">Equipo</th><th scope="col">PJ</th><th scope="col">G</th>
        <th scope="col">E</th><th scope="col">P</th><th scope="col">GF</th><th scope="col">GC</th>
        <th scope="col">DG</th><th scope="col">Pts</th>
      </tr></thead>
      <tbody>' . $cuerpo . '</tbody>
    </table>
  </div>';
}

/** Bloque completo de una división: fases, movimiento, reglas y tabla. */
function bloque_division(array $division, array $tabla, int $indice): string
{
    $fases = '';
    foreach ((array) $division['phases'] as $fase) {
        $fases .= '<article class="card">
            <span class="card-kicker">' . e($fase['label'] ?? '') . '</span>
            <h4>' . e($fase['title'] ?? '') . '</h4>
            <p>' . e($fase['text'] ?? '') . '</p>'
            . (!empty($fase['note']) ? '<p class="card-note">' . e($fase['note']) . '</p>' : '')
            . '</article>';
    }

    $movimiento = (array) $division['movement'];
    $items = '';
    foreach ((array) ($movimiento['items'] ?? []) as $item) {
        $items .= '<article>
              <small>' . e($item['place'] ?? '') . '</small>
              <strong>' . e($item['label'] ?? '') . '</strong>
              <p>' . e($item['text'] ?? '') . '</p>
            </article>';
    }
    $movimientoHtml = $items !== ''
        ? '<div class="movement">
            <h4>' . e($movimiento['title'] ?: 'Movimiento') . '</h4>
            <div class="movement-grid">' . $items . '</div>
          </div>'
        : '';

    $reglas = '';
    foreach ((array) $division['rules'] as $regla) {
        $reglas .= '<li><strong>' . e($regla['title'] ?? '') . '</strong><p>' . e($regla['text'] ?? '') . '</p></li>';
    }

    return '<article class="division-block" id="equipos-' . e($division['id']) . '">
      <header class="division-head">
        <p class="eyebrow">División ' . e($indice) . '</p>
        <h3>' . e($division['name']) . ' <span class="accent">' . e($division['code']) . '</span></h3>
        <p>' . e($division['summary']) . '</p>
      </header>
      <ul class="kv-grid">
        <li><small>Equipos</small><strong>' . (int) $division['teams'] . '</strong></li>
        <li><small>Jornadas</small><strong>' . (int) $division['journeys'] . '</strong></li>
        <li><small>Playoffs</small><strong>' . e($division['playoffs']) . '</strong></li>
        <li><small>' . e($movimiento['title'] ?: 'Movimiento') . '</small><strong>'
            . e($division['promotion'] ?: ($division['relegation'] ?: '—')) . '</strong></li>
      </ul>
      ' . ($fases !== '' ? '<div class="phase-grid">' . $fases . '</div>' : '')
      . $movimientoHtml
      . ($reglas !== '' ? '<div class="division-rules">
            <h4>Reglas de ' . e($division['name']) . '</h4>
            <ul>' . $reglas . '</ul>
          </div>' : '')
      . '<div class="standings-block">
            <div class="block-head">
              <h4>Clasificación · ' . e($division['name']) . '</h4>
              <p>Se actualiza con los resultados que carga el staff.</p>
            </div>
            ' . tabla_clasificacion($division, $tabla) . '
          </div>
    </article>';
}

/** Reglamento por pestañas. */
function reglamento(array $reglas): string
{
    if (!$reglas) {
        return '<p class="empty">El reglamento se publicará próximamente.</p>';
    }
    $pestanas = '';
    $paneles = '';
    foreach ($reglas as $i => $regla) {
        $pestanas .= '<button type="button" role="tab" aria-selected="' . ($i === 0 ? 'true' : 'false')
            . '" data-rule-tab="' . e($regla['id']) . '">' . e($regla['title']) . '</button>';

        $puntos = '';
        $lista = '';
        foreach ($regla['items'] ?? [] as $n => $item) {
            $titulo = is_array($item) ? (string) ($item['title'] ?? '') : '';
            $texto = is_array($item) ? (string) ($item['text'] ?? '') : (string) $item;
            $lista .= '<li><span>' . str_pad((string) ($n + 1), 2, '0', STR_PAD_LEFT) . '</span>'
                . '<div><strong>' . e($titulo !== '' ? $titulo : $texto) . '</strong>'
                . ($titulo !== '' && $texto !== $titulo ? '<p>' . e($texto) . '</p>' : '')
                . '</div></li>';
        }

        $bloques = '';
        foreach ($regla['blocks'] ?? [] as $bloque) {
            $ticks = '';
            foreach ($bloque['list'] ?? [] as $li) {
                $ticks .= '<li>' . e(is_array($li) ? ($li['text'] ?? '') : $li) . '</li>';
            }
            $bloques .= '<article class="card">
              <span class="card-kicker">' . e($bloque['subtitle'] ?: 'Regla') . '</span>
              <h4>' . e($bloque['title'] ?? '') . '</h4>'
                . (!empty($bloque['text']) ? '<p>' . e($bloque['text']) . '</p>' : '')
                . ($ticks !== '' ? '<ul class="ticks">' . $ticks . '</ul>' : '')
                . '</article>';
        }

        $tarjetas = '';
        foreach ($regla['cards'] ?? [] as $tarjeta) {
            $ticks = '';
            foreach ($tarjeta['list'] ?? [] as $li) {
                $ticks .= '<li>' . e(is_array($li) ? ($li['text'] ?? '') : $li) . '</li>';
            }
            $tarjetas .= '<article class="card card-' . e($tarjeta['tone'] ?? 'info') . '">
              <span class="card-kicker">' . e($tarjeta['kicker'] ?? '') . '</span>
              <h4>' . e($tarjeta['title'] ?? '') . '</h4>'
                . ($ticks !== '' ? '<ul class="ticks">' . $ticks . '</ul>' : '')
                . (!empty($tarjeta['text']) ? '<p class="card-note">' . e($tarjeta['text']) . '</p>' : '')
                . '</article>';
        }

        $paneles .= '<div class="panel" data-rule-panel="' . e($regla['id']) . '"' . ($i === 0 ? '' : ' hidden') . '>'
            . '<p class="panel-lead">' . e($regla['summary'] ?? '') . '</p>'
            . ($lista !== '' ? '<ol class="rule-list">' . $lista . '</ol>' : '')
            . ($bloques !== '' ? '<div class="block-grid">' . $bloques . '</div>' : '')
            . ($tarjetas !== '' ? '<div class="discipline-grid">' . $tarjetas . '</div>' : '')
            . '</div>';
    }
    return '<div class="tabs" data-tabs="rules" id="reglas">
      <div class="chip-row" role="tablist" aria-label="Secciones del reglamento">' . $pestanas . '</div>
      ' . $paneles . '
    </div>';
}

/** Agrupa los partidos por división, jornada y fase. */
function grupos_jornada(array $partidos): array
{
    $grupos = [];
    foreach ($partidos as $partido) {
        $clave = $partido['journey'] !== null && $partido['journey'] !== ''
            ? 'j' . (int) $partido['journey']
            : 'p-' . ($partido['journeyLabel'] ?: 'extra');
        if (!isset($grupos[$clave])) {
            $grupos[$clave] = [
                'key' => $clave,
                'label' => $partido['journey'] !== null && $partido['journey'] !== ''
                    ? 'J' . (int) $partido['journey']
                    : ($partido['journeyLabel'] ?: 'Extra'),
                'title' => $partido['journey'] !== null && $partido['journey'] !== ''
                    ? 'Jornada ' . (int) $partido['journey']
                    : fase_texto((string) $partido['stage']),
                'range' => (string) ($partido['range'] ?? ''),
                'stage' => (string) ($partido['stage'] ?? 'liga'),
                'matches' => []
            ];
        }
        $grupos[$clave]['matches'][] = $partido;
    }
    uasort($grupos, static function (array $a, array $b): int {
        if ($a['stage'] !== $b['stage']) {
            return $a['stage'] === 'liga' ? -1 : 1;
        }
        $fa = $a['matches'][0]['date'] ?? '';
        $fb = $b['matches'][0]['date'] ?? '';
        if ($fa !== '' && $fb !== '' && $fa !== $fb) {
            return strcmp($fa, $fb);
        }
        return strnatcasecmp($a['label'], $b['label']);
    });
    return $grupos;
}

/** Fila de un partido. */
function fila_partido(array $partido): string
{
    $jugado = in_array($partido['status'], ['finalizado', 'wo'], true);
    $marcador = $jugado && $partido['homeGoals'] !== null
        ? (int) $partido['homeGoals'] . ' - ' . (int) $partido['awayGoals']
        : null;
    $replay = url_segura($partido['replay'] ?? '');
    $caliente = $partido['status'] === 'en-vivo' ? ' is-hot' : '';

    return '<li class="match">
    <div class="match-when">
      <strong>' . e(fecha_larga($partido['date'] ?: null)) . '</strong>
      <span>' . e(hora($partido['time'] ?? '')) . '</span>
    </div>
    <div class="match-teams">
      <span class="team' . $caliente . '">' . e($partido['home']) . '</span>
      <span class="vs">' . ($marcador !== null ? '<b>' . e($marcador) . '</b>' : 'vs') . '</span>
      <span class="team' . $caliente . '">' . e($partido['away']) . '</span>
    </div>
    <div class="match-state"><span class="chip chip-' . e(str_replace('-', '', (string) $partido['status'])) . '">'
        . e(estado_texto((string) $partido['status'])) . '</span>'
        . ($replay !== '' ? '<a href="' . e($replay) . '" target="_blank" rel="noopener noreferrer">Replay</a>' : '')
        . '</div>
  </li>';
}

/** Mapa de la liga: navegación rápida de las 12 entradas (11 anclas + tuerca). */
function mapa_modulos(): string
{
    $salida = '';
    $i = 0;
    foreach (modulos() as $modulo) {
        $salida .= entrada_mapa($i + 1, '#' . $modulo['id'], $modulo['nombre'], $modulo['desc']);
        $i++;
        if (!empty($modulo['gear'])) {
            $salida .= entrada_mapa(++$i, '#tuerca', 'TUERCA DE CONFIGURACION', 'Acceso, cuenta, contraseña, premium, administración y privacidad');
        }
    }
    return '<section class="section section-modules" aria-labelledby="modulos-title">
  <div class="shell">
    <header class="section-head">
      <p class="eyebrow">Módulos</p>
      <h2 id="modulos-title">Todo en doce entradas</h2>
      <p>Información pública de la liga, sin ruido y actualizada por el staff desde el panel de administración.</p>
    </header>
    <ul class="module-grid">' . $salida . '</ul>
  </div>
</section>';
}

/** Tarjeta del mapa de módulos. */
function entrada_mapa(int $numero, string $href, string $nombre, string $desc): string
{
    return '<li>
        <a href="' . e($href) . '">
          <span class="module-index">' . str_pad((string) $numero, 2, '0', STR_PAD_LEFT) . '</span>
          <strong>' . e($nombre) . '</strong>
          <small>' . e($desc) . '</small>
        </a>
      </li>';
}

/** @'s de un usuario de la liga (sin la @ inicial). */
function usuario_sin_arroba($valor): string
{
    return ltrim(trim((string) $valor), '@');
}

/** Redes del staff: mismo marcado y clases que el diseño original. */
function redes_staff(array $miembro): string
{
    $items = '';
    $ig = usuario_sin_arroba($miembro['instagram'] ?? '');
    $gh = usuario_sin_arroba($miembro['github'] ?? '');
    $dc = usuario_sin_arroba($miembro['discord'] ?? '');

    if ($ig !== '') {
        $items .= '<li><a class="social social-ig" href="https://instagram.com/' . e($ig)
            . '" target="_blank" rel="noopener noreferrer nofollow">'
            . icono_red('instagram') . '<span>Instagram</span><b>@' . e($ig) . '</b></a></li>';
    }
    if ($gh !== '') {
        $items .= '<li><a class="social social-gh" href="https://github.com/' . e($gh)
            . '" target="_blank" rel="noopener noreferrer nofollow">'
            . icono_red('otro') . '<span>GitHub</span><b>@' . e($gh) . '</b></a></li>';
    }
    if ($dc !== '') {
        $items .= '<li><button class="social social-dc" type="button" data-copy="' . e($dc)
            . '" title="Copiar Discord">' . icono_red('discord')
            . '<span>Discord</span><b data-copy-value>' . e($dc) . '</b></button></li>';
    }

    return $items === '' ? '' : '<ul class="socials">' . $items . '</ul>';
}

/** Marca luminosa para las tarjetas del staff sin banner. */
function marca_radiante(): string
{
    return '<span class="member-radiant" aria-hidden="true"><i class="member-ring"></i><i class="member-ring"></i>'
        . '<i class="member-ring"></i><img src="/assets/logo-mark.png" width="30" height="30" alt="" loading="lazy"></span>';
}

/** Ficha ampliada de un miembro del equipo, en el mismo modal del diseño original. */
function ficha_staff(array $miembro, string $redes): string
{
    $avatar = ruta_segura($miembro['avatar'] ?? '', 300);
    $tags = '';
    foreach ((array) ($miembro['tags'] ?? []) as $tag) {
        $titulo = is_array($tag) ? ($tag['title'] ?? '') : (string) $tag;
        if ($titulo !== '') {
            $tags .= '<li>' . e($titulo) . '</li>';
        }
    }

    return '<div class="member-detail" data-member-detail hidden>
            <div class="member-detail-head">
              <span class="member-avatar member-avatar-lg" aria-hidden="true">'
        . ($avatar !== '' ? '<img src="' . e($avatar) . '" width="88" height="88" alt="" loading="lazy">' : '')
        . '</span>
              <div>
                <p class="card-kicker">' . e($miembro['role']) . '</p>
                <h3>' . e($miembro['name']) . '</h3>
                <p class="member-user">@' . e($miembro['username'] ?: '—') . '</p>
              </div>
            </div>'
        . (!empty($miembro['bio']) ? '<p class="member-bio">' . e($miembro['bio']) . '</p>' : '')
        . (!empty($miembro['focus'])
            ? '<p class="member-focus"><span>Especialidad</span>' . e($miembro['focus']) . '</p>'
            : '')
        . $redes
        . (!empty($miembro['available'])
            ? '<p class="member-avail"><i aria-hidden="true"></i>Disponible para nuevos proyectos</p>'
            : '')
        . ($tags !== '' ? '<ul class="member-tags">' . $tags . '</ul>' : '')
        . '</div>';
}

/** Tarjeta del equipo de administración (marcado y clases del diseño original). */
function tarjeta_staff(array $miembro): string
{
    $rol = $miembro['role'] ?: 'Staff';
    $clases = ['member'];
    if ($rol === 'Owner') {
        $clases[] = 'is-owner';
    }
    if (mb_strtoupper($rol) === 'DESARROLLADOR') {
        $clases[] = 'is-developer';
    }

    $redes = redes_staff($miembro);
    $avatar = ruta_segura($miembro['avatar'] ?? '', 300);
    $banner = ruta_segura($miembro['banner'] ?? '', 300);
    $tags = '';
    foreach ((array) ($miembro['tags'] ?? []) as $tag) {
        $titulo = is_array($tag) ? ($tag['title'] ?? '') : (string) $tag;
        if ($titulo !== '') {
            $tags .= '<li>' . e($titulo) . '</li>';
        }
    }

    $imagen = $avatar !== ''
        ? '<img class="member-avatar" src="' . e($avatar) . '" width="64" height="64" alt="Foto de '
            . e($miembro['name']) . '" loading="lazy">'
        : '<span class="member-avatar member-avatar-empty" aria-hidden="true"></span>';

    $cabecera = $banner !== ''
        ? '<img src="' . e($banner) . '" width="320" height="72" alt="" aria-hidden="true" loading="lazy">'
        : marca_radiante();

    return '<li class="' . e(implode(' ', $clases)) . '">
        <article>
          <div class="member-banner' . ($banner !== '' ? '' : ' is-radiant') . '">' . $cabecera . '</div>
          <div class="member-body">
            ' . $imagen . '
            <div>
              <p class="card-kicker">' . e($rol) . '</p>
              <h3>' . e($miembro['name']) . '</h3>
              <p class="member-user">@' . e($miembro['username'] ?: '—') . '</p>'
        . (!empty($miembro['bio']) ? '<p class="member-bio">' . e($miembro['bio']) . '</p>' : '')
        . (!empty($miembro['available'])
            ? '<p class="member-avail"><i aria-hidden="true"></i>Disponible para nuevos proyectos</p>'
            : '')
        . ($tags !== '' ? '<ul class="member-tags">' . $tags . '</ul>' : '')
        . $redes
        . '</div>
          </div>'
        . ($redes !== '' || !empty($miembro['focus'])
            ? '<button class="member-open" type="button" data-member-open>Ver ficha y redes</button>'
            : '')
        . '</article>'
        . ficha_staff($miembro, $redes)
        . '</li>';
}

/* -------------------------------------------------------------------------
 * Secciones
 * ---------------------------------------------------------------------- */

/** 01 · LIGA */
function seccion_liga(array $datos, array $tablas): string
{
    $ajustes = $datos['settings'];
    $divisiones = '';
    $navegacion = '';
    foreach ($datos['divisions'] as $i => $division) {
        $divisiones .= bloque_division($division, $tablas[$division['id']] ?? [], $i + 1);
        $navegacion .= '<a href="#equipos-' . e($division['id']) . '">' . e($division['name']) . '</a>';
    }

    $accesos = '';
    foreach ($datos['important'] as $item) {
        $href = enlace_seguro($item['href'] ?? '', 400) ?: '#';
        $externo = $item['kind'] === 'external' || es_externo($href);
        $accesos .= '<li>
        <a href="' . e($href) . '"' . ($externo ? ' target="_blank" rel="noopener noreferrer"' : '') . '>
          <strong>' . e($item['title']) . '</strong>
          <small>' . e($item['description'] ?? '') . '</small>
          <span>' . e($item['cta'] ?: 'Abrir') . ' <i aria-hidden="true">→</i></span>
        </a>
      </li>';
    }

    $equipos = '';
    foreach ($datos['teams'] as $equipo) {
        $colores = '';
        foreach (preg_split('/[,\s]+/', (string) ($equipo['colors'] ?? ''), -1, PREG_SPLIT_NO_EMPTY) as $color) {
            if (preg_match('/^#?[0-9a-fA-F]{3,8}$/', $color)) {
                $hex = str_starts_with($color, '#') ? $color : '#' . $color;
                $colores .= '<span class="team-color" style="background:' . e($hex) . '"></span>';
            }
        }
        $equipos .= '<li>
          <span class="team-swatch">' . ($colores !== '' ? $colores : '<i></i>') . '</span>
          <strong>' . e($equipo['name']) . '</strong>
          <small>' . e(strtoupper((string) $equipo['division'])) . (!empty($equipo['coach']) ? ' · ' . e($equipo['coach']) : '') . '</small>
        </li>';
    }

    return '<section class="section" id="liga" aria-labelledby="liga-title">
  <div class="shell">
    <header class="section-head">
      <p class="eyebrow">01 · Liga</p>
      <h2 id="liga-title">Todo sobre la competición <span class="accent">' . e($ajustes['season']) . '</span></h2>
      <p>Reglamento, formato, información general y las tablas de cada división separadas.</p>
    </header>

    <div class="status-panel">
      <div>
        <p class="eyebrow">Estado de la liga</p>
        <h3>' . e($ajustes['status']) . '</h3>
        <p>' . e($ajustes['statusNote']) . '</p>
      </div>
      <dl>
        <div><dt>Temporada</dt><dd>' . e($ajustes['season']) . '</dd></div>
        <div><dt>Modalidad</dt><dd>' . e($ajustes['modality']) . '</dd></div>
        <div><dt>Divisiones</dt><dd>' . count($datos['divisions']) . '</dd></div>
        <div><dt>Servidor</dt><dd>' . e($ajustes['server']) . '</dd></div>
      </dl>
    </div>

    ' . como_se_juega($datos) . '

    <div class="section-subsection">
      <div class="block-head">
        <h3>Reglamento de la liga</h3>
        <p>Normas de Discord, comunidad, formato de competición y sanciones.</p>
      </div>
      ' . reglamento($datos['rules']) . '
    </div>

    <div class="section-subsection" id="equipos">
      <div class="block-head">
        <h3>Divisiones y clasificación</h3>
        <p>Cada división con su formato, su movimiento y su tabla de posiciones.</p>
      </div>
      ' . ($navegacion !== '' ? '<div class="chip-row anchor-row">' . $navegacion . '</div>' : '')
      . $divisiones . '
    </div>

    <div class="section-subsection" id="equipos-inscritos">
      <div class="block-head">
        <h3>Equipos inscritos</h3>
        <p>' . count($datos['teams']) . ' ' . plural(count($datos['teams']), 'equipo', 'equipos') . ' repartidos entre las divisiones.</p>
      </div>
      <ul class="team-list">' . $equipos . '</ul>
    </div>

    ' . ($accesos !== '' ? '<div class="section-subsection" id="importante">
      <div class="block-head">
        <h3>Accesos de la liga</h3>
        <p>Estado actual, calendario, partners y redes en un solo lugar.</p>
      </div>
      <ul class="link-grid">' . $accesos . '</ul>
    </div>' : '') . '
  </div>
</section>';
}

/** 02 · FECHAS */
function seccion_fechas(array $datos): string
{
    $salida = '';
    $hay = false;
    foreach ($datos['divisions'] as $division) {
        $partidos = array_values(array_filter(
            $datos['matches'],
            static fn(array $m): bool => (string) ($m['division'] ?? '') === $division['id']
        ));
        $grupos = grupos_jornada($partidos);
        if (!$grupos) {
            continue;
        }
        $hay = true;
        $pestanas = '';
        $paneles = '';
        $primero = true;
        foreach ($grupos as $grupo) {
            $pestanas .= '<button type="button" role="tab" aria-selected="' . ($primero ? 'true' : 'false')
                . '" data-journey-tab="' . e($grupo['key']) . '">' . e($grupo['label']) . '</button>';
            $filas = '';
            foreach ($grupo['matches'] as $partido) {
                $filas .= fila_partido($partido);
            }
            $paneles .= '<div class="panel" data-journey-panel="' . e($grupo['key']) . '"' . ($primero ? '' : ' hidden') . '>
          <div class="block-head">
            <h4>' . e($grupo['title']) . '</h4>
            <p>' . e($grupo['range'] ?: fecha_larga($grupo['matches'][0]['date'] ?: null)) . ' · '
                . plural(count($grupo['matches']), 'partido', 'partidos') . '</p>
          </div>
          <ul class="match-list">' . $filas . '</ul>
        </div>';
            $primero = false;
        }
        $salida .= '<div class="tabs" data-tabs="journey">
      <h3 class="division-title">' . e($division['name']) . ' <small>' . e($division['code']) . '</small></h3>
      <div class="chip-row" role="tablist" aria-label="Jornadas de ' . e($division['name']) . '">' . $pestanas . '</div>
      ' . $paneles . '
    </div>';
    }

    return '<section class="section section-alt" id="fechas" aria-labelledby="fechas-title">
  <div class="shell">
    <header class="section-head">
      <p class="eyebrow">02 · Fechas</p>
      <h2 id="fechas-title">Calendario oficial</h2>
      <p>Jornadas, horarios y resultados de ' . e($datos['settings']['season'])
        . '. Cada fecha la publica el staff desde el panel.</p>
    </header>
    ' . ($hay ? $salida : '<p class="empty">El calendario se publica próximamente.</p>') . '
  </div>
</section>';
}

/** 03 · PUBS */
function seccion_pubs(array $datos): string
{
    $salas = '';
    foreach ($datos['pubs'] as $sala) {
        $url = url_segura($sala['url'] ?? '');
        $abierta = $sala['status'] === 'ABIERTA';
        $salas .= '<li>
        <a href="' . e($url !== '' ? $url : '#') . '"' . ($url !== '' ? ' target="_blank" rel="noopener noreferrer"' : ' aria-disabled="true"') . '>
          <div class="room-top">
            <img src="/assets/logo-mark.png" width="34" height="34" alt="" aria-hidden="true" loading="lazy">
            <span>' . e($sala['label'] ?? '') . '</span>
            <span class="chip ' . ($abierta ? 'chip-live' : 'chip-muted') . '">' . e($sala['status'] ?? '') . '</span>
          </div>
          <strong>' . e($sala['name'] ?? '') . '</strong>
          <small>' . e($sala['note'] ?: 'Sala pública oficial · ' . ($sala['label'] ?? '')) . '</small>
          <span class="room-cta">' . ($url !== '' ? 'Abrir sala' : 'Sin enlace') . ' <i aria-hidden="true">→</i></span>
        </a>
      </li>';
    }

    return '<section class="section section-alt" id="pubs" aria-labelledby="pubs-title">
  <div class="shell">
    <header class="section-head">
      <p class="eyebrow">03 · Pubs</p>
      <h2 id="pubs-title">Diamonds Pubs</h2>
      <p>Salas públicas de HaxBall de la liga. El staff las mantiene desde el panel.</p>
    </header>
    ' . aviso_rojo('Salas no disponibles', 'Los enlaces de las salas se publicarán de nuevo cuando la liga tenga servidores activos.') . '
    ' . ($salas !== ''
        ? '<ul class="room-grid is-disabled">' . $salas . '</ul>'
        : '<p class="empty">Todavía no hay salas registradas en el panel.</p>') . '
  </div>
</section>';
}

/** 04 · MUSEO */
function seccion_museo(array $datos): string
{
    $filtros = [
        'all' => 'Todo',
        'premios' => 'Premios',
        'rankings' => 'Rankings',
        'campeones' => 'Campeones',
        'd1' => 'División 1',
        'd2' => 'División 2'
    ];
    $chips = '';
    $i = 0;
    foreach ($filtros as $id => $etiqueta) {
        $chips .= '<button type="button" class="chip-btn" data-filter="' . e($id) . '" aria-pressed="'
            . ($i === 0 ? 'true' : 'false') . '">' . e($etiqueta) . '</button>';
        $i++;
    }

    $premios = '';
    foreach ($datos['awards'] as $premio) {
        $imagen = ruta_segura($premio['image'] ?? '', 300);
        $division = (string) ($premio['division'] ?? 'ambas');
        $etiquetaDivision = $division === 'ambas' ? 'General' : strtoupper($division);
        $contenido = $imagen !== ''
            ? '<button type="button" data-lightbox="' . e($imagen) . '" data-caption="'
                . e($premio['title'] . ' · ' . $premio['team']) . '">'
                . '<img src="' . e($imagen) . '" width="240" height="240" alt="' . e($premio['title']) . '" loading="lazy">'
                . '<span>Ampliar</span></button>'
            : '<span class="award-placeholder" aria-hidden="true">TDL</span>';
        $premios .= '<li class="award" data-category="' . e($premio['category'] ?? '') . '" data-division="'
            . e($division) . '">
          ' . $contenido . '
          <div class="award-caption">
            <small>' . e($premio['season'] ?? '') . ' · ' . e($etiquetaDivision) . '</small>
            <strong>' . e($premio['title']) . '</strong>
            <p>' . e($premio['team']) . ' · ' . e($premio['text'] ?? '') . '</p>
          </div>
        </li>';
    }

    $temporadas = array_values(array_unique(array_filter(array_map(
        static fn(array $a): string => (string) ($a['season'] ?? ''),
        $datos['awards']
    ))));

    return '<section class="section" id="museo" aria-labelledby="museo-title">
  <div class="shell">
    <header class="section-head">
      <p class="eyebrow">04 · Museo</p>
      <h2 id="museo-title">Museo de premios</h2>
      <p>La historia de la liga: premios entregados antiguos y recientes, rankings y clubes campeones.</p>
    </header>

    ' . ($temporadas !== ''
        ? '<div class="block-head">
            <h3>Colección ' . e(implode(' · ', $temporadas)) . '</h3>
            <p>' . count($datos['awards']) . ' piezas del museo, con filtro por categoría y división.</p>
          </div>'
        : '') . '
    ' . ($premios !== ''
        ? '<div class="chip-row" data-filters>' . $chips . '</div>
      <ul class="award-grid">' . $premios . '</ul>'
        : '<p class="empty">El museo se está preparando.</p>') . '
  </div>
</section>';
}

/** 05 · NOTICIAS */
function seccion_noticias(array $datos): string
{
    $items = $datos['news'];
    usort($items, static function (array $a, array $b): int {
        $fijadoA = !empty($a['pinned']);
        $fijadoB = !empty($b['pinned']);
        if ($fijadoA !== $fijadoB) {
            return $fijadoA ? -1 : 1;
        }
        return strcmp((string) $b['date'], (string) $a['date']);
    });

    $salida = '';
    foreach ($items as $item) {
        $imagen = ruta_segura($item['image'] ?? '', 300);
        $media = $imagen !== ''
            ? '<img src="' . e($imagen) . '" width="320" height="180" alt="' . e($item['title']) . '" loading="lazy">'
            : '<span class="news-placeholder" aria-hidden="true">TDL</span>';
        $salida .= '<li class="news-card">
        <article>
          <div class="news-media">' . $media
            . (!empty($item['pinned']) ? '<span class="news-flag">Portada</span>' : '') . '</div>
          <div class="news-body">
            <p class="news-meta"><span>' . e($item['category'] ?: 'Noticia') . '</span><time datetime="'
                . e($item['date'] ?? '') . '">' . e(fecha_corta($item['date'] ?? null)) . '</time></p>
            <h3>' . e($item['title']) . '</h3>
            <p>' . e($item['excerpt'] ?? '') . '</p>'
                . (!empty($item['body']) ? '<details><summary>Leer más</summary><p>' . e($item['body']) . '</p></details>' : '')
                . '<p class="news-author">' . e($item['author'] ?: 'Staff') . '</p>'
                . '</div>
        </article>
      </li>';
    }

    return '<section class="section" id="noticias" aria-labelledby="noticias-title">
  <div class="shell">
    <header class="section-head">
      <p class="eyebrow">05 · Noticias</p>
      <h2 id="noticias-title">Noticias de la liga</h2>
      <p>Resultados, entrevistas, novedades y avisos del servidor.</p>
    </header>
    ' . ($salida !== '' ? '<ul class="news-grid">' . $salida . '</ul>'
        : '<p class="empty">Todavía no hay noticias publicadas.</p>') . '
  </div>
</section>';
}

/** 06 · ANUNCIOS - NOVEDADES */
function seccion_anuncios(array $datos): string
{
    $salida = '';
    foreach ($datos['announcements'] as $anuncio) {
        $fecha = $anuncio['date'] ?? null;
        $dia = $anuncio['day'] !== null && $anuncio['day'] !== '' ? (int) $anuncio['day'] : (int) date('j', (int) strtotime((string) $fecha));
        $mes = $anuncio['month'] !== null && $anuncio['month'] !== ''
            ? date('M', mktime(0, 0, 0, (int) $anuncio['month'], 1))
            : (int) date('n', (int) strtotime((string) $fecha));
        $mesLargo = date('F', mktime(0, 0, 0, (int) $mes, 1));

        $ticks = '';
        foreach ((array) ($anuncio['bullets'] ?? []) as $bullet) {
            $ticks .= '<li>' . e(is_array($bullet) ? ($bullet['text'] ?? '') : $bullet) . '</li>';
        }

        $salida .= '<li class="ann">
        <article>
          <div class="ann-side">
            <span class="card-kicker">' . e($anuncio['season'] ?: 'Comunicado') . '</span>
            <strong class="ann-day">' . (int) $dia . '</strong>
            <span class="ann-month">' . e($mesLargo) . '</span>
          </div>
          <div class="ann-body">
            <p class="card-kicker">' . e($anuncio['kicker'] ?: 'Anuncio') . '</p>
            <h3>' . e($anuncio['title']) . '</h3>
            <p>' . e($anuncio['text'] ?? '') . '</p>'
                . ($ticks !== '' ? '<ul class="ticks">' . $ticks . '</ul>' : '')
                . (!empty($anuncio['warning']) ? '<p class="ann-warning">' . e($anuncio['warning']) . '</p>' : '')
                . (!empty($anuncio['closing']) ? '<p class="card-note">' . e($anuncio['closing']) . '</p>' : '')
                . '</div>
        </article>
      </li>';
    }

    return '<section class="section section-alt" id="anuncios" aria-labelledby="anuncios-title">
  <div class="shell">
    <header class="section-head">
      <p class="eyebrow">06 · Anuncios</p>
      <h2 id="anuncios-title">Anuncios y novedades</h2>
      <p>Comunicados de la liga, inscripciones, premios entregados y avisos importantes.</p>
    </header>
    ' . ($salida !== '' ? '<ul class="ann-list">' . $salida . '</ul>'
        : '<p class="empty">Todavía no hay anuncios publicados.</p>') . '
  </div>
</section>';
}

/** 07 · ALIANZAS */
function seccion_alianzas(array $datos): string
{
    $grupos = ['activa' => [], 'proxima' => [], 'inactiva' => []];
    foreach ($datos['alliances'] as $alianza) {
        $grupos[$alianza['status'] ?? 'activa'][] = $alianza;
    }
    $etiquetas = [
        'activa' => 'Afiliaciones y partners',
        'proxima' => 'Próximas afiliaciones',
        'inactiva' => 'Historial'
    ];

    $salida = '';
    foreach ($etiquetas as $estado => $titulo) {
        if (!$grupos[$estado]) {
            continue;
        }
        $tarjetas = '';
        foreach ($grupos[$estado] as $alianza) {
            $href = enlace_segura($alianza['href'] ?? '', 400);
            $imagen = ruta_segura($alianza['image'] ?? '', 300);
            $tarjetas .= '<li class="alliance-card is-' . e($estado) . '">
          ' . ($imagen !== '' ? '<img src="' . e($imagen) . '" width="120" height="120" alt="" loading="lazy">' : '')
            . '<div>
            <span class="card-kicker">' . e(ucfirst((string) ($alianza['kind'] ?? 'alianza'))) . '</span>
            <h3>' . e($alianza['name']) . '</h3>
            <p>' . e($alianza['description'] ?? '') . '</p>'
                . ($href !== '' ? '<a class="btn btn-outline btn-sm" href="' . e($href) . '" target="_blank" rel="noopener noreferrer">'
                    . e($alianza['cta'] ?: 'Ver más') . '</a>' : '')
                . '</div>
        </li>';
        }
        $salida .= '<div class="section-subsection">
        <div class="block-head"><h3>' . e($titulo) . '</h3></div>
        <ul class="alliance-grid">' . $tarjetas . '</ul>
      </div>';
    }

    return '<section class="section" id="alianzas" aria-labelledby="alianzas-title">
  <div class="shell">
    <header class="section-head">
      <p class="eyebrow">07 · Alianzas</p>
      <h2 id="alianzas-title">Alianzas y afiliaciones</h2>
      <p>Servidores, partners y clubes con los que la liga mantiene colaboración.</p>
    </header>
    ' . ($salida !== '' ? $salida : '<p class="empty">Todavía no hay alianzas registradas.</p>') . '
  </div>
</section>';
}

/** 08 · REDES SOCIALES */
function seccion_redes(array $datos): string
{
    $liga = [];
    $streamers = [];
    foreach ($datos['social'] as $red) {
        if (!empty($red['is_streamer'])) {
            $streamers[] = $red;
        } else {
            $liga[] = $red;
        }
    }

    $tarjetas = '';
    foreach (array_merge($liga, $streamers) as $red) {
        $url = url_segura($red['url'] ?? '');
        $seguidores = (int) ($red['followers'] ?? 0);
        $tarjetas .= '<li class="social-card' . (!empty($red['is_streamer']) ? ' is-streamer' : '') . '">
        <a href="' . e($url !== '' ? $url : '#') . '"' . ($url !== '' ? ' target="_blank" rel="noopener noreferrer"' : ' aria-disabled="true"') . '>
          <span class="social-icon">' . icono_red((string) ($red['network'] ?? 'otro')) . '</span>
          <div>
            <strong>' . e($red['owner_name'] ?? '') . '</strong>
            <small>' . e($red['handle'] ?? '') . '</small>
          </div>
          <span class="social-meta">'
            . ($seguidores > 0 ? '<i class="social-followers">' . e(texto_corto((string) $seguidores, 8)) . '</i>' : '')
            . (!empty($red['is_streamer']) ? '<em>Streamer</em>' : '')
            . '</span>
        </a>
      </li>';
    }

    return '<section class="section section-alt" id="redes" aria-labelledby="redes-title">
  <div class="shell">
    <header class="section-head">
      <p class="eyebrow">08 · Redes sociales</p>
      <h2 id="redes-title">Síguenos en redes</h2>
      <p>Cuentas oficiales de la liga y de los streamers que la transmiten.</p>
    </header>
    ' . ($tarjetas !== '' ? '<ul class="social-grid">' . $tarjetas . '</ul>'
        : '<p class="empty">Todavía no hay redes registradas.</p>') . '
  </div>
</section>';
}

/** 09 · EQUIPO ADMINISTRACION */
function seccion_equipo(array $datos): string
{
    $tarjetas = '';
    foreach ($datos['staff'] as $miembro) {
        $tarjetas .= tarjeta_staff($miembro);
    }
    $disponibles = count(array_filter($datos['staff'], static fn(array $m): bool => !empty($m['available'])));

    return '<section class="section" id="equipo" aria-labelledby="equipo-title">
  <div class="shell">
    <header class="section-head">
      <p class="eyebrow">09 · Equipo</p>
      <h2 id="equipo-title">Equipo de administración</h2>
      <p>Quiénes hacen posible la liga. ' . $disponibles . ' ' . plural($disponibles, 'miembro disponible', 'miembros disponibles') . ' para consultas.</p>
    </header>
    ' . ($tarjetas !== '' ? '<ul class="team-grid">' . $tarjetas . '</ul>'
        : '<p class="empty">Todavía no hay miembros en el equipo.</p>') . '
  </div>
</section>';
}

/** 10 · LIVE FUTBOL */
function seccion_live(array $datos): string
{
    $enVivo = array_values(array_filter($datos['live'], static fn(array $l): bool => !empty($l['is_live'])));
    $proximos = array_values(array_filter($datos['live'], static fn(array $l): bool => empty($l['is_live'])));
    $plataformas = ['twitch' => 'Twitch', 'youtube' => 'YouTube', 'kick' => 'Kick', 'otro' => 'Otra plataforma'];

    $tarjeta = static function (array $directo, array $plataformas) use ($datos): string {
        $url = url_segura($directo['url'] ?? '');
        $plataforma = (string) ($directo['platform'] ?? 'otro');
        $escala = $directo['home_score'] !== null && $directo['home_score'] !== ''
            ? e($directo['home_score']) . ' - ' . e($directo['away_score'] ?? '') : null;
        $escala = $escala !== null ? $escala : 'vs';
        return '<li class="live-card' . (!empty($directo['is_live']) ? ' is-live' : '') . '">
        <div class="live-top">
          <span class="live-league">' . e($directo['league'] ?? 'Fútbol en vivo') . '</span>
          ' . (!empty($directo['is_live'])
              ? '<span class="chip chip-live"><i class="pulse"></i> EN VIVO</span>'
              : '<span class="chip chip-muted">Próximamente</span>')
            . (!empty($directo['channel']) ? '<span class="live-channel">' . e($directo['channel']) . '</span>' : '') . '
        </div>
        <p class="live-teams"><strong>' . e($directo['home'] ?? '') . '</strong> <i>' . $escala . '</i> <strong>'
            . e($directo['away'] ?? '') . '</strong></p>
        <div class="live-foot">
          <span class="live-platform">' . e($plataformas[$plataforma] ?? 'Stream') . '</span>
          ' . (!empty($directo['viewer_count']) ? '<span class="live-viewers">'
              . e(texto_corto((string) (int) $directo['viewer_count'], 8)) . ' espectadores</span>' : '')
            . (!empty($directo['starts_at']) ? '<span class="live-when">'
                . e(fecha_larga(substr((string) $directo['starts_at'], 0, 10))) . ' · ' . e(hora((string) $directo['starts_at'])) . '</span>' : '')
            . '</div>
        ' . ($url !== ''
            ? '<a class="btn btn-primary btn-sm" href="' . e($url) . '" target="_blank" rel="noopener noreferrer">'
                . (!empty($directo['is_live']) ? 'Ver transmisión' : 'Ver canal') . '</a>'
            : '') . '
      </li>';
    };

    $vivos = '';
    foreach ($enVivo as $directo) {
        $vivos .= $tarjeta($directo, $plataformas);
    }
    $futuros = '';
    foreach ($proximos as $directo) {
        $futuros .= $tarjeta($directo, $plataformas);
    }

    return '<section class="section section-alt" id="live" aria-labelledby="live-title">
  <div class="shell">
    <header class="section-head">
      <p class="eyebrow">10 · Live</p>
      <h2 id="live-title">Live fútbol</h2>
      <p>Partidos en directo estilo Kick o Twitch. El staff publica aquí el canal de cada transmisión.</p>
    </header>

    <div class="live-player' . ($enVivo ? ' is-live' : '') . '">
      <div class="live-player-frame">
        ' . ($enVivo
            ? '<div class="live-placeholder"><span class="pulse"></span><strong>Transmisión en directo</strong>'
                . '<p>El reproductor del canal aparece aquí cuando hay juego en vivo.</p></div>'
            : '<div class="live-placeholder"><strong>Ahora mismo no hay fútbol en vivo</strong>'
                . '<p>Cuando el staff marque un directo como en vivo, se verá aquí.</p></div>') . '
      </div>
      <div class="live-player-meta">
        <span class="chip ' . ($enVivo ? 'chip-live' : 'chip-muted') . '">'
            . ($enVivo ? 'En vivo ahora' : 'Sin directo activo') . '</span>
        <p>Canales de la liga en Twitch, YouTube y Kick.</p>
      </div>
    </div>

    ' . ($vivos !== '' ? '<div class="block-head"><h3>Ahora en directo</h3></div>
      <ul class="live-grid">' . $vivos . '</ul>' : '') . '
    ' . ($futuros !== '' ? '<div class="block-head"><h3>Próximas transmisiones</h3></div>
      <ul class="live-grid">' . $futuros . '</ul>' : '') . '
  </div>
</section>';
}

/** 11 · DONACIÓN */
function seccion_donacion(array $datos): string
{
    $ajustes = $datos['settings'];
    $meta = [];
    $metodos = [];
    $metaInfo = null;
    foreach ($datos['donations'] as $donacion) {
        if ($donacion['kind'] === 'metodo') {
            $metodos[] = $donacion;
        } elseif ($donacion['kind'] === 'meta') {
            $meta[] = $donacion;
        } else {
            $metaInfo = $metaInfo ?? $donacion;
        }
    }

    $objetivo = (float) $ajustes['donationGoal'];
    $recaudado = 0.0;
    foreach ($meta as $fila) {
        $recaudado += (float) ($fila['raised'] ?? 0);
    }
    if ($objetivo > 0) {
        $porcentaje = max(0, min(100, round(($recaudado / $objetivo) * 100)));
    } else {
        $porcentaje = 0;
    }

    $tarjetas = '';
    foreach ($metodos as $metodo) {
        $tarjetas .= '<li class="donation-card">
        <span class="card-kicker">' . e($metodo['method'] ?: 'Método') . '</span>
        <h3>' . e($metodo['title']) . '</h3>
        <p>' . e($metodo['description'] ?? '') . '</p>'
            . (!empty($metodo['account'])
                ? '<p class="donation-account"><code>' . e($metodo['account']) . '</code></p>' : '')
            . (!empty($metodo['amount']) ? '<p class="donation-amount">$ ' . e(number_format((float) $metodo['amount'], 2, ',', '.')) . '</p>' : '')
            . '</li>';
    }
    $historico = '';
    foreach ($meta as $fila) {
        $historico .= '<li><span>' . e($fila['title']) . '</span><strong>$ '
            . e(number_format((float) ($fila['raised'] ?? 0), 2, ',', '.')) . '</strong></li>';
    }

    return '<section class="section" id="donacion" aria-labelledby="donacion-title">
  <div class="shell">
    <header class="section-head">
      <p class="eyebrow">11 · Donación</p>
      <h2 id="donacion-title">Apoya a la liga</h2>
      <p>Tus aportes pagan los servidores, los premios y el material de la competición.</p>
    </header>

    <div class="status-panel">
      <div>
        <p class="eyebrow">Sobreviviendo</p>
        <h3>' . e($metaInfo['description'] ?? $ajustes['donationNote'] ?: 'Apoyo a The Diamonds League') . '</h3>
        <p>' . e($ajustes['donationNote'] ?: '') . '</p>
      </div>
      <dl>
        <div><dt>Recaudado</dt><dd>$ ' . e(number_format($recaudado, 2, ',', '.')) . '</dd></div>
        <div><dt>Objetivo</dt><dd>' . ($objetivo > 0 ? '$ ' . e(number_format($objetivo, 2, ',', '.')) : 'Por definir') . '</dd></div>
        <div><dt>Progreso</dt><dd>' . (int) $porcentaje . '%</dd></div>
        <div><dt>Clave</dt><dd>' . e($ajustes['donationKey'] ?: 'Pendiente') . '</dd></div>
      </dl>
    </div>

    ' . ($objetivo > 0
        ? '<div class="goal-bar"><span style="width:' . (int) $porcentaje . '%"></span></div>' : '') . '

    ' . ($tarjetas !== ''
        ? '<div class="block-head"><h3>Métodos de pago</h3><p>El staff edita estos datos desde el panel.</p></div>
      <ul class="donation-grid">' . $tarjetas . '</ul>'
        : aviso_rojo('Métodos de pago pendientes', 'El staff todavía no ha publicado los datos de donación. Escríbenos por Discord para colaborar.')) . '

    ' . ($historico !== '' ? '<div class="block-head"><h3>Historial</h3></div>
      <ul class="donation-history">' . $historico . '</ul>' : '') . '
  </div>
</section>';
}

/** Hero de portada. */
function seccion_hero(array $datos, ?array $usuario, ?array $proximo, array $tablas): string
{
    $ajustes = $datos['settings'];
    $enVivo = count(array_filter($datos['live'], static fn(array $l): bool => !empty($l['is_live'])));
    $salasAbiertas = count(array_filter($datos['pubs'], static fn(array $s): bool => $s['status'] === 'ABIERTA'));
    $jornadas = count(array_filter($datos['matches'], static fn(array $m): bool => ($m['status'] ?? '') === 'programado'));
    $noticias = count($datos['news']);

    $estadisticas = [
        ['label' => 'Equipos', 'value' => (string) count($datos['teams'])],
        ['label' => 'Divisiones', 'value' => (string) count($datos['divisions'])],
        ['label' => 'Próximas jornadas', 'value' => (string) $jornadas],
        ['label' => 'Noticias', 'value' => (string) $noticias],
        ['label' => 'Directos', 'value' => $enVivo > 0 ? $enVivo . ' en vivo' : 'Programados', 'live' => $enVivo > 0]
    ];
    $tiras = '';
    foreach ($estadisticas as $stat) {
        $tiras .= '<li><small>' . e($stat['label']) . '</small><strong'
            . (!empty($stat['live']) ? ' class="is-live"' : '') . '>' . e($stat['value']) . '</strong></li>';
    }

    $lideres = '';
    $primera = $datos['divisions'][0] ?? null;
    if ($primera !== null) {
        foreach (array_slice($tablas[$primera['id']] ?? [], 0, 3) as $fila) {
            $lideres .= '<li><b>' . (int) $fila['position'] . '</b><span>' . e($fila['name']) . '</span><i>'
                . (int) $fila['points'] . ' pts</i></li>';
        }
    }

    $sesion = $usuario
        ? '<p class="hero-note">Sesión de <strong>@' . e($usuario['username']) . '</strong>. Abre la '
            . '<a href="#equipo">tuerca</a> para gestionar tu cuenta.</p>'
        : '<p class="hero-note">¿Quieres seguir la liga de cerca? <a href="/registro">Crea tu cuenta</a> y accede a tu perfil desde la tuerca.</p>';

    $siguiente = $proximo
        ? '<a class="brief-card next-match" href="#fechas">
              <span class="next-label">Próximo partido</span>
              <strong class="next-teams">' . e($proximo['home']) . ' <i>vs</i> ' . e($proximo['away']) . '</strong>
              <span class="next-meta">' . e($proximo['divisionName']) . ' · ' . e(fecha_larga($proximo['date'])) . ' · '
                . e(hora($proximo['time'] ?? '')) . '</span>
            </a>'
        : '<div class="brief-card next-match"><span class="next-label">Calendario</span>'
            . '<strong class="next-teams">Sin partidos programados</strong>'
            . '<span class="next-meta">El staff publicará las próximas fechas</span></div>';

    return '<section class="hero" id="inicio">
  <div class="hero-bg" aria-hidden="true">
    <span class="hero-grid"></span>
    <span class="hero-glow hero-glow-1"></span>
    <span class="hero-glow hero-glow-2"></span>
    <span class="hero-orbit hero-orbit-1" aria-hidden="true"><i></i></span>
    <span class="hero-orbit hero-orbit-2" aria-hidden="true"><i></i></span>
    <span class="hero-orbit hero-orbit-3" aria-hidden="true"><i></i></span>
    <span class="hero-spark" aria-hidden="true"></span>
  </div>

  <div class="shell hero-inner">
    <div class="hero-copy">
      <p class="eyebrow">Liga de HaxBall · ' . e($ajustes['season']) . '</p>
      <div class="hero-emblem">
        <img src="/assets/logo-mark.png" width="164" height="164" alt="" aria-hidden="true" fetchpriority="high" decoding="async">
      </div>
      <h1 class="hero-title"><span>The Diamonds</span><em>League</em></h1>
      <p class="hero-lead">' . e($ajustes['description']) . '</p>
      <div class="hero-actions">
        <a class="btn btn-primary" href="#liga">Ver liga</a>
        <a class="btn btn-outline" href="#fechas">Calendario</a>
        <a class="btn btn-outline" href="#live">Live fútbol</a>
      </div>
      ' . $sesion . '
    </div>
  </div>

  <div class="shell hero-foot">
    <ul class="stat-strip">' . $tiras . '</ul>
    <p class="rooms-note">' . plural($salasAbiertas, 'sala pública abierta', 'salas públicas abiertas') . ' de '
        . count($datos['pubs']) . ' en este momento.</p>

    <div class="hero-brief">
      ' . $siguiente . '
      ' . ($lideres !== ''
          ? '<div class="brief-card hero-leaders">
              <span class="next-label">Cabeza de tabla · ' . e($primera['name']) . '</span>
              <ol>' . $lideres . '</ol>
            </div>'
          : '') . '
    </div>
  </div>

  ' . banda_hero() . '
</section>';
}

/* -------------------------------------------------------------------------
 * Ensamblado
 * ---------------------------------------------------------------------- */
function vista_inicio(array $datos, array $tablas, ?array $usuario, ?array $proximo): string
{
    $contenido = '<a class="skip-link" href="#liga">Saltar al contenido</a>'
        . '<div class="scroll-progress" data-scroll-progress aria-hidden="true"></div>'
        . seccion_hero($datos, $usuario, $proximo, $tablas)
        . cabecera($datos, $usuario, usuario_es_admin($usuario ?? ['is_admin' => 0]))
        . '<main id="contenido">'
        . mapa_modulos()
        . seccion_liga($datos, $tablas)
        . seccion_fechas($datos)
        . seccion_pubs($datos)
        . seccion_museo($datos)
        . seccion_noticias($datos)
        . seccion_anuncios($datos)
        . seccion_alianzas($datos)
        . seccion_redes($datos)
        . seccion_equipo($datos)
        . seccion_live($datos)
        . seccion_donacion($datos)
        . '</main>'
        . pie($datos)
        . '<button class="to-top" type="button" data-to-top aria-label="Volver arriba" hidden>↑</button>'
        . '<div class="lightbox" data-lightbox-box hidden role="dialog" aria-modal="true" aria-label="Imagen ampliada">
  <button type="button" data-lightbox-close aria-label="Cerrar">Cerrar</button>
  <figure>
    <img src="" alt="" data-lightbox-img>
    <figcaption data-lightbox-caption></figcaption>
  </figure>
</div>'
        . '<div class="member-modal" data-member-box hidden role="dialog" aria-modal="true" aria-label="Ficha del equipo">
  <div class="member-modal-card">
    <button class="member-modal-close" type="button" data-member-close aria-label="Cerrar ficha">&times;</button>
    <div class="member-modal-body" data-member-content></div>
  </div>
</div>';

    return layout([
        'datos' => $datos,
        'usuario' => $usuario,
        'title' => $datos['settings']['leagueName'] . ' · ' . $datos['settings']['tagline'],
        'description' => $datos['settings']['description'],
        'canonical' => APP_URL . '/'
    ], $contenido);
}
