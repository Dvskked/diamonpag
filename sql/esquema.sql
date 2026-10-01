-- ============================================================================
--  The Diamonds League · base de datos MySQL / MariaDB
--  neptun / andres / Dvskked — github.com/Dvskked
--  Conserva este aviso de autoría.
--
--  Cómo importarlo (phpMyAdmin, cPanel o consola):
--    1. Crea la base de datos y un usuario con permisos sobre ella.
--    2. Importa este archivo (esquema) y luego sql/datos.sql (contenido).
--    3. Copia .env.example a .env y rellena los datos de conexión.
--
--  Compatible con MySQL 5.7+ / 8.0+ y MariaDB 10.3+.
-- ============================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ---------------------------------------------------------------------------
--  Ajustes generales de la liga (una sola fila, id = 1)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `ajustes` (
  `id`            TINYINT UNSIGNED NOT NULL DEFAULT 1,
  `league_name`   VARCHAR(120) NOT NULL,
  `short_name`    VARCHAR(40)  NOT NULL DEFAULT '',
  `tagline`       VARCHAR(200) NOT NULL DEFAULT '',
  `description`   TEXT         NULL,
  `season`        VARCHAR(60)  NOT NULL DEFAULT '',
  `season_number` SMALLINT UNSIGNED NOT NULL DEFAULT 1,
  `modality`      VARCHAR(120) NOT NULL DEFAULT '',
  `status`        VARCHAR(60)  NOT NULL DEFAULT '',
  `status_note`   VARCHAR(255) NOT NULL DEFAULT '',
  `server`        VARCHAR(120) NOT NULL DEFAULT '',
  `map`           VARCHAR(60)  NOT NULL DEFAULT '',
  `match_duration` VARCHAR(60) NOT NULL DEFAULT '',
  `tolerance`     VARCHAR(60)  NOT NULL DEFAULT '',
  `points_win`    TINYINT UNSIGNED NOT NULL DEFAULT 3,
  `points_draw`   TINYINT UNSIGNED NOT NULL DEFAULT 1,
  `tiktok`        VARCHAR(255) NOT NULL DEFAULT '',
  `tiktok_handle` VARCHAR(120) NOT NULL DEFAULT '',
  `founded`       SMALLINT UNSIGNED NULL,
  `match_config`  TEXT NULL COMMENT 'Pares {label,value} en JSON',
  `donation_note` VARCHAR(255) NOT NULL DEFAULT '',
  `donation_key`  VARCHAR(120) NOT NULL DEFAULT '',
  `donation_goal` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  `updated_at`    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
--  Divisiones (D1, D2, ...)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `divisiones` (
  `id`         VARCHAR(24)  NOT NULL,
  `name`       VARCHAR(80)  NOT NULL,
  `code`       VARCHAR(24)  NOT NULL DEFAULT '',
  `season`     VARCHAR(60)  NOT NULL DEFAULT '',
  `summary`    TEXT NULL,
  `teams`      SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  `journeys`   SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  `playoffs`   VARCHAR(200) NOT NULL DEFAULT '',
  `relegation` VARCHAR(200) NOT NULL DEFAULT '',
  `promotion`  VARCHAR(200) NOT NULL DEFAULT '',
  `phases`     TEXT NULL,
  `movement`   TEXT NULL,
  `rules`      TEXT NULL,
  `sort_order` SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_divisiones_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
--  Equipos
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `equipos` (
  `id`        VARCHAR(40)  NOT NULL,
  `name`      VARCHAR(80)  NOT NULL,
  `division`  VARCHAR(24)  NOT NULL,
  `coach`     VARCHAR(80)  NOT NULL DEFAULT '',
  `colors`    VARCHAR(80)  NOT NULL DEFAULT '',
  `logo`      VARCHAR(300) NOT NULL DEFAULT '',
  `note`      TEXT NULL,
  `sort_order` SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `idx_equipos_division` (`division`),
  CONSTRAINT `fk_equipos_division` FOREIGN KEY (`division`)
    REFERENCES `divisiones` (`id`) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
--  Jugadores (plantillas)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `jugadores` (
  `id` VARCHAR(40) NOT NULL,
  `team_id` VARCHAR(40) NOT NULL,
  `name` VARCHAR(80) NOT NULL,
  `jersey` SMALLINT UNSIGNED NULL,
  `position` VARCHAR(40) NOT NULL DEFAULT 'Delantero',
  `note` VARCHAR(200) NOT NULL DEFAULT '',
  `sort_order` SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `idx_jugadores_team` (`team_id`, `sort_order`),
  CONSTRAINT `fk_jugadores_team` FOREIGN KEY (`team_id`)
    REFERENCES `equipos` (`id`) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
--  Partidos
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `partidos` (
  `id`           VARCHAR(40)  NOT NULL,
  `division`     VARCHAR(24)  NOT NULL,
  `stage`        VARCHAR(40)  NOT NULL DEFAULT 'liga',
  `journey`      TINYINT UNSIGNED NULL DEFAULT NULL,
  `journey_label` VARCHAR(60) NOT NULL DEFAULT '',
  `range`        VARCHAR(40)  NOT NULL DEFAULT '',
  `date`         DATE NULL,
  `time`         TIME NULL,
  `home`         VARCHAR(80)  NOT NULL,
  `away`         VARCHAR(80)  NOT NULL,
  `home_goals`   TINYINT UNSIGNED NULL,
  `away_goals`   TINYINT UNSIGNED NULL,
  `status`       VARCHAR(20)  NOT NULL DEFAULT 'programado',
  `replay`       VARCHAR(60)  NOT NULL DEFAULT '',
  `mvp`          VARCHAR(80)  NOT NULL DEFAULT '',
  `keeper_home`  VARCHAR(80)  NOT NULL DEFAULT '',
  `keeper_away`  VARCHAR(80)  NOT NULL DEFAULT '',
  `notes`        TEXT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_partidos_division` (`division`, `stage`, `journey`),
  KEY `idx_partidos_fecha` (`date`),
  CONSTRAINT `fk_partidos_division` FOREIGN KEY (`division`)
    REFERENCES `divisiones` (`id`) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
--  Goles y asistencias por partido
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `partido_eventos` (
  `id` VARCHAR(40) NOT NULL,
  `match_id` VARCHAR(40) NOT NULL,
  `kind` VARCHAR(20) NOT NULL DEFAULT 'gol',
  `side` VARCHAR(20) NOT NULL DEFAULT 'local',
  `team` VARCHAR(80) NOT NULL DEFAULT '',
  `player` VARCHAR(80) NOT NULL,
  `minute` TINYINT UNSIGNED NULL,
  `sort_order` SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `idx_eventos_partido` (`match_id`, `kind`, `sort_order`),
  CONSTRAINT `fk_eventos_partido` FOREIGN KEY (`match_id`)
    REFERENCES `partidos` (`id`) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
--  Reglamento: reglas + puntos
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `reglas` (
  `id`         VARCHAR(40)  NOT NULL,
  `title`      VARCHAR(120) NOT NULL,
  `summary`    VARCHAR(255) NOT NULL DEFAULT '',
  `sort_order` SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Los tres formatos del reglamento (puntos, bloques y tarjetas) se guardan en la
-- misma tabla hija, distinguidos por `kind`: item · bloque · tarjeta.
CREATE TABLE IF NOT EXISTS `regla_items` (
  `id`         INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `rule_id`    VARCHAR(40) NOT NULL,
  `kind`       VARCHAR(20)  NOT NULL DEFAULT 'item',
  `title`      VARCHAR(160) NOT NULL DEFAULT '',
  `subtitle`   VARCHAR(160) NOT NULL DEFAULT '',
  `kicker`     VARCHAR(60)  NOT NULL DEFAULT '',
  `tone`       VARCHAR(20)  NOT NULL DEFAULT '',
  `text`       TEXT NULL,
  `list`       TEXT NULL COMMENT 'Puntos sueltos en JSON',
  `sort_order` SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `idx_regla_items_rule` (`rule_id`, `sort_order`),
  CONSTRAINT `fk_regla_items_rule` FOREIGN KEY (`rule_id`)
    REFERENCES `reglas` (`id`) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
--  Salas públicas de HaxBall
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `salas` (
  `id`      VARCHAR(40)  NOT NULL,
  `label`   VARCHAR(120) NOT NULL,
  `name`    VARCHAR(80)  NOT NULL DEFAULT '',
  `url`     VARCHAR(255) NOT NULL DEFAULT '',
  `status`  VARCHAR(20)  NOT NULL DEFAULT 'offline',
  `players` TINYINT UNSIGNED NULL DEFAULT NULL,
  `note`    VARCHAR(255) NOT NULL DEFAULT '',
  `sort_order` SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `idx_salas_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
--  Noticias
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `noticias` (
  `id`       VARCHAR(40)  NOT NULL,
  `title`    VARCHAR(160) NOT NULL,
  `category` VARCHAR(60)  NOT NULL DEFAULT '',
  `excerpt`  VARCHAR(300) NOT NULL DEFAULT '',
  `body`     TEXT NULL,
  `date`     DATE NULL,
  `author`   VARCHAR(80)  NOT NULL DEFAULT '',
  `image`    VARCHAR(300) NOT NULL DEFAULT '',
  `pinned`   TINYINT(1)   NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `idx_noticias_fecha` (`date`),
  KEY `idx_noticias_portada` (`pinned`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
--  Anuncios / novedades
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `anuncios` (
  `id`      VARCHAR(40)  NOT NULL,
  `kind`    VARCHAR(40)  NOT NULL DEFAULT 'info',
  `season`  VARCHAR(60)  NOT NULL DEFAULT '',
  `title`   VARCHAR(160) NOT NULL,
  `kicker`  VARCHAR(120) NOT NULL DEFAULT '',
  `date`    DATE NULL,
  `text`    TEXT NULL,
  `bullets` TEXT NULL COMMENT 'Lista de puntos en JSON',
  `closing` VARCHAR(255) NOT NULL DEFAULT '',
  `warning` VARCHAR(255) NOT NULL DEFAULT '',
  `day`     TINYINT UNSIGNED NOT NULL DEFAULT 0,
  `month`   TINYINT UNSIGNED NOT NULL DEFAULT 0,
  `year`    SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `idx_anuncios_fecha` (`date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
--  Museo de premios (antiguos y recientes)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `premios` (
  `id`       VARCHAR(40)  NOT NULL,
  `division` VARCHAR(24)  NOT NULL DEFAULT '',
  `category` VARCHAR(40)  NOT NULL DEFAULT '',
  `season`   VARCHAR(60)  NOT NULL DEFAULT '',
  `title`    VARCHAR(160) NOT NULL,
  `team`     VARCHAR(80)  NOT NULL DEFAULT '',
  `text`     VARCHAR(300) NOT NULL DEFAULT '',
  `image`    VARCHAR(300) NOT NULL DEFAULT '',
  `year`     SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `idx_premios_division` (`division`, `category`),
  KEY `idx_premios_year` (`year`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
--  Equipo de administración y desarrollo
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `personal` (
  `id`        VARCHAR(40)  NOT NULL,
  `name`      VARCHAR(80)  NOT NULL,
  `username`  VARCHAR(80)  NOT NULL DEFAULT '',
  `role`      VARCHAR(40)  NOT NULL DEFAULT 'Staff',
  `bio`       VARCHAR(400) NOT NULL DEFAULT '',
  `avatar`    VARCHAR(300) NOT NULL DEFAULT '',
  `banner`    VARCHAR(300) NOT NULL DEFAULT '',
  `focus`     VARCHAR(120) NOT NULL DEFAULT '',
  `github`    VARCHAR(80)  NOT NULL DEFAULT '',
  `instagram` VARCHAR(80)  NOT NULL DEFAULT '',
  `discord`   VARCHAR(80)  NOT NULL DEFAULT '',
  `available` TINYINT(1)   NOT NULL DEFAULT 0,
  `sort_order` SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  `tags`      TEXT NULL COMMENT 'Etiquetas en JSON',
  PRIMARY KEY (`id`),
  KEY `idx_personal_role` (`role`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
--  Accesos rápidos de la liga (bloque "Importante" del panel)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `destacados` (
  `id`          VARCHAR(40)  NOT NULL,
  `title`       VARCHAR(120) NOT NULL,
  `description` VARCHAR(240) NOT NULL DEFAULT '',
  `kind`        VARCHAR(20)  NOT NULL DEFAULT 'link',
  `href`        VARCHAR(400) NOT NULL DEFAULT '',
  `cta`         VARCHAR(40)  NOT NULL DEFAULT '',
  `sort_order`  SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `idx_destacados_orden` (`sort_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
--  Alianzas y afiliaciones
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `alianzas` (
  `id`          VARCHAR(40)  NOT NULL,
  `name`        VARCHAR(120) NOT NULL,
  `kind`        VARCHAR(40)  NOT NULL DEFAULT 'afiliacion',
  `description` VARCHAR(400) NOT NULL DEFAULT '',
  `href`        VARCHAR(400) NOT NULL DEFAULT '',
  `cta`         VARCHAR(60)  NOT NULL DEFAULT '',
  `image`       VARCHAR(300) NOT NULL DEFAULT '',
  `status`      VARCHAR(20)  NOT NULL DEFAULT 'activa',
  `sort_order`  SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `idx_alianzas_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
--  Redes sociales de la liga y de los streamers
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `redes` (
  `id`          VARCHAR(40)  NOT NULL,
  `network`     VARCHAR(40)  NOT NULL DEFAULT 'instagram',
  `owner_name`  VARCHAR(120) NOT NULL DEFAULT '',
  `handle`      VARCHAR(120) NOT NULL DEFAULT '',
  `url`         VARCHAR(400) NOT NULL DEFAULT '',
  `followers`   INT UNSIGNED NOT NULL DEFAULT 0,
  `is_streamer` TINYINT(1)   NOT NULL DEFAULT 0,
  `sort_order`  SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `idx_redes_network` (`network`),
  KEY `idx_redes_streamer` (`is_streamer`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
--  Directos de fútbol en vivo
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `directos` (
  `id`        VARCHAR(40)  NOT NULL,
  `league`    VARCHAR(120) NOT NULL DEFAULT '',
  `home`      VARCHAR(120) NOT NULL DEFAULT '',
  `away`      VARCHAR(120) NOT NULL DEFAULT '',
  `home_score` VARCHAR(10) NOT NULL DEFAULT '',
  `away_score` VARCHAR(10) NOT NULL DEFAULT '',
  `channel`   VARCHAR(40)  NOT NULL DEFAULT '',
  `platform`  VARCHAR(40)  NOT NULL DEFAULT 'twitch',
  `url`       VARCHAR(400) NOT NULL DEFAULT '',
  `viewer_count` INT UNSIGNED NOT NULL DEFAULT 0,
  `starts_at` DATETIME NULL,
  `is_live`   TINYINT(1)   NOT NULL DEFAULT 0,
  `sort_order` SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `idx_directos_live` (`is_live`, `starts_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
--  Donaciones
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `donaciones` (
  `id`          VARCHAR(40)  NOT NULL,
  `title`       VARCHAR(120) NOT NULL,
  `description` VARCHAR(400) NOT NULL DEFAULT '',
  `kind`        VARCHAR(40)  NOT NULL DEFAULT 'info',
  `amount`      DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  `method`      VARCHAR(60)  NOT NULL DEFAULT '',
  `account`     VARCHAR(120) NOT NULL DEFAULT '',
  `goal`        DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  `raised`      DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  `is_active`   TINYINT(1)   NOT NULL DEFAULT 1,
  `sort_order`  SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `idx_donaciones_activo` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
--  Usuarios registrados
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `usuarios` (
  `id`            INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `username`      VARCHAR(32)  NOT NULL,
  `email`         VARCHAR(190) NOT NULL,
  `password_hash` VARCHAR(255) NOT NULL,
  `display_name`  VARCHAR(80)  NOT NULL DEFAULT '',
  `bio`           VARCHAR(400) NOT NULL DEFAULT '',
  `avatar_url`    VARCHAR(400) NOT NULL DEFAULT '',
  `country`       VARCHAR(60)  NOT NULL DEFAULT '',
  `favorite_team` VARCHAR(80)  NOT NULL DEFAULT '',
  `is_premium`    TINYINT(1)   NOT NULL DEFAULT 0,
  `is_admin`      TINYINT(1)   NOT NULL DEFAULT 0,
  `google_id`     VARCHAR(64)  NULL,
  `terms_accepted_at` DATETIME NULL,
  `newsletter`    TINYINT(1)   NOT NULL DEFAULT 0,
  `last_login_at` DATETIME NULL,
  `created_at`    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_usuarios_username` (`username`),
  UNIQUE KEY `uq_usuarios_email` (`email`),
  UNIQUE KEY `uq_usuarios_google` (`google_id`),
  KEY `idx_usuarios_premium` (`is_premium`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
--  Consentimientos de privacidad y tratamiento de datos
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `consentimientos` (
  `id`         INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id`    INT UNSIGNED NOT NULL,
  `doc_version` VARCHAR(20) NOT NULL DEFAULT '1.0',
  `accepted`   TINYINT(1)   NOT NULL DEFAULT 1,
  `newsletter` TINYINT(1)   NOT NULL DEFAULT 0,
  `ip`         VARCHAR(45)  NOT NULL DEFAULT '',
  `user_agent` VARCHAR(255) NOT NULL DEFAULT '',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_consentimientos_user` (`user_id`, `created_at`),
  CONSTRAINT `fk_consentimientos_user` FOREIGN KEY (`user_id`)
    REFERENCES `usuarios` (`id`) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
--  Intentos de acceso (limitación de fuerza bruta)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `intentos` (
  `id`         INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `scope`      VARCHAR(20)  NOT NULL DEFAULT 'usuario',
  `ip`         VARCHAR(45)  NOT NULL,
  `identifier` VARCHAR(190) NOT NULL DEFAULT '',
  `ok`         TINYINT(1)   NOT NULL DEFAULT 0,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_intentos_lookup` (`scope`, `ip`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
--  Avisos y novedades internas del sitio
-- ---------------------------------------------------------------------------
--  Nota: la tabla `avisos` del PHP original se sustituyó por `anuncios`.

SET FOREIGN_KEY_CHECKS = 1;
