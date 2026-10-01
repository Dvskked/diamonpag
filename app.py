#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
 The Diamonds League — Liga competitiva de HaxBall X5
 neptun / andres / Dvskked — github.com/Dvskked
================================================================================

 Aplicación web en un solo archivo. Ejecuta:

     pip install flask pymysql bcrypt
     python app.py

 Y abre http://localhost:8000 . La base de datos MySQL de CleverCloud se crea
 sola en el primer arranque (esquema + contenido inicial).

 Rutas
 -----
     /entrar            Acceso de usuarios y del panel de administración
     /registro          Alta de cuenta (usuario único, correo único, contraseña
                        y confirmación)
     /                  Portada con las 11 secciones de la liga
     /panel             Panel de administración
     /api/admin/...     API JSON del panel

 Todo el contenido exige una sesión iniciada. Solo el acceso, el registro y la
 política de privacidad son públicos.
"""

from __future__ import annotations

import json
import os
import re
import secrets
import unicodedata
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from functools import wraps
from pathlib import Path

import bcrypt
import pymysql
import urllib.parse
from flask import (
    Flask,
    Response,
    abort,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from jinja2 import DictLoader
from markupsafe import Markup, escape

# ==============================================================================
#  CONFIGURACIÓN
# ==============================================================================

RAIZ = Path(__file__).resolve().parent
ASSETS = RAIZ / "assets"
UPLOADS = RAIZ / "uploads"
SQL_DIR = RAIZ / "sql"
SECRET_FILE = RAIZ / ".secret_key"

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
         "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
MESES_CORTOS = ["ene", "feb", "mar", "abr", "may", "jun",
                "jul", "ago", "sep", "oct", "nov", "dic"]


def cargar_dotenv(ruta: Path) -> None:
    """Carga un .env sencillo sin pisar variables ya definidas."""
    if not ruta.is_file():
        return
    for linea in ruta.read_text(encoding="utf-8", errors="replace").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, _, valor = linea.partition("=")
        clave = clave.strip()
        valor = valor.strip().strip("\"'")
        if clave and clave not in os.environ:
            os.environ[clave] = valor


cargar_dotenv(RAIZ / ".env")


def cfg(clave: str, defecto: str = "") -> str:
    # Una variable presente pero vacía (p. ej. DB_PASSWORD="") se respeta:
    # solo recurrimos al valor por defecto si la variable no existe.
    if clave not in os.environ:
        return defecto
    return os.environ[clave].strip()


def flag(clave: str, defecto: bool = False) -> bool:
    valor = cfg(clave, "")
    if not valor:
        return defecto
    return valor.lower() in {"1", "true", "yes", "on", "si", "sí"}


APP_NOMBRE = cfg("APP_NAME", "The Diamonds League")
APP_URL = cfg("SITE_URL", "http://localhost:8000").rstrip("/")
APP_DEBUG = flag("APP_DEBUG", False)
APP_PUERTO = int(cfg("PORT", "8000"))
APP_HOST = cfg("HOST", "0.0.0.0")

DB_HOST = cfg("DB_HOST", "b6dxqgdzhg4dpauzkxaj-mysql.services.clever-cloud.com")
DB_PUERTO = int(cfg("DB_PORT", "3306"))
DB_NOMBRE = cfg("DB_NAME", "b6dxqgdzhg4dpauzkxaj")
DB_USUARIO = cfg("DB_USER", "uav71aojlkvkkfot")
DB_CLAVE = cfg("DB_PASSWORD", "uav71aojlkvkkfot")

SESION_HORAS = int(cfg("SESSION_HOURS", "12"))
LOGIN_MAX_INTENTOS = int(cfg("LOGIN_MAX_ATTEMPTS", "8"))
LOGIN_BLOQUEO_MIN = int(cfg("LOGIN_LOCK_MINUTES", "10"))

POLITICA_VERSION = cfg("POLICY_VERSION", "1.0")
POLITICA_FECHA = cfg("POLICY_DATE", "2026-10-01")
POLITICA_CONTACTO = cfg("POLICY_CONTACT", "admin@diamondsleague.app")
POLITICA_EMPRESA = cfg("POLICY_OWNER", APP_NOMBRE)

GOOGLE_CLIENT_ID = cfg("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = cfg("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT = cfg("GOOGLE_REDIRECT", APP_URL + "/cuenta/google/callback")

PREMIUM_PERMITE = {"premium"}
ADMIN_PERMITE = {"admin"}
LIMITE_SUBIDA = 4 * 1024 * 1024
FORMATOS_LOGO = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def secreto_sesion() -> str:
    """Secreto estable entre reinicios, para no invalidar las sesiones."""
    clave = cfg("SECRET_KEY", "")
    if clave:
        return clave
    if SECRET_FILE.is_file():
        return SECRET_FILE.read_text(encoding="utf-8").strip()
    nuevo = secrets.token_hex(48)
    try:
        SECRET_FILE.write_text(nuevo, encoding="utf-8")
    except OSError:
        pass
    return nuevo


app = Flask(__name__, static_folder=None)
app.config.update(
    SECRET_KEY=secreto_sesion(),
    SESSION_COOKIE_NAME=cfg("SESSION_NAME", "tdl_sesion"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=flag("SESSION_SECURE", APP_URL.startswith("https://")),
    PERMANENT_SESSION_LIFETIME=timedelta(hours=SESION_HORAS),
    MAX_CONTENT_LENGTH=LIMITE_SUBIDA,
    JSON_SORT_KEYS=False,
    TEMPLATES_AUTO_RELOAD=APP_DEBUG,
)

UPLOADS.mkdir(exist_ok=True)
(UPLOADS / "equipos").mkdir(exist_ok=True)
(UPLOADS / "avatares").mkdir(exist_ok=True)


# ==============================================================================
#  BASE DE DATOS
# ==============================================================================

def conexion() -> pymysql.connections.Connection:
    """Conexión de la petición actual a CleverCloud MySQL."""
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PUERTO,
        user=DB_USUARIO,
        password=DB_CLAVE,
        database=DB_NOMBRE,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        connect_timeout=15,
        read_timeout=30,
        write_timeout=30,
    )


def bd() -> pymysql.connections.Connection:
    if "bd" not in g:
        g.bd = conexion()
    return g.bd


@app.teardown_appcontext
def _cerrar_bd(excepcion=None) -> None:
    conexion_ = g.pop("bd", None)
    if conexion_ is None:
        return
    try:
        if conexion_.open:
            conexion_.close()
    except Exception:  # pragma: no cover - cierre best-effort
        pass


def consultar(sql: str, params: tuple | list = ()) -> list[dict]:
    with bd().cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def fila(sql: str, params: tuple | list = ()) -> dict | None:
    with bd().cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()


def valor(sql: str, params: tuple | list = (), defecto=None):
    with bd().cursor() as cur:
        cur.execute(sql, params)
        fila_ = cur.fetchone()
    if not fila_:
        return defecto
    got = next(iter(fila_.values()), defecto)
    return defecto if got is None else got


def ejecutar(sql: str, params: tuple | list = ()) -> int:
    with bd().cursor() as cur:
        cur.execute(sql, params)
        return cur.rowcount


def ejecutar_varios(sql: str, lista: list[tuple]) -> None:
    if not lista:
        return
    with bd().cursor() as cur:
        cur.executemany(sql, lista)


def confirmar() -> None:
    bd().commit()


def revertir() -> None:
    bd().rollback()


# ==============================================================================
#  ESQUEMA
# ==============================================================================

ESQUEMA = [
    """CREATE TABLE IF NOT EXISTS `ajustes` (
        `id` TINYINT UNSIGNED NOT NULL DEFAULT 1,
        `league_name` VARCHAR(120) NOT NULL,
        `short_name` VARCHAR(40) NOT NULL DEFAULT '',
        `tagline` VARCHAR(200) NOT NULL DEFAULT '',
        `description` TEXT NULL,
        `season` VARCHAR(60) NOT NULL DEFAULT '',
        `season_number` SMALLINT UNSIGNED NOT NULL DEFAULT 1,
        `modality` VARCHAR(120) NOT NULL DEFAULT '',
        `status` VARCHAR(60) NOT NULL DEFAULT '',
        `status_note` VARCHAR(255) NOT NULL DEFAULT '',
        `server` VARCHAR(120) NOT NULL DEFAULT '',
        `map` VARCHAR(60) NOT NULL DEFAULT '',
        `match_duration` VARCHAR(60) NOT NULL DEFAULT '',
        `tolerance` VARCHAR(60) NOT NULL DEFAULT '',
        `points_win` TINYINT UNSIGNED NOT NULL DEFAULT 3,
        `points_draw` TINYINT UNSIGNED NOT NULL DEFAULT 1,
        `tiktok` VARCHAR(255) NOT NULL DEFAULT '',
        `tiktok_handle` VARCHAR(120) NOT NULL DEFAULT '',
        `founded` SMALLINT UNSIGNED NULL,
        `match_config` TEXT NULL,
        `donation_note` VARCHAR(255) NOT NULL DEFAULT '',
        `donation_key` VARCHAR(120) NOT NULL DEFAULT '',
        `donation_goal` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
        `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",

    """CREATE TABLE IF NOT EXISTS `divisiones` (
        `id` VARCHAR(24) NOT NULL,
        `name` VARCHAR(80) NOT NULL,
        `code` VARCHAR(24) NOT NULL DEFAULT '',
        `season` VARCHAR(60) NOT NULL DEFAULT '',
        `summary` TEXT NULL,
        `teams` SMALLINT UNSIGNED NOT NULL DEFAULT 0,
        `journeys` SMALLINT UNSIGNED NOT NULL DEFAULT 0,
        `playoffs` VARCHAR(200) NOT NULL DEFAULT '',
        `relegation` VARCHAR(200) NOT NULL DEFAULT '',
        `promotion` VARCHAR(200) NOT NULL DEFAULT '',
        `phases` TEXT NULL,
        `movement` TEXT NULL,
        `rules` TEXT NULL,
        `sort_order` SMALLINT UNSIGNED NOT NULL DEFAULT 0,
        PRIMARY KEY (`id`), UNIQUE KEY `uq_divisiones_code` (`code`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",

    """CREATE TABLE IF NOT EXISTS `equipos` (
        `id` VARCHAR(40) NOT NULL,
        `name` VARCHAR(80) NOT NULL,
        `division` VARCHAR(24) NOT NULL,
        `coach` VARCHAR(80) NOT NULL DEFAULT '',
        `colors` VARCHAR(80) NOT NULL DEFAULT '',
        `logo` VARCHAR(300) NOT NULL DEFAULT '',
        `note` TEXT NULL,
        `sort_order` SMALLINT UNSIGNED NOT NULL DEFAULT 0,
        PRIMARY KEY (`id`), KEY `idx_equipos_division` (`division`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",

    """CREATE TABLE IF NOT EXISTS `jugadores` (
        `id` VARCHAR(40) NOT NULL,
        `team_id` VARCHAR(40) NOT NULL,
        `name` VARCHAR(80) NOT NULL,
        `jersey` SMALLINT UNSIGNED NULL,
        `position` VARCHAR(40) NOT NULL DEFAULT 'Delantero',
        `note` VARCHAR(200) NOT NULL DEFAULT '',
        `sort_order` SMALLINT UNSIGNED NOT NULL DEFAULT 0,
        PRIMARY KEY (`id`), KEY `idx_jugadores_team` (`team_id`, `sort_order`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",

    """CREATE TABLE IF NOT EXISTS `partidos` (
        `id` VARCHAR(40) NOT NULL,
        `division` VARCHAR(24) NOT NULL,
        `stage` VARCHAR(40) NOT NULL DEFAULT 'liga',
        `journey` TINYINT UNSIGNED NULL DEFAULT NULL,
        `journey_label` VARCHAR(60) NOT NULL DEFAULT '',
        `range` VARCHAR(40) NOT NULL DEFAULT '',
        `date` DATE NULL,
        `time` TIME NULL,
        `home` VARCHAR(80) NOT NULL,
        `away` VARCHAR(80) NOT NULL,
        `home_goals` TINYINT UNSIGNED NULL,
        `away_goals` TINYINT UNSIGNED NULL,
        `status` VARCHAR(20) NOT NULL DEFAULT 'programado',
        `mvp` VARCHAR(80) NOT NULL DEFAULT '',
        `keeper_home` VARCHAR(80) NOT NULL DEFAULT '',
        `keeper_away` VARCHAR(80) NOT NULL DEFAULT '',
        `replay` VARCHAR(60) NOT NULL DEFAULT '',
        `notes` TEXT NULL,
        PRIMARY KEY (`id`),
        KEY `idx_partidos_division` (`division`,`stage`,`journey`),
        KEY `idx_partidos_fecha` (`date`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",

    """CREATE TABLE IF NOT EXISTS `partido_eventos` (
        `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
        `match_id` VARCHAR(40) NOT NULL,
        `kind` VARCHAR(20) NOT NULL DEFAULT 'gol',
        `side` VARCHAR(20) NOT NULL DEFAULT 'local',
        `team` VARCHAR(80) NOT NULL DEFAULT '',
        `player` VARCHAR(80) NOT NULL DEFAULT '',
        `minute` TINYINT UNSIGNED NULL,
        `sort_order` SMALLINT UNSIGNED NOT NULL DEFAULT 0,
        PRIMARY KEY (`id`), KEY `idx_eventos_match` (`match_id`,`sort_order`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",

    """CREATE TABLE IF NOT EXISTS `reglas` (
        `id` VARCHAR(40) NOT NULL,
        `title` VARCHAR(120) NOT NULL,
        `summary` VARCHAR(255) NOT NULL DEFAULT '',
        `sort_order` SMALLINT UNSIGNED NOT NULL DEFAULT 0,
        PRIMARY KEY (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",

    """CREATE TABLE IF NOT EXISTS `regla_items` (
        `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
        `rule_id` VARCHAR(40) NOT NULL,
        `kind` VARCHAR(20) NOT NULL DEFAULT 'item',
        `title` VARCHAR(160) NOT NULL DEFAULT '',
        `subtitle` VARCHAR(160) NOT NULL DEFAULT '',
        `kicker` VARCHAR(60) NOT NULL DEFAULT '',
        `tone` VARCHAR(20) NOT NULL DEFAULT '',
        `text` TEXT NULL,
        `list` TEXT NULL,
        `sort_order` SMALLINT UNSIGNED NOT NULL DEFAULT 0,
        PRIMARY KEY (`id`), KEY `idx_regla_items_rule` (`rule_id`,`sort_order`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",

    """CREATE TABLE IF NOT EXISTS `salas` (
        `id` VARCHAR(40) NOT NULL,
        `label` VARCHAR(120) NOT NULL,
        `name` VARCHAR(80) NOT NULL DEFAULT '',
        `url` VARCHAR(255) NOT NULL DEFAULT '',
        `status` VARCHAR(20) NOT NULL DEFAULT 'offline',
        `players` TINYINT UNSIGNED NULL DEFAULT NULL,
        `note` VARCHAR(255) NOT NULL DEFAULT '',
        `sort_order` SMALLINT UNSIGNED NOT NULL DEFAULT 0,
        PRIMARY KEY (`id`), KEY `idx_salas_status` (`status`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",

    """CREATE TABLE IF NOT EXISTS `noticias` (
        `id` VARCHAR(40) NOT NULL,
        `title` VARCHAR(160) NOT NULL,
        `category` VARCHAR(60) NOT NULL DEFAULT '',
        `excerpt` VARCHAR(300) NOT NULL DEFAULT '',
        `body` TEXT NULL,
        `date` DATE NULL,
        `author` VARCHAR(80) NOT NULL DEFAULT '',
        `image` VARCHAR(300) NOT NULL DEFAULT '',
        `pinned` TINYINT(1) NOT NULL DEFAULT 0,
        PRIMARY KEY (`id`), KEY `idx_noticias_fecha` (`date`), KEY `idx_noticias_portada` (`pinned`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",

    """CREATE TABLE IF NOT EXISTS `anuncios` (
        `id` VARCHAR(40) NOT NULL,
        `kind` VARCHAR(40) NOT NULL DEFAULT 'info',
        `season` VARCHAR(60) NOT NULL DEFAULT '',
        `title` VARCHAR(160) NOT NULL,
        `kicker` VARCHAR(120) NOT NULL DEFAULT '',
        `date` DATE NULL,
        `text` TEXT NULL,
        `bullets` TEXT NULL,
        `closing` VARCHAR(255) NOT NULL DEFAULT '',
        `warning` VARCHAR(255) NOT NULL DEFAULT '',
        `day` TINYINT UNSIGNED NOT NULL DEFAULT 0,
        `month` TINYINT UNSIGNED NOT NULL DEFAULT 0,
        `year` SMALLINT UNSIGNED NOT NULL DEFAULT 0,
        PRIMARY KEY (`id`), KEY `idx_anuncios_fecha` (`date`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",

    """CREATE TABLE IF NOT EXISTS `premios` (
        `id` VARCHAR(40) NOT NULL,
        `division` VARCHAR(24) NOT NULL DEFAULT '',
        `category` VARCHAR(40) NOT NULL DEFAULT '',
        `season` VARCHAR(60) NOT NULL DEFAULT '',
        `title` VARCHAR(160) NOT NULL,
        `team` VARCHAR(80) NOT NULL DEFAULT '',
        `text` VARCHAR(300) NOT NULL DEFAULT '',
        `image` VARCHAR(300) NOT NULL DEFAULT '',
        `year` SMALLINT UNSIGNED NOT NULL DEFAULT 0,
        PRIMARY KEY (`id`),
        KEY `idx_premios_division` (`division`,`category`), KEY `idx_premios_year` (`year`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",

    """CREATE TABLE IF NOT EXISTS `personal` (
        `id` VARCHAR(40) NOT NULL,
        `name` VARCHAR(80) NOT NULL,
        `username` VARCHAR(80) NOT NULL DEFAULT '',
        `role` VARCHAR(40) NOT NULL DEFAULT 'Staff',
        `bio` VARCHAR(400) NOT NULL DEFAULT '',
        `avatar` VARCHAR(300) NOT NULL DEFAULT '',
        `banner` VARCHAR(300) NOT NULL DEFAULT '',
        `focus` VARCHAR(120) NOT NULL DEFAULT '',
        `github` VARCHAR(80) NOT NULL DEFAULT '',
        `instagram` VARCHAR(80) NOT NULL DEFAULT '',
        `discord` VARCHAR(80) NOT NULL DEFAULT '',
        `available` TINYINT(1) NOT NULL DEFAULT 0,
        `tags` TEXT NULL,
        `sort_order` SMALLINT UNSIGNED NOT NULL DEFAULT 0,
        PRIMARY KEY (`id`), KEY `idx_personal_role` (`role`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",

    """CREATE TABLE IF NOT EXISTS `destacados` (
        `id` VARCHAR(40) NOT NULL,
        `title` VARCHAR(120) NOT NULL,
        `description` VARCHAR(240) NOT NULL DEFAULT '',
        `kind` VARCHAR(20) NOT NULL DEFAULT 'link',
        `href` VARCHAR(400) NOT NULL DEFAULT '',
        `cta` VARCHAR(40) NOT NULL DEFAULT '',
        `sort_order` SMALLINT UNSIGNED NOT NULL DEFAULT 0,
        PRIMARY KEY (`id`), KEY `idx_destacados_orden` (`sort_order`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",

    """CREATE TABLE IF NOT EXISTS `alianzas` (
        `id` VARCHAR(40) NOT NULL,
        `name` VARCHAR(120) NOT NULL,
        `kind` VARCHAR(40) NOT NULL DEFAULT 'afiliacion',
        `description` VARCHAR(400) NOT NULL DEFAULT '',
        `href` VARCHAR(400) NOT NULL DEFAULT '',
        `cta` VARCHAR(60) NOT NULL DEFAULT '',
        `image` VARCHAR(300) NOT NULL DEFAULT '',
        `status` VARCHAR(20) NOT NULL DEFAULT 'activa',
        `sort_order` SMALLINT UNSIGNED NOT NULL DEFAULT 0,
        PRIMARY KEY (`id`), KEY `idx_alianzas_status` (`status`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",

    """CREATE TABLE IF NOT EXISTS `redes` (
        `id` VARCHAR(40) NOT NULL,
        `network` VARCHAR(40) NOT NULL DEFAULT 'instagram',
        `owner_name` VARCHAR(120) NOT NULL DEFAULT '',
        `handle` VARCHAR(120) NOT NULL DEFAULT '',
        `url` VARCHAR(400) NOT NULL DEFAULT '',
        `followers` INT UNSIGNED NOT NULL DEFAULT 0,
        `is_streamer` TINYINT(1) NOT NULL DEFAULT 0,
        `sort_order` SMALLINT UNSIGNED NOT NULL DEFAULT 0,
        PRIMARY KEY (`id`),
        KEY `idx_redes_network` (`network`), KEY `idx_redes_streamer` (`is_streamer`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",

    """CREATE TABLE IF NOT EXISTS `directos` (
        `id` VARCHAR(40) NOT NULL,
        `league` VARCHAR(120) NOT NULL DEFAULT '',
        `home` VARCHAR(120) NOT NULL DEFAULT '',
        `away` VARCHAR(120) NOT NULL DEFAULT '',
        `home_score` VARCHAR(10) NOT NULL DEFAULT '',
        `away_score` VARCHAR(10) NOT NULL DEFAULT '',
        `channel` VARCHAR(40) NOT NULL DEFAULT '',
        `platform` VARCHAR(40) NOT NULL DEFAULT 'twitch',
        `url` VARCHAR(400) NOT NULL DEFAULT '',
        `viewer_count` INT UNSIGNED NOT NULL DEFAULT 0,
        `starts_at` DATETIME NULL,
        `is_live` TINYINT(1) NOT NULL DEFAULT 0,
        `sort_order` SMALLINT UNSIGNED NOT NULL DEFAULT 0,
        PRIMARY KEY (`id`), KEY `idx_directos_live` (`is_live`,`starts_at`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",

    """CREATE TABLE IF NOT EXISTS `donaciones` (
        `id` VARCHAR(40) NOT NULL,
        `title` VARCHAR(120) NOT NULL,
        `description` VARCHAR(400) NOT NULL DEFAULT '',
        `kind` VARCHAR(40) NOT NULL DEFAULT 'info',
        `amount` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
        `method` VARCHAR(60) NOT NULL DEFAULT '',
        `account` VARCHAR(120) NOT NULL DEFAULT '',
        `goal` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
        `raised` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
        `is_active` TINYINT(1) NOT NULL DEFAULT 1,
        `sort_order` SMALLINT UNSIGNED NOT NULL DEFAULT 0,
        PRIMARY KEY (`id`), KEY `idx_donaciones_activo` (`is_active`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",

    """CREATE TABLE IF NOT EXISTS `usuarios` (
        `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
        `username` VARCHAR(32) NOT NULL,
        `email` VARCHAR(190) NOT NULL,
        `password_hash` VARCHAR(255) NOT NULL,
        `display_name` VARCHAR(80) NOT NULL DEFAULT '',
        `bio` VARCHAR(400) NOT NULL DEFAULT '',
        `avatar_url` VARCHAR(400) NOT NULL DEFAULT '',
        `country` VARCHAR(60) NOT NULL DEFAULT '',
        `favorite_team` VARCHAR(80) NOT NULL DEFAULT '',
        `is_premium` TINYINT(1) NOT NULL DEFAULT 0,
        `is_admin` TINYINT(1) NOT NULL DEFAULT 0,
        `google_id` VARCHAR(64) NULL,
        `terms_accepted_at` DATETIME NULL,
        `newsletter` TINYINT(1) NOT NULL DEFAULT 0,
        `last_login_at` DATETIME NULL,
        `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (`id`),
        UNIQUE KEY `uq_usuarios_username` (`username`),
        UNIQUE KEY `uq_usuarios_email` (`email`),
        UNIQUE KEY `uq_usuarios_google` (`google_id`),
        KEY `idx_usuarios_premium` (`is_premium`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",

    """CREATE TABLE IF NOT EXISTS `consentimientos` (
        `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
        `user_id` INT UNSIGNED NOT NULL,
        `doc_version` VARCHAR(20) NOT NULL DEFAULT '1.0',
        `accepted` TINYINT(1) NOT NULL DEFAULT 1,
        `newsletter` TINYINT(1) NOT NULL DEFAULT 0,
        `ip` VARCHAR(45) NOT NULL DEFAULT '',
        `user_agent` VARCHAR(255) NOT NULL DEFAULT '',
        `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (`id`), KEY `idx_consentimientos_user` (`user_id`,`created_at`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",

    """CREATE TABLE IF NOT EXISTS `intentos` (
        `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
        `scope` VARCHAR(20) NOT NULL DEFAULT 'usuario',
        `ip` VARCHAR(45) NOT NULL,
        `identifier` VARCHAR(190) NOT NULL DEFAULT '',
        `ok` TINYINT(1) NOT NULL DEFAULT 0,
        `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (`id`), KEY `idx_intentos_lookup` (`scope`,`ip`,`created_at`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
]

# Columnas añadidas a tablas que ya existían en el proyecto original.
MIGRACIONES = [
    ("equipos", "ALTER TABLE `equipos` ADD COLUMN `logo` VARCHAR(300) NOT NULL DEFAULT ''"),
    ("partidos", "ALTER TABLE `partidos` ADD COLUMN `mvp` VARCHAR(80) NOT NULL DEFAULT ''"),
    ("partidos", "ALTER TABLE `partidos` ADD COLUMN `keeper_home` VARCHAR(80) NOT NULL DEFAULT ''"),
    ("partidos", "ALTER TABLE `partidos` ADD COLUMN `keeper_away` VARCHAR(80) NOT NULL DEFAULT ''"),
    ("salas", "ALTER TABLE `salas` ADD COLUMN `sort_order` SMALLINT UNSIGNED NOT NULL DEFAULT 0"),
    ("personal", "ALTER TABLE `personal` ADD COLUMN `sort_order` SMALLINT UNSIGNED NOT NULL DEFAULT 0"),
]


def columna_existe(tabla: str, columna: str) -> bool:
    return bool(valor(
        "SELECT COUNT(*) AS n FROM information_schema.COLUMNS"
        " WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND COLUMN_NAME = %s",
        (DB_NOMBRE, tabla, columna), 0,
    ))


def instalar_esquema() -> None:
    """Crea las tablas que falten y aplica las columnas nuevas."""
    for sentencia in ESQUEMA:
        ejecutar(sentencia)
    for tabla, sentencia in MIGRACIONES:
        columna_ = sentencia.split("`")[3]
        if not columna_existe(tabla, columna_):
            try:
                ejecutar(sentencia)
            except pymysql.err.OperationalError:
                pass
    confirmar()


def separar_sql(crudo: str) -> list:
    """Parte un volcado SQL en sentencias, respetando comillas y comentarios.

    sql/datos.sql trae comentarios al final de línea (';' -- nota), así que
   quitarlos con una expresión regular no basta: hay que ir carácter a carácter
    para no partir dentro de un texto entre comillas.
    """
    sentencias: list = []
    actual: list = []
    comilla = ""
    i, largo = 0, len(crudo)
    while i < largo:
        caracter = crudo[i]
        siguiente = crudo[i + 1] if i + 1 < largo else ""
        if comilla:
            actual.append(caracter)
            if caracter == "\\" and siguiente:
                actual.append(siguiente)
                i += 2
                continue
            if caracter == comilla:
                comilla = ""
            i += 1
            continue
        if caracter in ("'", '"', "`"):
            comilla = caracter
            actual.append(caracter)
            i += 1
            continue
        if caracter == "-" and siguiente == "-":
            while i < largo and crudo[i] != "\n":
                i += 1
            continue
        if caracter == "#":
            while i < largo and crudo[i] != "\n":
                i += 1
            continue
        if caracter == "/" and siguiente == "*":
            i += 2
            while i + 1 < largo and not (crudo[i] == "*" and crudo[i + 1] == "/"):
                i += 1
            i += 2
            continue
        if caracter == ";":
            texto = "".join(actual).strip()
            if texto:
                sentencias.append(texto)
            actual = []
            i += 1
            continue
        actual.append(caracter)
        i += 1
    texto = "".join(actual).strip()
    if texto:
        sentencias.append(texto)
    return sentencias


def cargar_semilla() -> int:
    """Carga sql/datos.sql la primera vez, para no empezar con la liga vacía."""
    if valor("SELECT COUNT(*) AS n FROM `ajustes`", (), 0):
        return 0
    archivo = SQL_DIR / "datos.sql"
    if not archivo.is_file():
        ejecutar("INSERT INTO `ajustes` (`id`,`league_name`,`short_name`,`tagline`)"
                 " VALUES (1,%s,%s,%s)", (APP_NOMBRE, "TDL", "Liga de HaxBall"))
        for division in (("d1", "División 1", "D1"), ("d2", "División 2", "D2")):
            ejecutar("INSERT INTO `divisiones` (`id`,`name`,`code`,`summary`)"
                     " VALUES (%s,%s,%s,%s) ON DUPLICATE KEY UPDATE `name`=VALUES(`name`)",
                     (division[0], division[1], division[2], "División de la liga"))
        confirmar()
        return 2

    crudo = archivo.read_text(encoding="utf-8", errors="replace")
    sentencias = 0
    try:
        with bd().cursor() as cur:
            cur.execute("SET FOREIGN_KEY_CHECKS = 0")
            for tabla in ("anuncios", "noticias", "premios", "destacados", "alianzas",
                          "redes", "directos", "donaciones", "salas", "personal",
                          "regla_items", "reglas", "partido_eventos", "jugadores",
                          "partidos", "equipos", "divisiones", "ajustes"):
                cur.execute(f"TRUNCATE TABLE `{tabla}`")
            cur.execute("SET FOREIGN_KEY_CHECKS = 1")
            for sentencia in separar_sql(crudo):
                if not re.match(r"^(INSERT|REPLACE|UPDATE)\b", sentencia, re.IGNORECASE):
                    continue
                cur.execute(sentencia)
                sentencias += 1
        confirmar()
    except Exception as error:  # pragma: no cover - deja la base utilizable
        revertir()
        app.logger.warning("No se pudo cargar sql/datos.sql: %s", error)
        return 0
    return sentencias


# ==============================================================================
#  FUNCIONES DE APOYO
# ==============================================================================

RE_EMAIL = re.compile(r"^[^@\s]+@[^@\s.]+(\.[^@\s.]+)+$")
RE_USUARIO = re.compile(r"^[a-z0-9_.-]{3,32}$")
RE_ID = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")
RE_URL = re.compile(r"^https?://[^\s\"'<>]+$", re.IGNORECASE)


def e(valor) -> Markup:
    """Escapa texto para HTML."""
    return escape("" if valor is None else str(valor))


def texto_corto(valor, maximo: int = 140, sufijo: str = "…") -> str:
    texto = re.sub(r"\s+", " ", "" if valor is None else str(valor)).strip()
    if not texto or len(texto) <= maximo:
        return texto
    corte = texto[:maximo]
    espacio = corte.rfind(" ")
    if espacio > maximo * 0.6:
        corte = corte[:espacio]
    return corte.rstrip(" ,.;:") + sufijo


def a_fecha(valor):
    """Convierte a date; devuelve None si no es una fecha válida."""
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    texto = str(valor or "").strip()[:10]
    try:
        return datetime.strptime(texto, "%Y-%m-%d").date()
    except ValueError:
        return None


def a_datetime(valor):
    if isinstance(valor, datetime):
        return valor
    texto = str(valor or "").strip().replace("T", " ")
    for patron in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(texto, patron)
        except ValueError:
            continue
    return None


def fecha_larga(valor) -> str:
    f = a_fecha(valor)
    return f"{f.day} de {MESES[f.month - 1]} de {f.year}" if f else ""


def fecha_corta(valor) -> str:
    f = a_fecha(valor)
    return f"{f.day} {MESES_CORTOS[f.month - 1]}" if f else ""


def fecha_hora(valor) -> str:
    momento = a_datetime(valor)
    if momento is None:
        return ""
    return f"{fecha_larga(momento)} · {momento.strftime('%H:%M')}"


def hora(valor) -> str:
    texto = str(valor or "")
    return texto[:5] if re.match(r"^\d{2}:\d{2}", texto) else ""


def estado_texto(estado: str) -> str:
    return {
        "programado": "Programado", "en-vivo": "En vivo", "finalizado": "Finalizado",
        "wo": "W.O.", "pospuesto": "Pospuesto", "por-definir": "Por definir",
    }.get(estado, str(estado or "").replace("-", " ").capitalize())


def fase_texto(fase: str) -> str:
    return {"liga": "Liga regular", "playoffs": "Playoffs"}.get(fase, str(fase or "").capitalize())


def plural(cantidad: int, singular: str, many: str) -> str:
    return singular if cantidad == 1 else many


def json_seguro(texto, por_defecto=None):
    if isinstance(texto, (list, dict)):
        return texto
    if not texto:
        return [] if por_defecto is None else por_defecto
    try:
        datos = json.loads(texto)
    except (ValueError, TypeError):
        return [] if por_defecto is None else por_defecto
    if datos is None:
        return [] if por_defecto is None else por_defecto
    return datos


def json_texto(datos) -> str:
    return json.dumps(datos, ensure_ascii=False)


def usuario_normalizado(valor) -> str:
    valor = unicodedata.normalize("NFKD", str(valor or ""))
    valor = "".join(c for c in valor if not unicodedata.combining(c))
    valor = valor.lower().strip().lstrip("@")
    valor = re.sub(r"[^a-z0-9_.-]+", "", valor)
    return valor[:32]


def sin_acentos(valor) -> str:
    valor = unicodedata.normalize("NFKD", str(valor or ""))
    return "".join(c for c in valor if not unicodedata.combining(c)).lower()


def buscar_normalizado(valor) -> str:
    return re.sub(r"\s+", " ", sin_acentos(valor)).strip()


def ip_cliente() -> str:
    wx = request.headers.get("X-Forwarded-For", "") if request else ""
    return (wx.split(",")[0].strip() if wx else (request.remote_addr or "0.0.0.0"))[:45]


def agente_cliente() -> str:
    return (request.headers.get("User-Agent", "") or "")[:255]


def a_entero(valor, defecto=None):
    if valor is None or valor == "":
        return defecto
    try:
        return int(float(str(valor).strip()))
    except (ValueError, TypeError):
        return defecto


def a_decimal(valor, defecto=None):
    if valor is None or valor == "":
        return defecto
    try:
        return float(Decimal(str(valor).strip()))
    except (InvalidOperation, ValueError, TypeError):
        return defecto


def a_bool(valor) -> bool:
    if isinstance(valor, bool):
        return valor
    return str(valor or "").strip().lower() in {"1", "true", "on", "yes", "si", "sí"}


def fecha_valida(valor) -> str:
    texto = str(valor or "").strip()[:10]
    return texto if a_fecha(texto) else ""


def hora_valida(valor) -> str:
    texto = str(valor or "").strip()
    return texto if re.match(r"^([01]\d|2[0-3]):([0-5]\d)(:[0-5]\d)?$", texto) else ""


def datetime_valido(valor) -> str:
    momento = a_datetime(valor)
    return momento.strftime("%Y-%m-%d %H:%M:%S") if momento else ""


def str_corta(valor, maximo: int = 400) -> str:
    return str(valor or "").strip()[:maximo]


def url_segura(valor) -> str:
    texto = str(valor or "").strip()
    return texto if RE_URL.match(texto) else ""


def ruta_segura(valor, maximo: int = 300) -> str:
    texto = str_corta(valor, maximo)
    if not texto:
        return ""
    if url_segura(texto):
        return texto
    return texto if texto.startswith("/uploads/") else ""


def enlace_seguro(valor, maximo: int = 300) -> str:
    texto = str_corta(valor, maximo)
    if not texto:
        return ""
    if texto.startswith("#"):
        return texto if re.match(r"^#[a-zA-Z0-9\-]{1,60}$", texto) else ""
    if texto.startswith("/") and not texto.startswith("//"):
        return texto if re.match(r"^/[a-zA-Z0-9\-/_.]{0,200}$", texto) else ""
    return url_segura(texto)


def sanear_lista(valor, maximo: int = 400) -> list:
    """Lista de textos cortos (etiquetas, puntos, bullets)."""
    if isinstance(valor, str):
        texto = valor.strip()
        if not texto:
            return []
        if "[" in texto:
            texto = texto[texto.index("["):]
        try:
            valor = json.loads(texto)
        except ValueError:
            return []
    if not isinstance(valor, list):
        return []
    limpia = []
    for item in valor:
        if isinstance(item, dict):
            item = item.get("title", "")
        texto = str_corta(item, maximo or 60)
        if texto:
            limpia.append(texto)
        if len(limpia) >= 12:
            break
    return limpia


def sanear_objetos(valor, esquema: dict, maximo: int = 12) -> list:
    """Lista de objetos con un esquema fijo ({label, value}, fases, etc.)."""
    if isinstance(valor, str):
        try:
            valor = json.loads(valor or "[]")
        except ValueError:
            valor = []
    if not isinstance(valor, list):
        return []
    limpia = []
    for item in valor:
        if not isinstance(item, dict):
            continue
        limpia.append({clave: str_corta(item.get(clave, ""), limite) for clave, limite in esquema.items()})
        if len(limpia) >= maximo:
            break
    return limpia


def sanear_movimiento(valor) -> dict:
    """Ascensos y descensos: {title, items:[{place,label,text}]}."""
    if isinstance(valor, str):
        try:
            valor = json.loads(valor or "{}")
        except ValueError:
            valor = {}
    if not isinstance(valor, dict):
        valor = {"title": "", "items": valor if isinstance(valor, list) else []}
    crudos = valor.get("items")
    if not isinstance(crudos, list):
        crudos = [valor]
    items = []
    for item in crudos:
        if isinstance(item, str):
            item = {"place": "", "label": item}
        if not isinstance(item, dict):
            continue
        items.append({
            "place": str_corta(item.get("place", ""), 60),
            "label": str_corta(item.get("label", ""), 120),
            "text": str_corta(item.get("text", ""), 400),
        })
        if len(items) >= 12:
            break
    return {"title": str_corta(valor.get("title", ""), 120), "items": items}


def nuevo_id(prefijo: str, largo: int = 6) -> str:
    return f"{prefijo}-{secrets.token_hex(8)[:largo]}"


def id_valido(valor) -> bool:
    return bool(RE_ID.match(str(valor or "")))


def wants_json() -> bool:
    if request.path.startswith("/api/"):
        return True
    acepta = request.headers.get("Accept", "")
    return "application/json" in acepta or request.headers.get("X-Requested-With", "").startswith("fetch")


def es_externo(url: str) -> bool:
    return bool(RE_URL.match(str(url or "")))


def numero(valor, decimales: int = 0) -> str:
    """Formato español: 1.234,5"""
    try:
        cantidad = float(valor or 0)
    except (ValueError, TypeError):
        cantidad = 0.0
    entero, _, frac = f"{cantidad:.{decimales}f}".partition(".")
    entero = f"{int(entero):,}".replace(",", ".")
    return f"{entero},{frac}" if frac else entero


# ==============================================================================
#  SESIÓN, CSRF Y ACCESO
# ==============================================================================

def csrf_token() -> str:
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_urlsafe(32)
    return session["_csrf"]


def csrf_valido(token=None) -> bool:
    if token is None:
        token = request.form.get("csrf") or request.headers.get("X-CSRF-Token", "")
    guardado = session.get("_csrf", "")
    return bool(guardado) and secrets.compare_digest(str(guardado), str(token or ""))


def csrf_campo() -> Markup:
    return Markup(f'<input type="hidden" name="csrf" value="{e(csrf_token())}">')


def csrf_exigir() -> None:
    if csrf_valido():
        return
    raise SesionCaducada()


def ip_bloqueada(scope: str = "usuario") -> bool:
    fallos = valor(
        f"SELECT COUNT(*) AS n FROM `intentos` WHERE `scope` = %s AND `ip` = %s"
        f" AND `ok` = 0 AND `created_at` > (NOW() - INTERVAL {LOGIN_BLOQUEO_MIN} MINUTE)",
        (scope, ip_cliente()), 0,
    )
    return int(fallos or 0) >= LOGIN_MAX_INTENTOS


def registrar_intento(scope: str, identificador: str, ok: bool) -> None:
    ejecutar(
        "INSERT INTO `intentos` (`scope`,`ip`,`identifier`,`ok`) VALUES (%s,%s,%s,%s)",
        (scope, ip_cliente(), str_corta(identificador, 190), 1 if ok else 0),
    )
    if ok:
        ejecutar("DELETE FROM `intentos` WHERE `scope` = %s AND `ip` = %s AND `ok` = 0",
                 (scope, ip_cliente()))
    confirmar()


CAMBIOS_SENSIBLES = {"password_hash", "email", "username", "is_admin", "is_premium", "google_id"}


def usuario_actual() -> dict | None:
    id_ = session.get("uid")
    if not id_:
        return None
    registro = fila(
        "SELECT id, username, email, display_name, bio, avatar_url, country,"
        " favorite_team, is_premium, is_admin, google_id, newsletter,"
        " created_at, last_login_at, password_hash FROM `usuarios` WHERE `id` = %s",
        (id_,),
    )
    if registro is None:
        session.pop("uid", None)
        return None
    registro["id"] = int(registro["id"])
    registro["is_premium"] = bool(registro["is_premium"])
    registro["is_admin"] = bool(registro["is_admin"])
    registro["tiene_password"] = bool(registro.get("password_hash"))
    registro["password_hash"] = "" if registro["tiene_password"] else ""
    return registro


def usuario_logueado() -> bool:
    return usuario_actual() is not None


def usuario_exigir() -> dict:
    usuario = usuario_actual()
    if usuario is None:
        if wants_json():
            abort(401, description="Necesitas iniciar sesión.")
        return redirect(url_for("entrar", volver=request.full_path.rstrip("?")))
    return usuario


def admin_exigir() -> dict:
    usuario = usuario_exigir()
    if isinstance(usuario, Response):
        # usuario_exigir() ya redirigió o abortó la petición.
        return usuario
    if not usuario["is_admin"]:
        if wants_json():
            abort(403, description="Esta zona es solo para la administración.")
        abort(403)
    return usuario


def requiere_login(vista):
    @wraps(vista)
    def envoltorio(*args, **kwargs):
        resultado = usuario_exigir()
        if isinstance(resultado, Response):
            return resultado
        return vista(*args, **kwargs)
    return envoltorio


def requiere_admin(vista):
    @wraps(vista)
    def envoltorio(*args, **kwargs):
        resultado = admin_exigir()
        if isinstance(resultado, Response):
            return resultado
        return vista(*args, **kwargs)
    return envoltorio


def requiere_csrf(vista):
    @wraps(vista)
    def envoltorio(*args, **kwargs):
        csrf_exigir()
        return vista(*args, **kwargs)
    return envoltorio


def cuerpo() -> dict:
    """Cuerpo JSON o formulario, indistinto."""
    if request.is_json:
        try:
            datos = request.get_json(silent=True)
        except ValueError:
            datos = None
        if isinstance(datos, dict):
            return datos
    return {clave: request.form.get(clave) for clave in request.form}


def cuerpo_archivos() -> dict:
    """Como cuerpo(), pero incluye los ficheros subidos."""
    datos = cuerpo()
    for clave in request.files:
        datos[clave] = request.files[clave]
    return datos


# ==============================================================================
#  CONTRASEÑAS
# ==============================================================================

def hash_contrasena(contrasena: str) -> str:
    return bcrypt.hashpw(contrasena.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")


def verificar_contrasena(contrasena: str, guardado: str) -> bool:
    if not contrasena or not guardado:
        return False
    try:
        return bcrypt.checkpw(contrasena.encode("utf-8")[:72], guardado.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# Valores señuelo para que el tiempo de respuesta no delate si el usuario existe.
SEÑUELO = "$2y$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy"


def validar_registro(usuario: str, email: str, contrasena: str, confirmar_pw: str,
                     acepta: bool, boletin: bool) -> tuple[dict | None, list[str]]:
    """Crea la cuenta. Devuelve (usuario, errores); si hay errores, usuario es None."""
    errores: list[str] = []
    usuario = usuario_normalizado(usuario)
    email = str(email or "").strip().lower()

    if not RE_USUARIO.match(usuario):
        errores.append("El usuario debe tener entre 3 y 32 caracteres, "
                       "solo letras, números, punto, guion y guion bajo.")
    if not RE_EMAIL.match(email) or len(email) > 190:
        errores.append("Escribe un correo electrónico válido.")
    if len(contrasena or "") < 8:
        errores.append("La contraseña debe tener al menos 8 caracteres.")
    if not contrasena or contrasena != confirmar_pw:
        errores.append("Las contraseñas no coinciden.")
    if not acepta:
        errores.append("Tienes que aceptar la política de privacidad y el tratamiento de datos.")
    if errores:
        return None, errores

    existe = valor("SELECT id FROM `usuarios` WHERE username = %s", (usuario,))
    if existe:
        return None, ["Ese nombre de usuario ya está en uso."]
    existe = valor("SELECT id FROM `usuarios` WHERE email = %s", (email,))
    if existe:
        return None, ["Ese correo electrónico ya está registrado."]

    # El primer usuario de la liga es quien administra el panel.
    primero = valor("SELECT COUNT(*) AS n FROM `usuarios`", (), 0)
    es_admin = 1 if int(primero or 0) == 0 else 0

    ejecutar(
        "INSERT INTO `usuarios` (`username`,`email`,`password_hash`,`display_name`,"
        "`newsletter`,`is_admin`,`terms_accepted_at`,`created_at`,`last_login_at`)"
        " VALUES (%s,%s,%s,%s,%s,%s,NOW(),NOW(),NOW())",
        (usuario, email, hash_contrasena(contrasena), usuario,
         1 if boletin else 0, es_admin),
    )
    nuevo_id_ = valor("SELECT LAST_INSERT_ID() AS n")
    id_ = int(nuevo_id_ or 0)
    registrar_consentimiento(id_, boletin=boletin)
    confirmar()

    return {
        "id": id_, "username": usuario, "email": email, "display_name": usuario,
        "bio": "", "avatar_url": "", "country": "", "favorite_team": "",
        "is_premium": False, "is_admin": bool(es_admin), "google_id": None,
        "newsletter": bool(boletin), "terms_accepted_at": datetime.now(),
    }, []


def registrar_consentimiento(user_id: int, aceptado: bool = True, boletin: bool = False) -> None:
    if not user_id or user_id <= 0:
        return
    ejecutar(
        "INSERT INTO `consentimientos` (`user_id`,`doc_version`,`accepted`,`newsletter`,`ip`,`user_agent`)"
        " VALUES (%s,%s,%s,%s,%s,%s)",
        (user_id, POLITICA_VERSION, 1 if aceptado else 0, 1 if boletin else 0,
         ip_cliente(), agente_cliente()),
    )


def usuario_credenciales(identificador: str, contrasena: str) -> dict | None:
    """Valida el acceso con usuario o con correo."""
    identificador = str(identificador or "").strip()
    if not identificador or not contrasena:
        return None
    registro = fila(
        "SELECT * FROM `usuarios` WHERE username = %s OR email = %s LIMIT 1",
        (identificador, identificador.lower()),
    )
    if registro is None:
        verificar_contrasena(contrasena, SEÑUELO)
        return None
    if not verificar_contrasena(contrasena, registro.get("password_hash") or ""):
        return None
    return registro


def usuario_entrar(registro: dict) -> None:
    session.clear()
    session["uid"] = int(registro["id"])
    session.permanent = True
    csrf_token()
    ejecutar("UPDATE `usuarios` SET `last_login_at` = NOW() WHERE `id` = %s", (registro["id"],))
    confirmar()


def usuario_cerrar() -> None:
    session.clear()


def usuario_perfil_actualizar(usuario: dict, entrada: dict) -> list[str]:
    errores: list[str] = []
    nuevo = usuario_normalizado(entrada.get("username") or usuario["username"])
    email = str(entrada.get("email") or usuario["email"]).strip().lower()

    if not RE_USUARIO.match(nuevo):
        errores.append("El usuario debe tener entre 3 y 32 caracteres válidos.")
    elif nuevo != usuario["username"] and valor("SELECT id FROM `usuarios` WHERE username = %s", (nuevo,)):
        errores.append("Ese nombre de usuario ya está en uso.")
    if not RE_EMAIL.match(email) or len(email) > 190:
        errores.append("Escribe un correo electrónico válido.")
    elif email != usuario["email"] and valor("SELECT id FROM `usuarios` WHERE email = %s", (email,)):
        errores.append("Ese correo electrónico ya está registrado.")
    if errores:
        return errores

    avatar = entrada.get("avatar_url")
    if isinstance(avatar, str) and avatar.strip() == "":
        avatar_url = ""
    elif hasattr(avatar, "filename"):
        avatar_url = guardar_subida(avatar, "avatares", ruta_segura(usuario.get("avatar_url")))
    else:
        avatar_url = ruta_segura(avatar) or ruta_segura(usuario.get("avatar_url"))

    ejecutar(
        "UPDATE `usuarios` SET `username` = %s, `email` = %s, `display_name` = %s,"
        " `bio` = %s, `avatar_url` = %s, `country` = %s, `favorite_team` = %s,"
        " `newsletter` = %s WHERE `id` = %s",
        (nuevo, email,
         str_corta(entrada.get("display_name") or usuario["username"], 80),
         str_corta(entrada.get("bio"), 400),
         avatar_url,
         str_corta(entrada.get("country"), 60),
         str_corta(entrada.get("favorite_team"), 80),
         1 if a_bool(entrada.get("newsletter")) else 0,
         usuario["id"]),
    )
    confirmar()
    return []


def usuario_password_actualizar(usuario: dict, actual: str, nueva: str, confirmar_pw: str,
                                exigir_actual: bool = True) -> list[str]:
    if exigir_actual:
        guardado = valor("SELECT password_hash FROM `usuarios` WHERE `id` = %s", (usuario["id"],), "")
        if not verificar_contrasena(actual, str(guardado or "")):
            return ["La contraseña actual no es correcta."]
    if len(nueva or "") < 8:
        return ["La nueva contraseña debe tener al menos 8 caracteres."]
    if nueva != confirmar_pw:
        return ["Las contraseñas no coinciden."]
    if actual and actual == nueva:
        return ["La nueva contraseña debe ser distinta de la actual."]
    ejecutar("UPDATE `usuarios` SET `password_hash` = %s WHERE `id` = %s",
             (hash_contrasena(nueva), usuario["id"]))
    confirmar()
    return []


def usuario_premium_actualizar(usuario: dict, activo: bool) -> None:
    ejecutar("UPDATE `usuarios` SET `is_premium` = %s WHERE `id` = %s",
             (1 if activo else 0, usuario["id"]))
    confirmar()


def usuario_eliminar(usuario: dict) -> None:
    ejecutar("DELETE FROM `usuarios` WHERE `id` = %s", (usuario["id"],))
    confirmar()
    session.clear()


def usuario_exportar(usuario: dict) -> dict:
    registro = fila("SELECT * FROM `usuarios` WHERE `id` = %s", (usuario["id"],)) or {}
    registro.pop("password_hash", None)
    consentimientos = consultar(
        "SELECT doc_version, accepted, ip, user_agent, created_at FROM `consentimientos`"
        " WHERE `user_id` = %s ORDER BY created_at", (usuario["id"],))
    return {
        "exportado_el": datetime.now().isoformat(timespec="seconds"),
        "documento": f"privacidad-v{POLITICA_VERSION}",
        "cuenta": {clave: (str(valor) if isinstance(valor, (datetime, date)) else valor)
                   for clave, valor in registro.items()},
        "consentimientos": [{clave: (str(valor) if isinstance(valor, (datetime, date)) else valor)
                             for clave, valor in c.items()} for c in consentimientos],
    }



# ==============================================================================
#  DEFINICIÓN DE COLECCIONES
#
#  Cada colección es una tabla que alimenta al panel y a la API. El nombre de
#  tabla y el de columna salen siempre de estas listas blancas, nunca de lo que
#  envíe el visitante: eso es lo que evita la inyección SQL.
# ==============================================================================

def _c(campos: dict, requeridos: list | None = None) -> dict:
    return {"campos": campos, "requeridos": requeridos or []}


COLECCIONES: dict = {
    "matches": {
        "tabla": "partidos", "prefijo": "match", "etiqueta": "Partidos",
        "orden": "`division`, `journey`, `date`, `home`",
        **_c({
            "division": ("division", "division"),
            "stage": ("stage", ["liga", "playoffs"]),
            "journey": ("journey", "entero_null"),
            "journeyLabel": ("journey_label", "texto:60"),
            "range": ("range", "texto:40"),
            "date": ("date", "fecha"),
            "time": ("time", "hora"),
            "home": ("home", "texto:80"),
            "away": ("away", "texto:80"),
            "homeGoals": ("home_goals", "entero_null"),
            "awayGoals": ("away_goals", "entero_null"),
            "status": ("status", ["programado", "en-vivo", "finalizado", "wo", "pospuesto",
                                  "por-definir"]),
            "mvp": ("mvp", "texto:80"),
            "keeperHome": ("keeper_home", "texto:80"),
            "keeperAway": ("keeper_away", "texto:80"),
            "replay": ("replay", "texto:400"),
            "notes": ("notes", "texto:400"),
        }, ["home", "away"]),
    },
    "teams": {
        "tabla": "equipos", "prefijo": "team", "etiqueta": "Equipos",
        "orden": "`division`, `sort_order`, `name`",
        **_c({
            "name": ("name", "texto:80"),
            "division": ("division", "division"),
            "coach": ("coach", "texto:80"),
            "colors": ("colors", "texto:80"),
            "logo": ("logo", "ruta:300"),
            "note": ("note", "texto:400"),
            "sort_order": ("sort_order", "entero"),
        }, ["name"]),
    },
    "news": {
        "tabla": "noticias", "prefijo": "news", "etiqueta": "Noticias",
        "orden": "`pinned` DESC, `date` DESC, `id`",
        **_c({
            "title": ("title", "texto:160"),
            "category": ("category", "texto:60"),
            "excerpt": ("excerpt", "texto:400"),
            "body": ("body", "texto:8000"),
            "date": ("date", "fecha"),
            "author": ("author", "texto:80"),
            "image": ("image", "ruta:300"),
            "pinned": ("pinned", "bool"),
        }, ["title"]),
    },
    "announcements": {
        "tabla": "anuncios", "prefijo": "ann", "etiqueta": "Anuncios",
        "orden": "`date` DESC, `id`",
        **_c({
            "title": ("title", "texto:160"),
            "kicker": ("kicker", "texto:120"),
            "season": ("season", "texto:60"),
            "kind": ("kind", ["awards", "registration", "general"]),
            "date": ("date", "fecha"),
            "day": ("day", "entero"),
            "month": ("month", "entero"),
            "year": ("year", "entero"),
            "text": ("text", "texto:4000"),
            "bullets": ("bullets", "lista"),
            "closing": ("closing", "texto:800"),
            "warning": ("warning", "texto:400"),
        }, ["title"]),
    },
    "awards": {
        "tabla": "premios", "prefijo": "award", "etiqueta": "Museo de premios",
        "orden": "`year` DESC, `division`, `category`, `id`",
        **_c({
            "title": ("title", "texto:160"),
            "team": ("team", "texto:80"),
            "text": ("text", "texto:300"),
            "season": ("season", "texto:60"),
            "division": ("division", "division|ambas"),
            "category": ("category", ["premios", "rankings", "campeones"]),
            "image": ("image", "ruta:300"),
            "year": ("year", "entero"),
        }, ["title"]),
    },
    "pubs": {
        "tabla": "salas", "prefijo": "room", "etiqueta": "Salas públicas",
        "orden": "`sort_order`, `id`",
        **_c({
            "label": ("label", "texto:120"),
            "name": ("name", "texto:80"),
            "url": ("url", "url:400"),
            "status": ("status", ["ABIERTA", "CERRADA", "MANTENIMIENTO"]),
            "players": ("players", "entero_null"),
            "note": ("note", "texto:200"),
            "sort_order": ("sort_order", "entero"),
        }, ["url"]),
    },
    "important": {
        "tabla": "destacados", "prefijo": "imp", "etiqueta": "Accesos de la liga",
        "orden": "`sort_order`, `id`",
        **_c({
            "title": ("title", "texto:120"),
            "description": ("description", "texto:240"),
            "kind": ("kind", ["link", "external", "status"]),
            "href": ("href", "enlace:400"),
            "cta": ("cta", "texto:40"),
            "sort_order": ("sort_order", "entero"),
        }, ["title"]),
    },
    "staff": {
        "tabla": "personal", "prefijo": "staff", "etiqueta": "Equipo de administración",
        "orden": "`sort_order`, `id`",
        **_c({
            "name": ("name", "texto:80"),
            "username": ("username", "texto:80"),
            "role": ("role", ["Owner", "DESARROLLADOR", "Master", "Moderador", "Staff"]),
            "bio": ("bio", "texto:400"),
            "avatar": ("avatar", "ruta:300"),
            "banner": ("banner", "ruta:300"),
            "focus": ("focus", "texto:120"),
            "github": ("github", "texto:80"),
            "instagram": ("instagram", "texto:80"),
            "discord": ("discord", "texto:80"),
            "available": ("available", "bool"),
            "tags": ("tags", "lista"),
            "sort_order": ("sort_order", "entero"),
        }, ["name"]),
    },
    "alliances": {
        "tabla": "alianzas", "prefijo": "al", "etiqueta": "Alianzas y afiliaciones",
        "orden": "`sort_order`, `id`",
        **_c({
            "name": ("name", "texto:120"),
            "kind": ("kind", ["afiliacion", "partner", "proxima", "servidor"]),
            "description": ("description", "texto:400"),
            "href": ("href", "url:400"),
            "cta": ("cta", "texto:60"),
            "image": ("image", "ruta:300"),
            "status": ("status", ["activa", "proxima", "inactiva"]),
            "sort_order": ("sort_order", "entero"),
        }, ["name"]),
    },
    "social": {
        "tabla": "redes", "prefijo": "rd", "etiqueta": "Redes sociales",
        "orden": "`sort_order`, `id`",
        **_c({
            "network": ("network", ["instagram", "tiktok", "twitch", "youtube", "discord",
                                    "x", "facebook", "otro"]),
            "owner_name": ("owner_name", "texto:120"),
            "handle": ("handle", "texto:120"),
            "url": ("url", "url:400"),
            "followers": ("followers", "entero"),
            "is_streamer": ("is_streamer", "bool"),
            "sort_order": ("sort_order", "entero"),
        }, ["network"]),
    },
    "live": {
        "tabla": "directos", "prefijo": "live", "etiqueta": "Directos de fútbol",
        "orden": "`is_live` DESC, `starts_at`, `sort_order`",
        **_c({
            "league": ("league", "texto:120"),
            "home": ("home", "texto:120"),
            "away": ("away", "texto:120"),
            "home_score": ("home_score", "texto:10"),
            "away_score": ("away_score", "texto:10"),
            "channel": ("channel", "texto:40"),
            "platform": ("platform", ["twitch", "youtube", "kick", "otro"]),
            "url": ("url", "url:400"),
            "viewer_count": ("viewer_count", "entero"),
            "starts_at": ("starts_at", "datetime"),
            "is_live": ("is_live", "bool"),
            "sort_order": ("sort_order", "entero"),
        }, ["url"]),
    },
    "donations": {
        "tabla": "donaciones", "prefijo": "dn", "etiqueta": "Donaciones",
        "orden": "`sort_order`, `id`",
        **_c({
            "title": ("title", "texto:120"),
            "description": ("description", "texto:400"),
            "kind": ("kind", ["info", "meta", "metodo"]),
            "amount": ("amount", "decimal"),
            "method": ("method", "texto:60"),
            "account": ("account", "texto:120"),
            "goal": ("goal", "decimal"),
            "raised": ("raised", "decimal"),
            "is_active": ("is_active", "bool"),
            "sort_order": ("sort_order", "entero"),
        }, ["title"]),
    },
}

# Campos que guardan listas JSON y se leen ya desempaquetadas.
CAMPOS_LISTA = {"tags", "bullets"}

POSICIONES = ["Portero", "Defensa", "Defensa central", "Lateral", "Medio", "MCD",
             "MI", "MD", "Delantero", "Extremo"]

NOMBRES_RED = {"instagram": "Instagram", "tiktok": "TikTok", "twitch": "Twitch",
               "youtube": "YouTube", "discord": "Discord", "x": "X",
               "facebook": "Facebook", "otro": "Otro"}


# ==============================================================================
#  SANEADO DE ENTRADAS
# ==============================================================================

def ids_division() -> list:
    return [r["id"] for r in consultar("SELECT `id` FROM `divisiones` ORDER BY sort_order, name")]


def sanear(valor, regla):
    """Limpia un valor según la regla declarada en la colección."""
    if isinstance(regla, list):
        texto = str_corta(valor, 120)
        return texto if texto in regla else regla[0]
    if isinstance(regla, tuple):
        return sanear(valor, regla[0])

    partes = str(regla).split(":", 1)
    tipo = partes[0]
    maximo = int(partes[1]) if len(partes) > 1 and partes[1].isdigit() else 400

    if tipo.startswith("division"):
        permitidos = ids_division()
        if "|ambas" in tipo:
            permitidos = permitidos + ["ambas"]
        if not permitidos:
            return ""
        texto = str_corta(valor, 24)
        return texto if texto in permitidos else permitidos[0]
    if tipo == "entero":
        return a_entero(valor, 0)
    if tipo == "entero_null":
        return a_entero(valor, None)
    if tipo == "decimal":
        return a_decimal(valor, 0.0)
    if tipo == "bool":
        return 1 if a_bool(valor) else 0
    if tipo == "fecha":
        return fecha_valida(valor)
    if tipo == "hora":
        return hora_valida(valor)
    if tipo == "datetime":
        return datetime_valido(valor)
    if tipo == "url":
        return url_segura(valor)
    if tipo == "ruta":
        return ruta_segura(valor, maximo)
    if tipo == "enlace":
        return enlace_seguro(valor, maximo)
    if tipo == "lista":
        return json_texto(sanear_lista(valor, maximo))
    return str_corta(valor, maximo)


def sanear_campo(nombre_coleccion: str, campo: str, valor):
    """Devuelve (columna, valor saneado), o None si el campo no existe."""
    definicion = COLECCIONES.get(nombre_coleccion)
    if definicion is None or campo not in definicion["campos"]:
        return None
    columna, regla = definicion["campos"][campo]
    if columna in CAMPOS_LISTA and not isinstance(valor, str):
        return columna, json_texto(sanear_lista(valor, 400))
    return columna, sanear(valor, regla)


def validar_coleccion(registro: dict, definicion: dict) -> list:
    errores = []
    for campo in definicion["requeridos"]:
        valor = registro.get(campo)
        if valor is None or not str(valor).strip():
            errores.append('El campo "' + campo + '" es obligatorio.')
    return errores


def fila_a_json(fila_: dict, nombre_coleccion: str) -> dict:
    definicion = COLECCIONES.get(nombre_coleccion) or {"campos": {}}
    salida = {}
    for campo, par in definicion["campos"].items():
        columna = par[0]
        if columna not in fila_:
            continue
        valor = fila_[columna]
        if columna in CAMPOS_LISTA:
            salida[campo] = json_seguro(valor)
        elif isinstance(valor, datetime):
            salida[campo] = valor.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(valor, date):
            salida[campo] = valor.strftime("%Y-%m-%d")
        elif isinstance(valor, timedelta):
            # PyMySQL devuelve las columnas TIME como timedelta.
            segundos = int(valor.total_seconds()) % 86400
            salida[campo] = "%02d:%02d" % (segundos // 3600, (segundos % 3600) // 60)
        elif isinstance(valor, Decimal):
            salida[campo] = float(valor)
        elif isinstance(valor, (bytes, bytearray)):
            salida[campo] = valor.decode("utf-8", "replace")
        else:
            salida[campo] = valor
    salida["id"] = fila_.get("id", "")
    return salida


# ==============================================================================
#  LECTURA
# ==============================================================================

def leer_ajustes() -> dict:
    f = fila("SELECT * FROM `ajustes` WHERE `id` = 1") or {}
    return {
        "leagueName": f.get("league_name") or APP_NOMBRE,
        "shortName": f.get("short_name") or "TDL",
        "tagline": f.get("tagline") or "",
        "description": f.get("description") or "",
        "season": f.get("season") or "",
        "seasonNumber": int(f.get("season_number") or 1),
        "modality": f.get("modality") or "",
        "status": f.get("status") or "",
        "statusNote": f.get("status_note") or "",
        "server": f.get("server") or "",
        "map": f.get("map") or "",
        "matchDuration": f.get("match_duration") or "",
        "tolerance": f.get("tolerance") or "",
        "pointsWin": int(f.get("points_win") or 3),
        "pointsDraw": int(f.get("points_draw") or 1),
        "tiktok": f.get("tiktok") or "",
        "tiktokHandle": f.get("tiktok_handle") or "",
        "founded": int(f["founded"]) if f.get("founded") else None,
        "donationNote": f.get("donation_note") or "",
        "donationKey": f.get("donation_key") or "",
        "donationGoal": float(f.get("donation_goal") or 0),
        "matchConfig": [
            {"label": str(p.get("label", "")), "value": str(p.get("value", ""))}
            for p in json_seguro(f.get("match_config"))
        ],
    }


def leer_divisiones() -> list:
    salida = []
    for f in consultar("SELECT * FROM `divisiones` ORDER BY sort_order, name"):
        salida.append({
            "id": f["id"], "name": f["name"], "code": f["code"], "season": f["season"],
            "summary": f.get("summary") or "", "teams": int(f["teams"] or 0),
            "journeys": int(f["journeys"] or 0), "playoffs": f["playoffs"],
            "relegation": f["relegation"], "promotion": f["promotion"],
            "phases": json_seguro(f.get("phases")), "movement": json_seguro(f.get("movement")),
            "rules": json_seguro(f.get("rules")),
        })
    return salida


def leer_coleccion(nombre: str) -> list:
    definicion = COLECCIONES.get(nombre)
    if definicion is None:
        return []
    filas_ = consultar("SELECT * FROM `" + definicion["tabla"] + "` ORDER BY " + definicion["orden"])
    return [fila_a_json(f, nombre) for f in filas_]


def leer_reglas() -> list:
    reglas = consultar("SELECT * FROM `reglas` ORDER BY sort_order, id")
    puntos = consultar("SELECT * FROM `regla_items` ORDER BY `rule_id`, sort_order, id")
    por_regla: dict = {}
    for punto in puntos:
        por_regla.setdefault(punto["rule_id"], []).append(punto)

    salida = []
    for regla in reglas:
        items, bloques, tarjetas = [], [], []
        for punto in por_regla.get(regla["id"], []):
            lista = json_seguro(punto.get("list"))
            texto = punto.get("text") or ""
            titulo = punto.get("title") or ""
            # La semilla original guarda objetos JSON dentro de `text`.
            if not titulo and texto.startswith("{"):
                objeto = json_seguro(texto)
                if isinstance(objeto, dict):
                    titulo = objeto.get("title") or ""
                    texto = objeto.get("text") or ""
            if punto["kind"] == "bloque":
                bloque = {"title": titulo, "subtitle": punto.get("subtitle") or "", "text": texto}
                if lista:
                    bloque["list"] = lista
                bloques.append({k: v for k, v in bloque.items() if v != ""})
            elif punto["kind"] == "tarjeta":
                tarjeta = {"title": titulo, "kicker": punto.get("kicker") or "",
                           "tone": punto.get("tone") or "info"}
                if lista:
                    tarjeta["list"] = lista
                if texto:
                    tarjeta["text"] = texto
                tarjetas.append({k: v for k, v in tarjeta.items() if v != ""})
            else:
                item = {"title": titulo}
                if texto:
                    item["text"] = texto
                items.append(item)

        entrada = {"id": regla["id"], "title": regla["title"]}
        if regla.get("summary"):
            entrada["summary"] = regla["summary"]
        if items:
            entrada["items"] = items
        if bloques:
            entrada["blocks"] = bloques
        if tarjetas:
            entrada["cards"] = tarjetas
        salida.append(entrada)
    return salida


def leer_jugadores(team_id: str = "") -> list:
    if team_id:
        return consultar(
            "SELECT j.*, e.`name` AS team_name FROM `jugadores` j"
            " LEFT JOIN `equipos` e ON e.`id` = j.`team_id`"
            " WHERE j.`team_id` = %s ORDER BY j.sort_order, j.`name`", (team_id,))
    return consultar(
        "SELECT j.*, e.`name` AS team_name FROM `jugadores` j"
        " LEFT JOIN `equipos` e ON e.`id` = j.`team_id`"
        " ORDER BY e.`name`, j.sort_order, j.`name`")


def leer_eventos(match_id: str = "") -> list:
    if match_id:
        return consultar(
            "SELECT * FROM `partido_eventos` WHERE `match_id` = %s"
            " ORDER BY sort_order, id", (match_id,))
    return consultar(
        "SELECT ev.*, p.`home`, p.`away` FROM `partido_eventos` ev"
        " JOIN `partidos` p ON p.`id` = ev.`match_id`"
        " ORDER BY p.`date`, ev.sort_order, ev.id")


def cargar_datos() -> dict:
    return {
        "version": 4,
        "updatedAt": datetime.now().isoformat(timespec="seconds"),
        "settings": leer_ajustes(),
        "divisions": leer_divisiones(),
        "teams": leer_coleccion("teams"),
        "matches": leer_coleccion("matches"),
        "rules": leer_reglas(),
        "pubs": leer_coleccion("pubs"),
        "news": leer_coleccion("news"),
        "announcements": leer_coleccion("announcements"),
        "awards": leer_coleccion("awards"),
        "important": leer_coleccion("important"),
        "staff": leer_coleccion("staff"),
        "alliances": leer_coleccion("alliances"),
        "social": leer_coleccion("social"),
        "live": leer_coleccion("live"),
        "donations": leer_coleccion("donations"),
    }


# ==============================================================================
#  SUBIDAS DE FICHEROS
# ==============================================================================

def guardar_subida(archivo, carpeta: str, anterior: str = "") -> str:
    """Guarda un logo o un avatar y devuelve su ruta pública /uploads/..."""
    if archivo is None or not getattr(archivo, "filename", ""):
        return anterior or ""
    extension = Path(str(archivo.filename)).suffix.lower()
    if extension not in FORMATOS_LOGO:
        raise ValueError("Solo se admiten imagenes PNG, JPG, WEBP o GIF.")

    destino_dir = UPLOADS / carpeta
    destino_dir.mkdir(parents=True, exist_ok=True)
    destino = destino_dir / (secrets.token_hex(10) + extension)
    archivo.save(str(destino))

    nueva = "/uploads/" + carpeta + "/" + destino.name
    if anterior and anterior.startswith("/uploads/") and anterior != nueva:
        viejo = RAIZ / anterior.lstrip("/")
        try:
            if viejo.is_file() and viejo.resolve().parent == destino_dir.resolve():
                viejo.unlink()
        except OSError:
            pass
    return nueva


# ==============================================================================
#  ESCRITURA
# ==============================================================================

def crear_registro(nombre: str, entrada: dict) -> dict:
    definicion = COLECCIONES.get(nombre)
    if definicion is None:
        raise ValueError("Coleccion desconocida.")

    registro: dict = {}
    for campo, valor in entrada.items():
        par = definicion["campos"].get(campo)
        if par is None:
            continue
        columna = par[0]
        if hasattr(valor, "filename"):
            registro[columna] = guardar_subida(
                valor, "equipos" if columna == "logo" else "avatares")
            continue
        saneado = sanear_campo(nombre, campo, valor)
        if saneado is not None:
            registro[saneado[0]] = saneado[1]

    errores = validar_coleccion(entrada, definicion)
    if errores:
        raise ValueError(" ".join(errores))

    registro["id"] = nuevo_id(definicion["prefijo"])
    columnas = list(registro.keys())
    marcas = ", ".join(["%s"] * len(columnas))
    ejecutar("INSERT INTO `" + definicion["tabla"] + "` (`"
             + "`, `".join(columnas) + "`) VALUES (" + marcas + ")",
             tuple(registro[c] for c in columnas))

    guardado = fila("SELECT * FROM `" + definicion["tabla"] + "` WHERE `id` = %s",
                    (registro["id"],)) or {}
    confirmar()
    return fila_a_json(guardado, nombre)


def actualizar_registro(nombre: str, id_: str, entrada: dict) -> dict:
    definicion = COLECCIONES.get(nombre)
    if definicion is None or not id_valido(id_):
        raise ValueError("Registro no valido.")
    actual = fila("SELECT * FROM `" + definicion["tabla"] + "` WHERE `id` = %s", (id_,))
    if actual is None:
        raise ValueError("El registro no existe.")

    cambios: dict = {}
    for campo, valor in entrada.items():
        par = definicion["campos"].get(campo)
        if par is None:
            continue
        columna = par[0]
        if hasattr(valor, "filename"):
            if not valor.filename:
                continue                     # campo sin tocar
            cambios[columna] = guardar_subida(
                valor, "equipos" if columna == "logo" else "avatares", actual.get(columna) or "")
            continue
        saneado = sanear_campo(nombre, campo, valor)
        if saneado is not None:
            cambios[saneado[0]] = saneado[1]

    cambios.pop("id", None)
    if cambios:
        sets = ", ".join("`" + c + "` = %s" for c in cambios)
        ejecutar("UPDATE `" + definicion["tabla"] + "` SET " + sets + " WHERE `id` = %s",
                 tuple(cambios.values()) + (id_,))

    final = fila("SELECT * FROM `" + definicion["tabla"] + "` WHERE `id` = %s", (id_,)) or {}
    errores = validar_coleccion(fila_a_json(final, nombre), definicion)
    confirmar()
    if errores:
        raise ValueError(" ".join(errores))
    return fila_a_json(final, nombre)


def borrar_registro(nombre: str, id_: str) -> bool:
    definicion = COLECCIONES.get(nombre)
    if definicion is None or not id_valido(id_):
        return False
    affected = ejecutar("DELETE FROM `" + definicion["tabla"] + "` WHERE `id` = %s", (id_,))
    confirmar()
    return affected > 0


def guardar_jugadores(team_id: str, lista: list) -> list:
    """Reemplaza la plantilla de un equipo (name, jersey, position, note)."""
    ejecutar("DELETE FROM `jugadores` WHERE `team_id` = %s", (team_id,))
    orden = 0
    for item in lista or []:
        if not isinstance(item, dict):
            continue
        nombre = str_corta(item.get("name"), 80)
        if not nombre:
            continue
        puesto = str_corta(item.get("position"), 40) or "Delantero"
        if puesto not in POSICIONES:
            puesto = "Delantero"
        dorsal = a_entero(item.get("jersey"), None)
        if dorsal is not None and not 0 <= dorsal <= 99:
            dorsal = None
        ejecutar(
            "INSERT INTO `jugadores` (`id`,`team_id`,`name`,`jersey`,`position`,`note`,`sort_order`)"
            " VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (nuevo_id("jug", 5), team_id, nombre, dorsal, puesto,
             str_corta(item.get("note"), 200), orden))
        orden += 1
    confirmar()
    return leer_jugadores(team_id)


def guardar_eventos(match_id: str, lista: list) -> list:
    """Reemplaza los goles y las asistencias de un partido."""
    partido = fila("SELECT `home`, `away` FROM `partidos` WHERE `id` = %s", (match_id,)) or {}
    ejecutar("DELETE FROM `partido_eventos` WHERE `match_id` = %s", (match_id,))
    orden = 0
    for item in lista or []:
        if not isinstance(item, dict):
            continue
        jugador = str_corta(item.get("player"), 80)
        if not jugador:
            continue
        tipo = "asistencia" if str(item.get("kind")) == "asistencia" else "gol"
        lado = "visitante" if str(item.get("side")) == "visitante" else "local"
        equipo = str_corta(item.get("team"), 80) or (partido.get(lado) or "")
        minuto = a_entero(item.get("minute"), None)
        if minuto is not None and not 0 <= minuto <= 200:
            minuto = None
        ejecutar(
            "INSERT INTO `partido_eventos`"
            " (`match_id`,`kind`,`side`,`team`,`player`,`minute`,`sort_order`)"
            " VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (match_id, tipo, lado, equipo, jugador, minuto, orden))
        orden += 1
    confirmar()
    return leer_eventos(match_id)


def guardar_ajustes(entrada: dict) -> dict:
    mapa = {
        "leagueName": ("league_name", "texto:120"), "shortName": ("short_name", "texto:40"),
        "tagline": ("tagline", "texto:200"), "description": ("description", "texto:2000"),
        "season": ("season", "texto:60"), "seasonNumber": ("season_number", "entero"),
        "modality": ("modality", "texto:120"), "status": ("status", "texto:60"),
        "statusNote": ("status_note", "texto:255"), "server": ("server", "texto:120"),
        "map": ("map", "texto:60"), "matchDuration": ("match_duration", "texto:60"),
        "tolerance": ("tolerance", "texto:60"), "pointsWin": ("points_win", "entero"),
        "pointsDraw": ("points_draw", "entero"), "tiktok": ("tiktok", "url:255"),
        "tiktokHandle": ("tiktok_handle", "texto:120"), "founded": ("founded", "entero_null"),
        "matchConfig": ("match_config", "config"), "donationNote": ("donation_note", "texto:255"),
        "donationKey": ("donation_key", "texto:120"), "donationGoal": ("donation_goal", "decimal"),
    }
    sets, params = [], []
    for campo, valor in entrada.items():
        if campo not in mapa:
            continue
        columna, regla = mapa[campo]
        if regla == "config":
            valor = json_texto(sanear_objetos(valor, {"label": 60, "value": 120}))
        else:
            valor = sanear(valor, regla)
        sets.append("`" + columna + "` = %s")
        params.append(valor)
    if sets:
        ejecutar("UPDATE `ajustes` SET " + ", ".join(sets) + " WHERE `id` = 1", tuple(params))
        confirmar()
    return leer_ajustes()


def guardar_reglas(entrada: list) -> list:
    for regla in entrada or []:
        if not isinstance(regla, dict):
            continue
        id_ = str_corta(regla.get("id"), 40)
        if not id_:
            continue
        ejecutar(
            "INSERT INTO `reglas` (`id`,`title`,`summary`,`sort_order`) VALUES (%s,%s,%s,%s)"
            " ON DUPLICATE KEY UPDATE `title` = VALUES(`title`),"
            " `summary` = VALUES(`summary`), `sort_order` = VALUES(`sort_order`)",
            (id_, str_corta(regla.get("title"), 120), str_corta(regla.get("summary"), 255),
             a_entero(regla.get("sort_order"), 0)))
        ejecutar("DELETE FROM `regla_items` WHERE `rule_id` = %s", (id_,))
        orden = 0
        for grupo, tipo in (("items", "item"), ("blocks", "bloque"), ("cards", "tarjeta")):
            for item in (regla.get(grupo) or []):
                if not isinstance(item, dict):
                    continue
                ejecutar(
                    "INSERT INTO `regla_items` (`rule_id`,`kind`,`title`,`subtitle`,`kicker`,"
                    "`tone`,`text`,`list`,`sort_order`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (id_, tipo,
                     str_corta(item.get("title"), 160), str_corta(item.get("subtitle"), 160),
                     str_corta(item.get("kicker"), 60), str_corta(item.get("tone") or "info", 20),
                     str_corta(item.get("text"), 800),
                     json_texto(sanear_lista(item.get("list"))), orden))
                orden += 1
    confirmar()
    return leer_reglas()


def guardar_divisiones(entrada: list) -> list:
    orden = 0
    for division in entrada or []:
        if not isinstance(division, dict):
            continue
        id_ = str_corta(division.get("id"), 24)
        if not id_:
            continue
        ejecutar(
            "INSERT INTO `divisiones` (`id`,`name`,`code`,`season`,`summary`,`teams`,`journeys`,"
            "`playoffs`,`relegation`,`promotion`,`phases`,`movement`,`rules`,`sort_order`)"
            " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            " ON DUPLICATE KEY UPDATE `name` = VALUES(`name`), `code` = VALUES(`code`),"
            " `season` = VALUES(`season`), `summary` = VALUES(`summary`),"
            " `teams` = VALUES(`teams`), `journeys` = VALUES(`journeys`),"
            "`playoffs` = VALUES(`playoffs`), `relegation` = VALUES(`relegation`),"
            "`promotion` = VALUES(`promotion`), `phases` = VALUES(`phases`),"
            "`movement` = VALUES(`movement`), `rules` = VALUES(`rules`),"
            "`sort_order` = VALUES(`sort_order`)",
            (id_,
             str_corta(division.get("name") or id_, 80),
             str_corta(division.get("code") or id_.upper(), 24),
             str_corta(division.get("season"), 60),
             str_corta(division.get("summary"), 800),
             max(0, a_entero(division.get("teams"), 0) or 0),
             max(0, a_entero(division.get("journeys"), 0) or 0),
             str_corta(division.get("playoffs"), 200),
             str_corta(division.get("relegation"), 200),
             str_corta(division.get("promotion"), 200),
             json_texto(sanear_objetos(division.get("phases"),
                                        {"label": 60, "title": 160, "text": 800, "note": 400})),
             json_texto(sanear_movimiento(division.get("movement"))),
             json_texto(sanear_objetos(division.get("rules"), {"title": 160, "text": 800})),
             orden))
        orden += 1
    confirmar()
    return leer_divisiones()


# ==============================================================================
#  CLASIFICACIONES, PARTIDOS Y ESTADÍSTICAS
# ==============================================================================

def calcular_clasificacion(equipos: list, partidos: list, division_id: str, ajustes: dict) -> list:
    victoria = int(ajustes.get("pointsWin") or 3)
    empate = int(ajustes.get("pointsDraw") or 1)
    filas_: dict = {}

    def asegurar(nombre):
        nombre = str(nombre or "").strip()
        if not nombre:
            return None
        clave = sin_acentos(nombre).upper()
        if clave not in filas_:
            filas_[clave] = {"key": clave, "name": nombre, "played": 0, "won": 0, "drawn": 0,
                             "lost": 0, "goalsFor": 0, "goalsAgainst": 0, "points": 0}
        return clave

    for equipo in equipos:
        if equipo.get("division") == division_id:
            asegurar(equipo.get("name"))

    for partido in partidos:
        if partido.get("division") != division_id or partido.get("status") != "finalizado":
            continue
        local = asegurar(partido.get("home"))
        visitante = asegurar(partido.get("away"))
        if local is None or visitante is None or local == visitante:
            continue
        gl = int(partido.get("homeGoals") or 0)
        gv = int(partido.get("awayGoals") or 0)

        for clave, a_favor, en_contra in ((local, gl, gv), (visitante, gv, gl)):
            filas_[clave]["played"] += 1
            filas_[clave]["goalsFor"] += a_favor
            filas_[clave]["goalsAgainst"] += en_contra

        if gl > gv:
            filas_[local]["won"] += 1
            filas_[local]["points"] += victoria
            filas_[visitante]["lost"] += 1
        elif gl < gv:
            filas_[visitante]["won"] += 1
            filas_[visitante]["points"] += victoria
            filas_[local]["lost"] += 1
        else:
            for clave in (local, visitante):
                filas_[clave]["drawn"] += 1
                filas_[clave]["points"] += empate

    tabla = list(filas_.values())
    for f in tabla:
        f["goalDiff"] = f["goalsFor"] - f["goalsAgainst"]

    tabla.sort(key=lambda f: (-f["points"], -f["goalDiff"], -f["goalsFor"], f["name"]))
    for indice, f in enumerate(tabla, start=1):
        f["position"] = indice
    return tabla


def clasificaciones(equipos: list, partidos: list, divisiones: list, ajustes: dict) -> dict:
    return {d["id"]: calcular_clasificacion(equipos, partidos, d["id"], ajustes)
            for d in divisiones}


def proximo_partido(partidos: list, divisiones: list):
    ahora = datetime.now()
    candidatos = []
    for partido in partidos:
        if partido.get("status") != "programado" or not partido.get("date"):
            continue
        momento = a_datetime(str(partido["date"]) + " " + str(partido.get("time") or "00:00"))
        if momento is None or momento < ahora - timedelta(hours=3):
            continue
        copia = dict(partido)
        copia["stamp"] = momento
        candidatos.append(copia)
    if not candidatos:
        return None
    partido = min(candidatos, key=lambda p: p["stamp"])
    for division in divisiones:
        if division["id"] == partido["division"]:
            partido["divisionName"] = division["name"]
            break
    partido.setdefault("divisionName", "")
    return partido


def resumen_partido(partido: dict) -> dict:
    """Un partido con sus goles, asistencias, porterías a cero y MVP."""
    eventos = leer_eventos(partido["id"])
    porterias = []
    if partido.get("keeper_home") and int(partido.get("homeGoals") or 0) == 0:
        porterias.append({"team": partido["home"], "player": partido["keeper_home"]})
    if partido.get("keeper_away") and int(partido.get("awayGoals") or 0) == 0:
        porterias.append({"team": partido["away"], "player": partido["keeper_away"]})
    return {
        "match": partido,
        "events": eventos,
        "goals": {
            "local": sum(1 for ev in eventos if ev["kind"] == "gol" and ev["side"] == "local"),
            "visitante": sum(1 for ev in eventos if ev["kind"] == "gol" and ev["side"] == "visitante"),
        },
        "cleanSheets": porterias,
        "mvp": partido.get("mvp") or "",
    }


def estadisticas_jugadores() -> list:
    """Totales de temporada: goles, asistencias, porterías a cero y premios MVP."""
    estadisticas: dict = {}

    def plaza(nombre, equipo=""):
        nombre = str(nombre or "").strip()
        if not nombre:
            return None
        clave = (sin_acentos(nombre) + "|" + sin_acentos(equipo)).upper()
        if clave not in estadisticas:
            estadisticas[clave] = {"player": nombre, "team": equipo, "goals": 0, "assists": 0,
                                   "cleanSheets": 0, "mvp": 0}
        if equipo and not estadisticas[clave]["team"]:
            estadisticas[clave]["team"] = equipo
        return estadisticas[clave]

    for evento in consultar(
            "SELECT ev.player, ev.kind, ev.team FROM `partido_eventos` ev"
            " JOIN `partidos` p ON p.`id` = ev.`match_id` WHERE p.status = 'finalizado'"):
        entrada = plaza(evento["player"], evento.get("team") or "")
        if entrada:
            entrada["goals" if evento["kind"] == "gol" else "assists"] += 1

    for partido in consultar(
            "SELECT `home`, `away`, `home_goals`, `away_goals`, `keeper_home`, `keeper_away`, `mvp`"
            " FROM `partidos` WHERE status = 'finalizado'"):
        for lado, columna in (("home", "keeper_home"), ("away", "keeper_away")):
            portero = partido.get(columna)
            if portero and int(partido[lado + "_goals"] or 0) == 0:
                plaza(portero, partido[lado])["cleanSheets"] += 1
        if partido.get("mvp"):
            jugador = plaza(partido["mvp"])
            if jugador:
                casa = sin_acentos(partido["home"]).upper() in sin_acentos(partido["mvp"]).upper()
                if not jugador["team"]:
                    jugador["team"] = partido["home"] if casa else partido["away"]
                jugador["mvp"] += 1

    for jugador in consultar("SELECT j.`name`, e.`name` AS team_name FROM `jugadores` j"
                             " LEFT JOIN `equipos` e ON e.`id` = j.`team_id`"):
        plaza(jugador["name"], jugador.get("team_name") or "")

    return sorted(estadisticas.values(),
                  key=lambda f: (-f["goals"], -f["assists"], -f["mvp"], f["player"]))
# ==============================================================================
#  HOJA DE ESTILOS
# ==============================================================================

CSS = r"""
*,*::before,*::after{box-sizing:border-box}
:root{
  --fondo:#07080d; --fondo-2:#0b0d14; --panel:#111420; --panel-2:#161a29;
  --linea:#232838; --linea-2:#2f364a;
  --texto:#eef1f8; --tenue:#98a1b8; --muy-tenue:#6b7590;
  --oro:#f5c451; --oro-2:#ffe9a8; --diamante:#7fe3ff;
  --verde:#3ddc97; --rojo:#ff5f6d; --azul:#5b8cff; --violeta:#a86bff;
  --radio:16px; --radio-s:10px;
  --sombra:0 18px 50px rgba(0,0,0,.55);
  --ancho:1240px;
}
html{scroll-behavior:smooth;scroll-padding-top:96px}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}
  *{animation-duration:.001ms!important;transition-duration:.001ms!important}}
body{
  margin:0;background:
    radial-gradient(1100px 620px at 12% -8%,rgba(245,196,81,.10),transparent 60%),
    radial-gradient(900px 560px at 92% 4%,rgba(127,227,255,.09),transparent 62%),
    var(--fondo);
  color:var(--texto);font:16px/1.65 "Segoe UI",system-ui,-apple-system,Roboto,sans-serif;
  min-height:100vh;overflow-x:hidden;
}
img{max-width:100%;height:auto;display:block}
a{color:var(--diamante);text-decoration:none}
a:hover{text-decoration:underline}
h1,h2,h3,h4{line-height:1.2;margin:0 0 .5em;font-weight:800;letter-spacing:-.02em}
h1{font-size:clamp(1.9rem,4.6vw,3.1rem)}
h2{font-size:clamp(1.4rem,2.9vw,2rem)}
h3{font-size:1.14rem}
p{margin:0 0 1em}
small{font-size:.82rem}
.tenue{color:var(--tenue)}
.muy-tenue{color:var(--muy-tenue)}
.centrado{text-align:center}
.der{text-align:right}
.nowrap{white-space:nowrap}
.oculto{display:none!important}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
.envoltura{width:100%;max-width:var(--ancho);margin-inline:auto;padding-inline:20px}

/* ---------- Botones ---------- */
.btn{
  display:inline-flex;align-items:center;justify-content:center;gap:.5em;
  padding:.7em 1.25em;border:1px solid var(--linea-2);border-radius:999px;
  background:var(--panel-2);color:var(--texto);font:inherit;font-weight:700;
  cursor:pointer;transition:.18s ease;text-decoration:none;line-height:1.2;
}
.btn:hover{border-color:var(--oro);color:var(--oro-2);text-decoration:none;transform:translateY(-1px)}
.btn:focus-visible{outline:2px solid var(--diamante);outline-offset:2px}
.btn.primario{background:linear-gradient(135deg,var(--oro),#e0a92f);border-color:transparent;color:#1a1405}
.btn.primario:hover{color:#1a1405;filter:brightness(1.08)}
.btn.peligro{border-color:rgba(255,95,109,.5);color:#ff9aa2}
.btn.peligro:hover{background:rgba(255,95,109,.14);border-color:var(--rojo);color:#ffb3b8}
.btn.pequeno{padding:.42em .85em;font-size:.84rem}
.btn.fantasma{background:transparent}

/* ---------- Etiquetas ---------- */
.etiqueta{
  display:inline-flex;align-items:center;gap:.4em;padding:.28em .75em;border-radius:999px;
  font-size:.72rem;font-weight:800;letter-spacing:.09em;text-transform:uppercase;
  border:1px solid var(--linea-2);background:rgba(255,255,255,.04);color:var(--tenue);
}
.etiqueta.oro{color:var(--oro);border-color:rgba(245,196,81,.42);background:rgba(245,196,81,.1)}
.etiqueta.diamante{color:var(--diamante);border-color:rgba(127,227,255,.4);background:rgba(127,227,255,.09)}
.etiqueta.verde{color:var(--verde);border-color:rgba(61,220,151,.42);background:rgba(61,220,151,.1)}
.etiqueta.rojo{color:#ff9aa2;border-color:rgba(255,95,109,.45);background:rgba(255,95,109,.11)}
.etiqueta.azul{color:#9db6ff;border-color:rgba(91,140,255,.45);background:rgba(91,140,255,.11)}
.etiqueta.violeta{color:#c9a4ff;border-color:rgba(168,107,255,.45);background:rgba(168,107,255,.11)}

/* ---------- Cabecera ---------- */
.cabecera{
  position:sticky;top:0;z-index:60;background:rgba(7,8,13,.9);
  backdrop-filter:blur(14px);border-bottom:1px solid var(--linea);
}
.cabecera-fila{display:flex;align-items:center;gap:18px;padding:12px 0}
.marca{display:flex;align-items:center;gap:11px;flex:0 0 auto}
.marca img{width:42px;height:42px;border-radius:12px;object-fit:cover}
.marca-escudo{
  width:42px;height:42px;border-radius:12px;display:grid;place-items:center;
  background:linear-gradient(135deg,var(--oro),#c9932a);color:#1a1405;font-weight:900;
  font-size:1.05rem;box-shadow:0 6px 20px rgba(245,196,81,.3);
}
.marca-txt strong{display:block;font-size:.98rem;letter-spacing:.02em}
.marca-txt span{display:block;font-size:.68rem;color:var(--muy-tenue);letter-spacing:.19em;text-transform:uppercase}

.nav{display:flex;align-items:center;gap:2px;margin-left:auto;flex-wrap:wrap}
.nav a{
  position:relative;padding:.55em .78em;border-radius:9px;font-size:.735rem;font-weight:800;
  letter-spacing:.055em;color:var(--tenue);white-space:nowrap;text-transform:uppercase;
}
.nav a:hover{color:var(--oro);background:rgba(245,196,81,.09);text-decoration:none}
.nav a.activo{color:var(--oro);background:rgba(245,196,81,.13)}
.nav a.activo::after{
  content:"";position:absolute;left:50%;bottom:-1px;transform:translateX(-50%);
  width:16px;height:2px;border-radius:2px;background:var(--oro);
}
.nav .tuerca-btn{
  width:38px;height:38px;padding:0;display:grid;place-items:center;border-radius:11px;
  border:1px solid var(--linea-2);background:var(--panel-2);font-size:1.05rem;
}
.nav .tuerca-btn:hover{border-color:var(--oro);transform:rotate(45deg)}
.nav .tuerca-btn.activo{border-color:var(--oro);background:rgba(245,196,81,.14)}
.sesion-chip{
  display:flex;align-items:center;gap:.5em;padding:.32em .5em .32em .34em;border-radius:999px;
  border:1px solid var(--linea-2);background:var(--panel-2);font-size:.78rem;font-weight:700;
}
.sesion-chip img{width:26px;height:26px;border-radius:50%;object-fit:cover;background:var(--linea)}
.sesion-chip .punto{width:7px;height:7px;border-radius:50%;background:var(--verde);
  box-shadow:0 0 0 3px rgba(61,220,151,.18)}

/* ---------- Tuerca ---------- */
.tuerca-caja{
  position:fixed;inset:0 0 0 auto;width:min(420px,100%);z-index:80;
  background:var(--fondo-2);border-left:1px solid var(--linea);box-shadow:var(--sombra);
  transform:translateX(100%);transition:transform .28s cubic-bezier(.4,0,.2,1);
  display:flex;flex-direction:column;overflow-y:auto;
}
.tuerca-caja.abierta{transform:none}
.tuerca-velo{position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:79;opacity:0;pointer-events:none;transition:.28s}
.tuerca-velo.visible{opacity:1;pointer-events:auto}
.tuerca-cab{display:flex;align-items:center;gap:12px;padding:20px;border-bottom:1px solid var(--linea)}
.tuerca-cab h2{font-size:1.02rem;margin:0;flex:1}
.tuerca-cuerpo{padding:20px;display:grid;gap:22px}
.tuerca-usuario{display:flex;align-items:center;gap:13px;padding:15px;border-radius:var(--radio);
  background:var(--panel);border:1px solid var(--linea)}
.tuerca-usuario img,.tuerca-usuario .ini{
  width:52px;height:52px;border-radius:14px;object-fit:cover;flex:0 0 auto;
  background:linear-gradient(135deg,var(--violeta),var(--azul));display:grid;place-items:center;
  font-weight:900;font-size:1.2rem;color:#fff;
}
.tuerca-usuario strong{display:block}
.tuerca-usuario span{display:block;font-size:.78rem;color:var(--tenue);word-break:break-all}
.tuerca-grupo h3{font-size:.72rem;letter-spacing:.15em;text-transform:uppercase;color:var(--muy-tenue);
  margin-bottom:9px}
.tuerca-lista{display:grid;gap:7px}
.tuerca-item{
  display:flex;align-items:center;gap:12px;padding:12px 14px;border-radius:var(--radio-s);
  background:var(--panel);border:1px solid var(--linea);color:var(--texto);
  font:inherit;font-size:.88rem;font-weight:600;cursor:pointer;text-align:left;
  transition:.16s;width:100%;text-decoration:none;
}
.tuerca-item:hover{border-color:var(--oro);background:var(--panel-2);text-decoration:none;transform:translateX(3px)}
.tuerca-item .ico{width:30px;height:30px;border-radius:9px;display:grid;place-items:center;
  background:rgba(255,255,255,.05);font-size:.95rem;flex:0 0 auto}
.tuerca-item .flecha{margin-left:auto;color:var(--muy-tenue)}
.tuerca-item.activo{border-color:var(--verde);background:rgba(61,220,151,.08)}
.tuerca-item.activo .ico{background:rgba(61,220,151,.16);color:var(--verde)}

/* ---------- Secciones ---------- */
.seccion{padding:64px 0;border-top:1px solid var(--linea);scroll-margin-top:90px}
.seccion.alt{background:linear-gradient(180deg,rgba(255,255,255,.016),transparent)}
.seccion-cab{margin-bottom:30px;display:flex;align-items:flex-end;gap:16px;flex-wrap:wrap}
.seccion-cab .txt{flex:1;min-width:260px}
.seccion-num{font-size:.72rem;font-weight:900;letter-spacing:.24em;color:var(--oro);display:block;margin-bottom:6px}
.seccion-cab p{color:var(--tenue);margin:0;max-width:74ch}

/* ---------- Rejillas y tarjetas ---------- */
.rejilla{display:grid;gap:16px}
.r2{grid-template-columns:repeat(auto-fit,minmax(300px,1fr))}
.r3{grid-template-columns:repeat(auto-fit,minmax(258px,1fr))}
.r4{grid-template-columns:repeat(auto-fit,minmax(212px,1fr))}
.tarjeta{
  background:linear-gradient(160deg,var(--panel),var(--fondo-2));border:1px solid var(--linea);
  border-radius:var(--radio);padding:20px;transition:.2s;position:relative;overflow:hidden;
}
.tarjeta:hover{border-color:var(--linea-2);transform:translateY(-3px);box-shadow:var(--sombra)}
.tarjeta h3{margin-bottom:.35em}
.tarjeta p:last-child{margin-bottom:0}
.tarjeta .cuerpo{color:var(--tenue);font-size:.92rem}
.tarjeta-cab{display:flex;align-items:flex-start;gap:12px;margin-bottom:10px}
.tarjeta-cab h3{margin:0;flex:1}
.tarjeta-img{width:100%;aspect-ratio:16/9;object-fit:cover;border-radius:var(--radio-s);margin-bottom:13px}
.vacio{padding:34px 20px;text-align:center;color:var(--muy-tenue);border:1px dashed var(--linea-2);
  border-radius:var(--radio);font-size:.92rem}
.lista-puntos{margin:.6em 0 0;padding-left:1.15em;color:var(--tenue);font-size:.9rem}
.lista-puntos li{margin-bottom:.34em}

/* ---------- Insignias de equipo ---------- */
.escudo{
  width:52px;height:52px;border-radius:13px;object-fit:cover;flex:0 0 auto;
  background:linear-gradient(140deg,var(--linea-2),var(--panel));border:1px solid var(--linea-2);
}
.escudo.lg{width:74px;height:74px;border-radius:18px}
.escudo.sm{width:34px;height:34px;border-radius:9px}
.escudo-ini{width:52px;height:52px;border-radius:13px;display:grid;place-items:center;flex:0 0 auto;
  background:linear-gradient(140deg,var(--linea-2),var(--panel-2));border:1px solid var(--linea-2);
  font-weight:900;font-size:1.15rem;color:var(--oro)}
.escudo-ini.lg{width:74px;height:74px;border-radius:18px;font-size:1.6rem}
.equipo{display:flex;align-items:center;gap:13px}
.equipo strong{display:block;line-height:1.25}
.equipo span{display:block;font-size:.8rem;color:var(--tenue)}
.equipos{display:grid;gap:13px;grid-template-columns:repeat(auto-fill,minmax(276px,1fr))}

/* ---------- Pestañas de LIGA ---------- */
.pestanas{display:flex;gap:6px;flex-wrap:wrap;padding:6px;border-radius:999px;
  background:var(--panel);border:1px solid var(--linea);width:fit-content;max-width:100%;margin-bottom:26px}
.pestanas button{
  padding:.6em 1.15em;border:0;border-radius:999px;background:transparent;color:var(--tenue);
  font:inherit;font-size:.84rem;font-weight:800;cursor:pointer;transition:.16s;white-space:nowrap;
}
.pestanas button:hover{color:var(--texto)}
.pestanas button[aria-selected="true"]{background:linear-gradient(135deg,var(--oro),#dfa92e);color:#1a1405}
.panel-liga{display:none;animation:aparecer .3s ease}
.panel-liga.activo{display:block}
@keyframes aparecer{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}

/* ---------- Tablas ---------- */
.tabla-caja{overflow-x:auto;border:1px solid var(--linea);border-radius:var(--radio);background:var(--panel)}
table{width:100%;border-collapse:collapse;font-size:.89rem;min-width:560px}
caption{text-align:left;padding:15px 17px 0;font-weight:800;color:var(--tenue);font-size:.8rem;
  letter-spacing:.1em;text-transform:uppercase}
th,td{padding:11px 14px;text-align:left;border-bottom:1px solid var(--linea)}
thead th{font-size:.7rem;letter-spacing:.12em;text-transform:uppercase;color:var(--muy-tenue);
  background:rgba(255,255,255,.022);position:sticky;top:0}
tbody tr:last-child td{border-bottom:0}
tbody tr:hover{background:rgba(255,255,255,.022)}
td.num,th.num{text-align:center;font-variant-numeric:tabular-nums}
.pos{display:inline-grid;place-items:center;width:24px;height:24px;border-radius:7px;
  background:var(--panel-2);border:1px solid var(--linea-2);font-size:.78rem;font-weight:900}
.pos.p1{background:rgba(245,196,81,.2);border-color:var(--oro);color:var(--oro)}
.pos.p2{background:rgba(191,199,214,.16);border-color:#a9b3c8;color:#d5dcea}
.pos.p3{background:rgba(198,127,63,.18);border-color:#c07f3f;color:#e0a06a}

/* ---------- Partidos ---------- */
.partido{
  display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:13px;
  padding:14px 16px;border:1px solid var(--linea);border-radius:var(--radio);background:var(--panel);
}
.partido .lado{display:flex;align-items:center;gap:10px;min-width:0}
.partido .lado.der{justify-content:flex-end;text-align:right}
.partido .nombre{font-weight:700;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.marcador{
  min-width:78px;text-align:center;padding:.4em .6em;border-radius:var(--radio-s);
  background:var(--panel-2);border:1px solid var(--linea-2);font-weight:900;
  font-size:1.06rem;font-variant-numeric:tabular-nums;flex:0 0 auto;
}
.marcador.final{border-color:var(--oro);color:var(--oro)}
.marcador.vivo{border-color:var(--rojo);color:#ff9aa2}
.partidos-lista{display:grid;gap:9px}
.partido-meta{display:flex;gap:8px;align-items:center;flex-wrap:wrap;font-size:.78rem;color:var(--muy-tenue);
  margin-top:7px;padding-top:7px;border-top:1px dashed var(--linea)}
.informe{grid-column:1/-1;display:none;padding-top:12px;margin-top:4px;border-top:1px dashed var(--linea)}
.partido.abierto .informe{display:block}
.informe h4{font-size:.7rem;letter-spacing:.14em;text-transform:uppercase;color:var(--muy-tenue);margin:0 0 8px}
.eventos{display:grid;gap:6px}
.evento{display:flex;align-items:center;gap:9px;font-size:.86rem;padding:6px 10px;
  border-radius:9px;background:rgba(255,255,255,.028)}
.evento .min{font-weight:900;color:var(--oro);font-size:.78rem;min-width:38px;
  font-variant-numeric:tabular-nums}
.evento .ico-balon{font-size:.9rem}
.evento .quien{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.evento .tipo{font-size:.68rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muy-tenue)}
.cronica{display:flex;flex-wrap:wrap;gap:8px;margin-top:11px}
.cronica span{padding:.4em .75em;border-radius:999px;font-size:.78rem;font-weight:700;
  border:1px solid var(--linea-2);background:var(--panel-2)}
.cronica span.mvp{border-color:var(--oro);color:var(--oro);background:rgba(245,196,81,.1)}
.cronica span.cs{border-color:var(--diamante);color:var(--diamante);background:rgba(127,227,255,.08)}
.ver-informe{border:0;background:none;color:var(--diamante);font:inherit;font-size:.78rem;font-weight:700;
  cursor:pointer;padding:0;text-decoration:none}
.ver-informe:hover{text-decoration:underline}

/* ---------- Salas / Streamers / Donaciones ---------- */
.sala{display:flex;align-items:center;gap:13px;padding:16px;border-radius:var(--radio);
  background:var(--panel);border:1px solid var(--linea);flex-wrap:wrap}
.sala .info{flex:1;min-width:170px}
.sala .info strong{display:block}
.sala .info span{display:block;font-size:.8rem;color:var(--tenue);word-break:break-all}
.punto{width:9px;height:9px;border-radius:50%;flex:0 0 auto}
.punto.verde{background:var(--verde);box-shadow:0 0 0 4px rgba(61,220,151,.16);animation:pulso 2s infinite}
.punto.roja{background:var(--rojo);box-shadow:0 0 0 4px rgba(255,95,109,.16)}
.punto.gris{background:var(--muy-tenue)}
@keyframes pulso{50%{box-shadow:0 0 0 9px rgba(61,220,151,0)}}
.embed{position:relative;aspect-ratio:16/9;border-radius:var(--radio);overflow:hidden;
  border:1px solid var(--linea);background:#000;margin-bottom:13px}
.embed iframe{position:absolute;inset:0;width:100%;height:100%;border:0}
.embed .cargando{position:absolute;inset:0;display:grid;place-items:center;color:var(--muy-tenue);
  font-size:.85rem;background:var(--panel)}
.meta{position:absolute;left:11px;bottom:11px;display:flex;gap:7px;align-items:center}
.embed .ocultar{position:absolute;right:11px;bottom:11px}
.meta-donacion{height:11px;border-radius:999px;background:var(--panel-2);overflow:hidden;
  border:1px solid var(--linea);margin:11px 0 7px}
.meta-donacion i{display:block;height:100%;background:linear-gradient(90deg,var(--oro),var(--oro-2))}

/* ---------- Formularios ---------- */
.campo{display:grid;gap:6px;margin-bottom:15px}
.campo label{font-size:.8rem;font-weight:800;letter-spacing:.05em;color:var(--tenue);
  text-transform:uppercase}
.campo .pista{font-size:.78rem;color:var(--muy-tenue)}
input[type=text],input[type=email],input[type=password],input[type=number],input[type=date],
input[type=time],input[type=datetime-local],input[type=search],select,textarea{
  width:100%;padding:.72em .9em;border:1px solid var(--linea-2);border-radius:var(--radio-s);
  background:var(--fondo-2);color:var(--texto);font:inherit;font-size:.94rem;transition:.16s;
}
input:focus,select:focus,textarea:focus{outline:0;border-color:var(--oro);
  box-shadow:0 0 0 3px rgba(245,196,81,.14)}
input[type=file]{width:100%;font-size:.85rem;color:var(--tenue);
  padding:.6em;border:1px dashed var(--linea-2);border-radius:var(--radio-s);background:var(--fondo-2)}
input[type=file]::file-selector-button{margin-right:11px;padding:.45em .95em;border:0;
  border-radius:8px;background:var(--oro);color:#1a1405;font:inherit;font-weight:800;cursor:pointer}
textarea{min-height:110px;resize:vertical;line-height:1.6}
select{appearance:none;background-image:linear-gradient(45deg,transparent 50%,var(--tenue) 50%),
  linear-gradient(135deg,var(--tenue) 50%,transparent 50%);
  background-position:calc(100% - 19px) 55%,calc(100% - 13px) 55%;
  background-size:6px 6px,6px 6px;background-repeat:no-repeat;padding-right:2.6em}
.casilla{display:flex;align-items:flex-start;gap:10px;font-size:.88rem;cursor:pointer}
.casilla input{width:auto;margin-top:.28em;flex:0 0 auto}
.aviso{padding:12px 15px;border-radius:var(--radio-s);font-size:.88rem;margin-bottom:16px;
  border:1px solid var(--linea-2);background:var(--panel)}
.aviso.ok{border-color:rgba(61,220,151,.45);background:rgba(61,220,151,.09);color:#a7f0cd}
.avoso.error,.aviso.error{border-color:rgba(255,95,109,.45);background:rgba(255,95,109,.1);color:#ffb0b6}
.aviso.aviso-info{border-color:rgba(127,227,255,.4);background:rgba(127,227,255,.08);color:#b8ecff}
.aviso ul{margin:.4em 0 0;padding-left:1.15em}

/* ---------- Acceso ---------- */
.acceso{min-height:100vh;display:grid;place-items:center;padding:34px 20px;
  background:radial-gradient(880px 520px at 50% -12%,rgba(245,196,81,.13),transparent 62%),var(--fondo)}
.acceso-caja{width:100%;max-width:452px;background:linear-gradient(165deg,var(--panel),var(--fondo-2));
  border:1px solid var(--linea);border-radius:22px;padding:32px;box-shadow:var(--sombra)}
.acceso-logo{width:64px;height:64px;margin:0 auto 17px;border-radius:18px;object-fit:cover}
.acceso-logo-fallback{width:64px;height:64px;margin:0 auto 17px;border-radius:18px;display:grid;
  place-items:center;background:linear-gradient(135deg,var(--oro),#c9932a);color:#1a1405;
  font-weight:900;font-size:1.5rem}
.acceso h1{font-size:1.42rem;text-align:center;margin-bottom:5px}
.acceso .sub{text-align:center;color:var(--tenue);font-size:.9rem;margin-bottom:23px}
.acceso-pie{margin-top:19px;padding-top:17px;border-top:1px solid var(--linea);
  text-align:center;font-size:.88rem;color:var(--tenue)}
.acceso-pie a{font-weight:700}
.acceso-dato{margin-top:17px;padding:12px 14px;border-radius:var(--radio-s);background:rgba(127,227,255,.07);
  border:1px solid rgba(127,227,255,.3);font-size:.81rem;color:#b8ecff}
.divisor{display:flex;align-items:center;gap:13px;margin:19px 0;color:var(--muy-tenue);
  font-size:.75rem;letter-spacing:.13em;text-transform:uppercase}
.divisor::before,.divisor::after{content:"";flex:1;height:1px;background:var(--linea)}

/* ---------- Portada ---------- */
.hero{padding:78px 0 54px;text-align:center;position:relative;overflow:hidden}
.hero h1{background:linear-gradient(135deg,#fff 12%,var(--oro-2) 52%,var(--oro) 88%);
  -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}
.hero .lema{font-size:clamp(1rem,2.1vw,1.2rem);color:var(--tenue);max-width:66ch;margin:0 auto 27px}
.hero-escudo{width:104px;height:104px;margin:0 auto 22px;border-radius:26px;object-fit:cover;
  box-shadow:0 20px 60px rgba(245,196,81,.28)}
.hero-escudo-fallback{width:104px;height:104px;margin:0 auto 22px;border-radius:26px;
  display:grid;place-items:center;background:linear-gradient(135deg,var(--oro),#c9932a);
  color:#1a1405;font-weight:900;font-size:2.1rem;box-shadow:0 20px 60px rgba(245,196,81,.3)}
.hero-acciones{display:flex;gap:11px;justify-content:center;flex-wrap:wrap}
.marcas{display:flex;gap:34px;justify-content:center;flex-wrap:wrap;margin-top:48px}
.marca-dato{text-align:center}
.marca-dato b{display:block;font-size:clamp(1.5rem,3.4vw,2.1rem);
  background:linear-gradient(135deg,var(--oro-2),var(--oro));-webkit-background-clip:text;
  background-clip:text;-webkit-text-fill-color:transparent;font-variant-numeric:tabular-nums}
.marca-dato span{display:block;font-size:.7rem;letter-spacing:.15em;text-transform:uppercase;color:var(--muy-tenue)}
.marquee{border-block:1px solid var(--linea);padding:15px 0;overflow:hidden;
  background:rgba(255,255,255,.014)}
.marquee-pista{display:flex;gap:38px;width:max-content;animation:correr 34s linear infinite}
.marquee span{font-size:.76rem;font-weight:800;letter-spacing:.14em;text-transform:uppercase;
  color:var(--muy-tenue);white-space:nowrap}
.marquee span::before{content:"◆";color:var(--oro);margin-right:11px;font-size:.6rem}
@keyframes correr{to{transform:translateX(-50%)}}

/* ---------- Pie ---------- */
.pie{border-top:1px solid var(--linea);padding:44px 0 28px;margin-top:20px;background:rgba(0,0,0,.22)}
.pie-cols{display:grid;gap:28px;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));margin-bottom:28px}
.pie h4{font-size:.72rem;letter-spacing:.15em;text-transform:uppercase;color:var(--muy-tenue);margin-bottom:11px}
.pie ul{list-style:none;margin:0;padding:0;display:grid;gap:7px;font-size:.88rem}
.pie a{color:var(--tenue)}
.pie a:hover{color:var(--oro)}
.pie-fina{border-top:1px solid var(--linea);padding-top:19px;display:flex;justify-content:space-between;
  gap:13px;flex-wrap:wrap;font-size:.79rem;color:var(--muy-tenue)}

/* ---------- Panel ---------- */
.panel-envoltura{display:grid;grid-template-columns:246px 1fr;min-height:100vh}
.panel-lateral{background:var(--fondo-2);border-right:1px solid var(--linea);padding:18px;
  position:sticky;top:0;height:100vh;overflow-y:auto}
.panel-lateral h2{font-size:.76rem;letter-spacing:.15em;text-transform:uppercase;color:var(--muy-tenue);
  margin:19px 0 8px}
.panel-lateral h2:first-child{margin-top:0}
.panel-menu{display:grid;gap:3px}
.panel-menu button{display:flex;align-items:center;gap:10px;width:100%;padding:9px 11px;border:0;
  border-radius:9px;background:transparent;color:var(--tenue);font:inherit;font-size:.87rem;
  font-weight:600;cursor:pointer;text-align:left;transition:.14s}
.panel-menu button:hover{background:var(--panel);color:var(--texto)}
.panel-menu button[aria-current="true"]{background:rgba(245,196,81,.13);color:var(--oro);font-weight:800}
.panel-contenido{padding:26px 30px;min-width:0}
.panel-cab{display:flex;align-items:center;gap:15px;flex-wrap:wrap;margin-bottom:22px}
.panel-cab h1{font-size:1.42rem;margin:0;flex:1}
.estadisticas{display:grid;gap:13px;grid-template-columns:repeat(auto-fit,minmax(158px,1fr));margin-bottom:24px}
.estadistica{padding:17px;border-radius:var(--radio);background:var(--panel);border:1px solid var(--linea)}
.estadistica b{display:block;font-size:1.75rem;font-variant-numeric:tabular-nums;line-height:1.15}
.estadistica span{display:block;font-size:.71rem;letter-spacing:.13em;text-transform:uppercase;color:var(--muy-tenue)}
.fila-datos{display:flex;align-items:center;gap:12px;padding:12px 14px;border:1px solid var(--linea);
  border-radius:var(--radio-s);background:var(--panel);margin-bottom:8px;flex-wrap:wrap}
.fila-datos .crece{flex:1;min-width:160px}
.fila-datos .acciones{display:flex;gap:6px;flex-wrap:wrap}
.sub-tarjeta{background:var(--fondo-2);border:1px solid var(--linea);border-radius:var(--radio);
  padding:17px;margin-top:14px}
.sub-tarjeta h4{font-size:.8rem;letter-spacing:.1em;text-transform:uppercase;color:var(--tenue);margin-bottom:11px}
.jug-fila{display:grid;grid-template-columns:64px 1fr 130px 1fr auto;gap:9px;align-items:center;margin-bottom:7px}
@media (max-width:760px){
  .jug-fila{grid-template-columns:56px 1fr;grid-template-areas:"dorsal nombre" "puesto puesto" "nota nota"}
  .jug-fila>*:nth-child(1){grid-area:dorsal}.jug-fila>*:nth-child(2){grid-area:nombre}
  .jug-fila>*:nth-child(3){grid-area:puesto}.jug-fila>*:nth-child(4){grid-area:nota}}
.ev-fila{display:grid;grid-template-columns:1fr 1fr 96px 92px auto;gap:9px;align-items:center;margin-bottom:7px}
@media (max-width:760px){
  .ev-fila{grid-template-columns:1fr 1fr;grid-template-areas:"jugador jugador" "tipo minuto" "x x"}
  .ev-fila>*:nth-child(1){grid-area:jugador}.ev-fila>*:nth-child(2){grid-area:tipo}
  .ev-fila>*:nth-child(3){grid-area:minuto}.ev-fila>*:nth-child(4){grid-area:x}}

/* ---------- Utilidades ---------- */
.sr-salto{position:absolute;left:-9999px}
.sr-salto:focus{left:20px;top:20px;z-index:200;padding:11px 19px;border-radius:10px;
  background:var(--oro);color:#1a1405;font-weight:800}
.volver-arriba{position:fixed;right:20px;bottom:20px;width:44px;height:44px;border-radius:50%;
  display:grid;place-items:center;background:var(--oro);color:#1a1405;border:0;font-size:1.1rem;
  cursor:pointer;opacity:0;pointer-events:none;transition:.22s;z-index:55;box-shadow:var(--sombra)}
.volver-arriba.visible{opacity:1;pointer-events:auto}
.volver-arriba:hover{transform:translateY(-3px)}
.barra-progreso{position:fixed;left:0;top:0;height:2px;background:linear-gradient(90deg,var(--oro),var(--diamante));
  z-index:70;width:0;transition:width .1s linear}
.revelar{opacity:0;transform:translateY(22px);transition:opacity .55s ease,transform .55s ease}
.revelar.visto{opacity:1;transform:none}
dialog{border:0;padding:0;background:transparent;color:var(--texto);max-width:min(560px,92vw)}
dialog::backdrop{background:rgba(0,0,0,.72)}
.modal{background:var(--fondo-2);border:1px solid var(--linea);border-radius:18px;padding:24px}
.modal h3{margin-bottom:14px}

@media (max-width:980px){
  .panel-envoltura{grid-template-columns:1fr}
  .panel-lateral{position:static;height:auto;border-right:0;border-bottom:1px solid var(--linea)}
  .panel-contenido{padding:20px}
}
@media (max-width:760px){
  .seccion{padding:44px 0}
  .hero{padding:52px 0 36px}
  .partido{grid-template-columns:1fr;gap:9px}
  .partido .lado.der{justify-content:flex-start;text-align:left;flex-direction:row-reverse}
  .marcador{justify-self:center}
  .nav{width:100%;margin-left:0;overflow-x:auto;padding-bottom:3px;flex-wrap:nowrap}
  .nav a{font-size:.68rem;padding:.5em .6em}
  .cabecera-fila{flex-wrap:wrap}
}
@media print{
  .cabecera,.pie,.tuerca-caja,.tuerca-velo,.volver-arriba,.barra-progreso,.hero-acciones{display:none!important}
  body{background:#fff;color:#000}
}
"""

# ==============================================================================
#  JAVASCRIPT DEL SITIO (sin dependencias)
# ==============================================================================

JS = r"""
(function(){
  "use strict";
  var d = document;

  /* --- Tuerca de configuración --- */
  var caja = d.getElementById("tuerca");
  var velo = d.getElementById("tuerca-velo");
  function abrirTuerca(estado){
    if(!caja) return;
    caja.classList.toggle("abierta", estado);
    if(velo) velo.classList.toggle("visible", estado);
    d.body.style.overflow = estado ? "hidden" : "";
    if(estado){
      var primero = caja.querySelector("a,button");
      if(primero) primero.focus();
    }
  }
  d.querySelectorAll("[data-tuerca]").forEach(function(b){
    b.addEventListener("click", function(){ abrirTuerca(true); });
  });
  d.querySelectorAll("[data-cerrar-tuerca]").forEach(function(b){
    b.addEventListener("click", function(){ abrirTuerca(false); });
  });
  if(velo) velo.addEventListener("click", function(){ abrirTuerca(false); });

  /* --- Sub-pestañas de LIGA --- */
  d.querySelectorAll("[data-pestanas]").forEach(function(grupo){
    var botones = grupo.querySelectorAll("button");
    var paneles = d.querySelectorAll("#" + grupo.dataset.pestanas + " > .panel-liga");
    function activar(id){
      botones.forEach(function(b){ b.setAttribute("aria-selected", String(b.dataset.panel === id)); });
      paneles.forEach(function(p){ p.classList.toggle("activo", p.id === id); });
      try{ history.replaceState(null, "", "#" + id); }catch(e){}
    }
    botones.forEach(function(b){ b.addEventListener("click", function(){ activar(b.dataset.panel); }); });
    var inicial = (location.hash || "").replace("#", "");
    if(inicial && d.getElementById(inicial) && d.getElementById(inicial).classList.contains("panel-liga")){
      activar(inicial);
    }
  });

  /* --- Informes de partido desplegables --- */
  d.querySelectorAll(".ver-informe").forEach(function(boton){
    boton.addEventListener("click", function(){
      var partido = boton.closest(".partido");
      if(!partido) return;
      var abierto = partido.classList.toggle("abierto");
      boton.textContent = abierto ? "Ocultar informe" : "Ver informe";
      boton.setAttribute("aria-expanded", String(abierto));
    });
  });

  /* --- Aparecer al hacer scroll --- */
  var revelables = d.querySelectorAll(".revelar");
  if(revelables.length && "IntersectionObserver" in window){
    var obs = new IntersectionObserver(function(entradas){
      entradas.forEach(function(e){
        if(e.isIntersecting){ e.target.classList.add("visto"); obs.unobserve(e.target); }
      });
    }, { threshold:.08, rootMargin:"0px 0px -40px 0px" });
    revelables.forEach(function(el){ obs.observe(el); });
  } else {
    revelables.forEach(function(el){ el.classList.add("visto"); });
  }

  /* --- Barra de progreso y volver arriba --- */
  var barra = d.getElementById("barra-progreso");
  var arriba = d.getElementById("volver-arriba");
  function alDesplazar(){
    var alto = d.documentElement.scrollHeight - window.innerHeight;
    var pct = alto > 0 ? (window.scrollY / alto) * 100 : 0;
    if(barra) barra.style.width = pct + "%";
    if(arriba) arriba.classList.toggle("visible", window.scrollY > 500);
  }
  window.addEventListener("scroll", alDesplazar, { passive:true });
  alDesplazar();
  if(arriba) arriba.addEventListener("click", function(){ window.scrollTo({ top:0, behavior:"smooth" }); });

  /* --- Resaltar la entrada activa del menú --- */
  var enlaces = Array.prototype.slice.call(d.querySelectorAll(".nav a[href^='#']"));
  var observados = enlaces.map(function(a){
    var id = a.getAttribute("href").slice(1);
    var seccion = d.getElementById(id);
    return seccion ? { a:a, seccion:seccion } : null;
  }).filter(Boolean);
  if(observados.length && "IntersectionObserver" in window){
    var spy = new IntersectionObserver(function(entradas){
      entradas.forEach(function(e){
        if(!e.isIntersecting) return;
        enlaces.forEach(function(a){ a.classList.remove("activo"); });
        var found = observados.filter(function(o){ return o.seccion === e.target; })[0];
        if(found) found.a.classList.add("activo");
      });
    }, { rootMargin:"-45% 0px -50% 0px" });
    observados.forEach(function(o){ spy.observe(o.seccion); });
  }

  /* --- Contador animado de la portada --- */
  var contadores = d.querySelectorAll("[data-contar]");
  if(contadores.length){
    var animado = new IntersectionObserver(function(entradas){
      entradas.forEach(function(e){
        if(!e.isIntersecting) return;
        var el = e.target, fin = parseFloat(el.dataset.contar) || 0, t0 = null;
        function paso(ts){
          if(!t0) t0 = ts;
          var p = Math.min((ts - t0) / 1100, 1);
          var v = fin * (1 - Math.pow(1 - p, 3));
          el.textContent = Number.isInteger(fin) ? Math.round(v) : v.toFixed(1);
          if(p < 1) requestAnimationFrame(paso);
        }
        requestAnimationFrame(paso);
        animado.unobserve(el);
      });
    }, { threshold:.4 });
    contadores.forEach(function(el){ animado.observe(el); });
  }

  /* --- Confirmación en acciones destructivas --- */
  d.querySelectorAll("form[data-confirmar]").forEach(function(form){
    form.addEventListener("submit", function(ev){
      if(!window.confirm(form.dataset.confirmar)) ev.preventDefault();
    });
  });

  /* --- Ocultar el aviso de carga cuando el iframe del directo responde --- */
  d.querySelectorAll(".embed iframe").forEach(function(iframe){
    var marco = iframe.closest(".embed");
    var carga = marco && marco.querySelector(".cargando");
    if(!marco || !carga) return;
    iframe.addEventListener("load", function(){ carga.style.display = "none"; });
  });
})();
"""
# ==============================================================================
#  PLANTILLAS
# ==============================================================================

# Las once entradas de la cabecera, en este orden.
NAVEGACION = [
    ("liga", "LIGA", "Liga: formato, divisiones, fechas, equipos y clasificación"),
    ("pubs", "PUBS", "Salas de HaxBall de la liga"),
    ("museo", "MUSEO", "Museo: todos los premios entregados, antiguos y recientes"),
    ("noticias", "NOTICIAS", "Reportarios y noticias recientes de la liga"),
    ("anuncios", "ANUNCIOS - NOVEDADES", "Novedades y comunicados de la liga"),
    ("alianzas", "ALIANZAS", "Afiliaciones y la próxima alianza"),
    ("redes", "REDES SOCIALES", "Redes de la liga y de nuestros streamers"),
    ("equipo", "EQUIPO ADMINISTRACION", "Todo el equipo administrativo"),
    ("tuerca", "TUERCA DE CONFIGURACION",
     "Cerrar sesión, perfil, contraseña, Google, modo premium y modo administrador"),
    ("live", "LIVE FUTBOL", "Partidos de fútbol en vivo, tipo Kick o Twitch"),
    ("donacion", "DONACION", "Donaciones, divisiones y estadísticas de la liga"),
]

app.jinja_env.filters.update({
    "corta": lambda v, m=140: texto_corto(v, m),
    "fecha": fecha_larga,
    "fecha_corta": fecha_corta,
    "fecha_hora": fecha_hora,
    "numero": numero,
    "hora": hora,
    "estado": estado_texto,
    "fase": fase_texto,
    "plural": plural,
    "buscar": buscar_normalizado,
    "red": lambda n: NOMBRES_RED.get(n, str(n or "").capitalize()),
})
app.jinja_env.globals.update({
    "csrf_campo": csrf_campo,
    "nombre_red": lambda n: NOMBRES_RED.get(n, str(n or "").capitalize()),
    "posiciones": POSICIONES,
    "plural": plural,
})


# ==============================================================================
#  BASE
# ==============================================================================

TPL_BASE = """
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="{{ 'noindex,nofollow' if noindex else 'index,follow' }}">
<title>{{ titulo }}</title>
<meta name="description" content="{{ descripcion }}">
<meta name="theme-color" content="#07080d">
<meta property="og:type" content="website">
<meta property="og:title" content="{{ titulo }}">
<meta property="og:description" content="{{ descripcion }}">
<meta property="og:url" content="{{ url_base }}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{{ url_for('assets_archivo', nombre='favicon.png') }}">
<style>{{ css }}</style>
</head>
<body>
<a class="sr-salto" href="#contenido">Saltar al contenido</a>

<header class="cabecera">
  <div class="envoltura cabecera-fila">
    <a class="marca" href="{{ url_for('portada') }}">
      {% if escudo %}
        <img src="{{ escudo }}" alt="Escudo de {{ ajustes.leagueName }}" width="42" height="42">
      {% else %}
        <span class="marca-escudo">{{ ajustes.shortName }}</span>
      {% endif %}
      <span class="marca-txt">
        <strong>{{ ajustes.leagueName }}</strong>
        <span>{{ ajustes.season or 'Liga de HaxBall' }}</span>
      </span>
    </a>

    <nav class="nav" aria-label="Secciones de la liga">
      {% for clave, texto, ayuda in navegacion %}
        {% if clave == 'tuerca' %}
          <button type="button" class="tuerca-btn" data-tuerca title="{{ texto }}"
                  aria-label="{{ texto }}" aria-haspopup="dialog">&#9881;</button>
        {% else %}
          <a href="#{{ clave }}" title="{{ ayuda }}">{{ texto }}</a>
        {% endif %}
      {% endfor %}
      <span class="sesion-chip">
        <span class="punto"></span>{{ usuario.username }}
        {% if usuario.is_premium %}<span class="etiqueta oro">PREMIUM</span>{% endif %}
        {% if usuario.is_admin %}<span class="etiqueta violeta">ADMIN</span>{% endif %}
      </span>
    </nav>
  </div>
</header>

<div class="barra-progreso" id="barra-progreso"></div>

{% block contenido %}{% endblock %}

<div class="tuerca-velo" id="tuerca-velo" data-cerrar-tuerca></div>
<aside class="tuerca-caja" id="tuerca" role="dialog" aria-modal="true"
       aria-label="Tuerca de configuración">
  <div class="tuerca-cab">
    <h2>TUERCA DE CONFIGURACION</h2>
    <button type="button" class="btn pequeno fantasma" data-cerrar-tuerca
            aria-label="Cerrar">&times;</button>
  </div>
  <div class="tuerca-cuerpo">
    <div class="tuerca-usuario">
      {% if usuario.avatar_url %}
        <img src="{{ usuario.avatar_url }}" alt="Foto de {{ usuario.username }}"
             width="52" height="52">
      {% else %}
        <span class="ini">{{ usuario.username[:1]|upper }}</span>
      {% endif %}
      <span style="min-width:0">
        <strong>{{ usuario.display_name or usuario.username }}</strong>
        <span>{{ usuario.email }}</span>
      </span>
    </div>

    <div class="tuerca-grupo">
      <h3>Cuenta</h3>
      <div class="tuerca-lista">
        <a class="tuerca-item" href="{{ url_for('perfil') }}">
          <span class="ico">&#128100;</span> Editar perfil <span class="flecha">&rsaquo;</span></a>
        <a class="tuerca-item" href="{{ url_for('password') }}">
          <span class="ico">&#128273;</span> Cambiar contraseña <span class="flecha">&rsaquo;</span></a>
        {% if google_activo %}
        {% if usuario.google_id %}
          <form class="tuerca-item" method="post" action="{{ url_for('google_quitar') }}">
            {{ csrf_campo() }}
            <span class="ico">G</span> Desvincular Google
            <span class="flecha">&rsaquo;</span>
          </form>
        {% else %}
          <a class="tuerca-item" href="{{ url_for('google_entrar') }}">
            <span class="ico">G</span> Vincular Google
            <span class="flecha">&rsaquo;</span></a>
        {% endif %}
        {% endif %}
        <a class="tuerca-item" href="{{ url_for('datos') }}">
          <span class="ico">&#128190;</span> Mis datos <span class="flecha">&rsaquo;</span></a>
        <a class="tuerca-item" href="{{ url_for('privacidad') }}">
          <span class="ico">&#128274;</span> Privacidad <span class="flecha">&rsaquo;</span></a>
      </div>
    </div>

    <div class="tuerca-grupo">
      <h3>Modos</h3>
      <div class="tuerca-lista">
        <form method="post" action="{{ url_for('premium') }}">
          {{ csrf_campo() }}
          <button type="submit" class="tuerca-item {{ 'activo' if usuario.is_premium }}">
            <span class="ico">&#11088;</span> Modo premium
            <span class="flecha">{{ 'ACTIVO' if usuario.is_premium else 'ACTIVAR' }}</span>
          </button>
        </form>
        {% if usuario.is_admin %}
        <a class="tuerca-item activo" href="{{ url_for('panel') }}">
          <span class="ico">&#128737;</span> Modo administrador <span class="flecha">&rsaquo;</span></a>
        {% else %}
        <span class="tuerca-item" style="opacity:.45;cursor:not-allowed">
          <span class="ico">&#128737;</span> Modo administrador
          <span class="flecha">NO DISPONIBLE</span></span>
        {% endif %}
      </div>
    </div>

    <div class="tuerca-grupo">
      <form method="post" action="{{ url_for('salir') }}">
        {{ csrf_campo() }}
        <button type="submit" class="tuerca-item" style="border-color:rgba(255,95,109,.4)">
          <span class="ico">&#128682;</span> Cerrar sesión
        </button>
      </form>
    </div>
  </div>
</aside>

<footer class="pie">
  <div class="envoltura">
    <div class="pie-cols">
      <div>
        <h4>{{ ajustes.leagueName }}</h4>
        <p class="tenue" style="font-size:.88rem">
          {{ ajustes.tagline or 'Liga competitiva de HaxBall X5' }}</p>
        {% if ajustes.status %}<span class="etiqueta verde">{{ ajustes.status }}</span>{% endif %}
      </div>
      <div>
        <h4>Liga</h4>
        <ul>
          <li><a href="#liga">Formato y divisiones</a></li>
          <li><a href="#liga">Fechas y calendario</a></li>
          <li><a href="#liga">Equipos y jugadores</a></li>
          <li><a href="#pubs">Salas de juego</a></li>
        </ul>
      </div>
      <div>
        <h4>Comunidad</h4>
        <ul>
          <li><a href="#noticias">Noticias</a></li>
          <li><a href="#anuncios">Anuncios y novedades</a></li>
          <li><a href="#museo">Museo de premios</a></li>
          <li><a href="#redes">Redes sociales</a></li>
        </ul>
      </div>
      <div>
        <h4>Cuenta</h4>
        <ul>
          <li><a href="{{ url_for('perfil') }}">Editar perfil</a></li>
          <li><a href="{{ url_for('password') }}">Cambiar contraseña</a></li>
          <li><a href="{{ url_for('privacidad') }}">Privacidad</a></li>
          {% if usuario.is_admin %}
          <li><a href="{{ url_for('panel') }}">Panel de administración</a></li>
          {% endif %}
        </ul>
      </div>
    </div>
    <div class="pie-fina">
      <span>© {{ anio }} {{ ajustes.leagueName }}. Todos los derechos reservados.</span>
      <span>neptun · andres · <a href="https://github.com/Dvskked" rel="noopener">Dvskked</a></span>
    </div>
  </div>
</footer>

<button class="volver-arriba" id="volver-arriba" aria-label="Volver arriba">&#8593;</button>
<script>{{ js }}</script>
</body>
</html>
"""


# ==============================================================================
#  ACCESO Y REGISTRO
# ==============================================================================

TPL_ACCESO = """
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>{{ titulo }}</title>
<meta name="description" content="{{ descripcion }}">
<link rel="icon" href="{{ url_for('assets_archivo', nombre='favicon.png') }}">
<style>{{ css }}</style>
</head>
<body>
<main class="acceso">
  <div class="acceso-caja">
    {% if logo %}
      <img class="acceso-logo" src="{{ logo }}" alt="Escudo de la liga" width="64" height="64">
    {% else %}
      <div class="acceso-logo-fallback">{{ ajustes.shortName }}</div>
    {% endif %}
    <h1>{{ encabezado }}</h1>
    <p class="sub">{{ sub }}</p>

    {% if errores %}
      <div class="aviso error"><strong>Revisa esto:</strong>
        <ul>{% for err in errores %}<li>{{ err }}</li>{% endfor %}</ul></div>
    {% endif %}
    {% if aviso %}<div class="aviso ok">{{ aviso }}</div>{% endif %}
    {% if primer_usuario %}
      <div class="aviso aviso-info">
        Eres la primera cuenta de la liga: al registrarte entras como
        <strong>administrador</strong> y podrás gestionarlo todo desde el panel.
      </div>
    {% endif %}

    <form method="post" novalidate>
      {{ csrf_campo() }}
      {% if modo == 'registro' %}
        <div class="campo">
          <label for="username">Usuario</label>
          <input id="username" name="username" type="text" required autocomplete="username"
                 minlength="3" maxlength="32" pattern="[A-Za-z0-9_.\\-]{3,32}"
                 placeholder="tu_usuario" value="{{ datos.get('username', '') }}" autofocus>
          <span class="pista">3 a 32 caracteres: letras, números, punto, guion y guion bajo.</span>
        </div>
        <div class="campo">
          <label for="email">Correo electrónico</label>
          <input id="email" name="email" type="email" required autocomplete="email"
                 placeholder="tu@correo.com" value="{{ datos.get('email', '') }}">
          <span class="pista">Solo puede usarse una vez.</span>
        </div>
        <div class="campo">
          <label for="password">Contraseña</label>
          <input id="password" name="password" type="password" required minlength="8"
                 autocomplete="new-password" placeholder="Mínimo 8 caracteres">
        </div>
        <div class="campo">
          <label for="confirmar">Confirmar contraseña</label>
          <input id="confirmar" name="confirmar" type="password" required minlength="8"
                 autocomplete="new-password" placeholder="Repite la contraseña">
        </div>
        <div class="campo">
          <label class="casilla">
            <input type="checkbox" name="boletin" value="1">
            <span>Quiero recibir las novedades de la liga por correo.</span>
          </label>
        </div>
        <div class="campo">
          <label class="casilla">
            <input type="checkbox" name="acepta" value="1" required>
            <span>Acepto la <a href="{{ url_for('privacidad') }}" target="_blank" rel="noopener">
              política de privacidad</a> y el tratamiento de mis datos.</span>
          </label>
        </div>
        <button class="btn primario" type="submit" style="width:100%">Crear mi cuenta</button>
      {% else %}
        <div class="campo">
          <label for="identificador">Usuario o correo</label>
          <input id="identificador" name="identificador" type="text" required autofocus
                 autocomplete="username" placeholder="tu_usuario o tu@correo.com"
                 value="{{ datos.get('identificador', '') }}">
        </div>
        <div class="campo">
          <label for="password">Contraseña</label>
          <input id="password" name="password" type="password" required
                 autocomplete="current-password" placeholder="Tu contraseña">
        </div>
        <button class="btn primario" type="submit" style="width:100%">Entrar a la liga</button>
        {% if google_activo %}
          <div class="divisor">o</div>
          <a class="btn" href="{{ url_for('google_entrar') }}" style="width:100%">
            Continuar con Google</a>
        {% endif %}
      {% endif %}
    </form>

    <div class="acceso-pie">
      {% if modo == 'registro' %}
        ¿Ya tienes cuenta? <a href="{{ url_for('entrar') }}">Inicia sesión</a>
      {% else %}
        ¿Todavía no tienes cuenta? <a href="{{ url_for('registro') }}">Regístrate aquí</a>
      {% endif %}
    </div>

    {% if modo == 'entrar' %}
      <div class="acceso-dato">
        La liga es privada: sin una cuenta registrada no se ve ninguna sección.
      </div>
    {% endif %}
  </div>
</main>
</body>
</html>
"""


# ==============================================================================
#  CUENTA
# ==============================================================================

TPL_CUENTA = """
{% extends 'base.html' %}
{% block contenido %}
<main id="contenido" class="envoltura" style="padding-block:44px 70px;max-width:880px">
  <div class="seccion-cab">
    <div class="txt">
      <span class="seccion-num">{% if modo == 'perfil' %}PERFIL{% elif modo == 'password' %}SEGURIDAD{% elif modo == 'datos' %}PRIVACIDAD{% else %}ELIMINAR{% endif %}</span>
      <h1>{{ encabezado }}</h1>
      <p>{{ sub }}</p>
    </div>
    <button class="btn fantasma pequeno" type="button" data-tuerca>Abrir la tuerca</button>
  </div>

  {% if errores %}
    <div class="aviso error"><strong>Revisa esto:</strong>
      <ul>{% for err in errores %}<li>{{ err }}</li>{% endfor %}</ul></div>
  {% endif %}
  {% if ok %}<div class="aviso ok">{{ ok }}</div>{% endif %}

  {% if modo == 'perfil' %}
    <form method="post" enctype="multipart/form-data" class="tarjeta">
      {{ csrf_campo() }}
      <div class="rejilla r2" style="gap:0 17px">
        <div class="campo">
          <label for="username">Usuario</label>
          <input id="username" name="username" type="text" required minlength="3" maxlength="32"
                 value="{{ usuario.username }}">
        </div>
        <div class="campo">
          <label for="display_name">Nombre visible</label>
          <input id="display_name" name="display_name" type="text" maxlength="80"
                 value="{{ usuario.display_name }}">
        </div>
      </div>
      <div class="campo">
        <label for="email">Correo electrónico</label>
        <input id="email" name="email" type="email" required value="{{ usuario.email }}">
      </div>
      <div class="rejilla r2" style="gap:0 17px">
        <div class="campo">
          <label for="country">País</label>
          <input id="country" name="country" type="text" maxlength="60" value="{{ usuario.country }}">
        </div>
        <div class="campo">
          <label for="favorite_team">Equipo favorito</label>
          <input id="favorite_team" name="favorite_team" type="text" maxlength="80"
                 list="lista-equipos" value="{{ usuario.favorite_team }}">
          <datalist id="lista-equipos">
            {% for t in equipos %}<option value="{{ t.name }}">{% endfor %}
          </datalist>
        </div>
      </div>
      <div class="campo">
        <label for="bio">Biografía</label>
        <textarea id="bio" name="bio" maxlength="400">{{ usuario.bio }}</textarea>
      </div>
      <div class="campo">
        <label for="avatar">Foto de perfil</label>
        <input id="avatar" name="avatar" type="file" accept="image/*">
        <span class="pista">PNG, JPG, WEBP o GIF. Máximo 4 MB.</span>
        {% if usuario.avatar_url %}
          <div class="equipo" style="margin-top:9px">
            <img class="escudo" src="{{ usuario.avatar_url }}" alt="Tu foto actual"
                 width="52" height="52">
            <span class="tenue">Tu foto actual. Sube otra para cambiarla.</span>
          </div>
        {% endif %}
      </div>
      <div class="campo">
        <label class="casilla">
          <input type="checkbox" name="newsletter" value="1" {{ 'checked' if usuario.newsletter }}>
          <span>Recibir las novedades de la liga por correo.</span>
        </label>
      </div>
      <button class="btn primario" type="submit">Guardar cambios</button>
    </form>

  {% elif modo == 'password' %}
    <form method="post" class="tarjeta">
      {{ csrf_campo() }}
      <div class="campo">
        <label for="actual">Contraseña actual</label>
        <input id="actual" name="actual" type="password" autocomplete="current-password"
               {{ 'required' if usuario.password_hash }} {{ 'autofocus' if usuario.password_hash }}>
        {% if not usuario.password_hash %}
          <span class="pista">Tu cuenta se creó con Google: fija aquí tu primera contraseña.</span>
        {% endif %}
      </div>
      <div class="campo">
        <label for="nueva">Contraseña nueva</label>
        <input id="nueva" name="nueva" type="password" required minlength="8"
               autocomplete="new-password">
        <span class="pista">Mínimo 8 caracteres.</span>
      </div>
      <div class="campo">
        <label for="confirmar">Confirmar contraseña nueva</label>
        <input id="confirmar" name="confirmar" type="password" required minlength="8"
               autocomplete="new-password">
      </div>
      <button class="btn primario" type="submit">Cambiar contraseña</button>
    </form>

  {% elif modo == 'datos' %}
    <div class="tarjeta">
      <p class="tenue">Estos son todos los datos que tenemos de tu cuenta. Puedes copiarlos o
        descargarlos en formato JSON.</p>
      <table>
        <caption>Datos de la cuenta</caption>
        <tbody>
          <tr><th>Usuario</th><td>{{ usuario.username }}</td></tr>
          <tr><th>Correo</th><td>{{ usuario.email }}</td></tr>
          <tr><th>Nombre visible</th><td>{{ usuario.display_name or '—' }}</td></tr>
          <tr><th>País</th><td>{{ usuario.country or '—' }}</td></tr>
          <tr><th>Equipo favorito</th><td>{{ usuario.favorite_team or '—' }}</td></tr>
          <tr><th>Premium</th><td>{{ 'Sí' if usuario.is_premium else 'No' }}</td></tr>
          <tr><th>Administrador</th><td>{{ 'Sí' if usuario.is_admin else 'No' }}</td></tr>
          <tr><th>Cuenta creada</th><td>{{ usuario.created_at }}</td></tr>
          <tr><th>Último acceso</th><td>{{ usuario.last_login_at or '—' }}</td></tr>
        </tbody>
      </table>
      <div style="margin-top:15px;display:flex;gap:9px;flex-wrap:wrap">
        <a class="btn" href="{{ url_for('datos_json') }}">Descargar en JSON</a>
      </div>
    </div>

  {% elif modo == 'eliminar' %}
    <form method="post" class="tarjeta"
          data-confirmar="Vas a borrar tu cuenta para siempre. ¿Seguro?">
      {{ csrf_campo() }}
      <div class="aviso error">
        Esto borra tu cuenta, tu perfil y todos tus consentimientos. No se puede deshacer.
      </div>
      <div class="campo">
        <label class="casilla">
          <input type="checkbox" name="confirmar" value="BORRAR" required>
          <span>Entiendo que quiero eliminar mi cuenta de la liga.</span>
        </label>
      </div>
      <button class="btn peligro" type="submit">Eliminar mi cuenta</button>
    </form>
  {% endif %}
</main>
{% endblock %}
"""


# ==============================================================================
#  PRIVACIDAD Y ERRORES
# ==============================================================================

TPL_PRIVACIDAD = """
{% extends 'base.html' %}
{% block contenido %}
<main id="contenido" class="envoltura" style="padding-block:44px 70px;max-width:840px">
  <span class="seccion-num">LEGAL</span>
  <h1>Política de privacidad</h1>
  <p class="tenue">Versión {{ version }} · revisada el {{ fecha }}</p>
  <div class="tarjeta" style="margin-top:22px">
    <h3>Responsable del tratamiento</h3>
    <p>{{ empresa }} · contacto: <a href="mailto:{{ contacto }}">{{ contacto }}</a></p>

    <h3>Qué datos recogemos</h3>
    <p>Nombre de usuario, correo electrónico, contraseña cifrada, nombre visible, biografía,
      foto, país, equipo favorito y, si lo pides, tu suscripción al boletín. Guardamos también
      la IP y el navegador en el momento del registro y de cada acceso.</p>

    <h3>Para qué los usamos</h3>
    <p>Solo para gestionar tu cuenta dentro de la liga y para enviarte las novedades que
      pidas. No vendemos ni cedemos tus datos.</p>

    <h3>Contraseñas</h3>
    <p>Se guardan cifradas con bcrypt. Ni siquiera la administración puede leerlas.</p>

    <h3>Tus derechos</h3>
    <p>Puedes consultar, corregir, exportar y borrar tus datos cuando quieras desde la tuerca de
      configuración. Al borrarte la cuenta se elimina también tu historial de consentimientos.</p>

    <h3>Cookies</h3>
    <p>Solo usamos una cookie de sesión y una de seguridad (CSRF). No hay cookies de publicidad
      ni de seguimiento.</p>
  </div>
</main>
{% endblock %}
"""


TPL_ERROR = """
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>{{ codigo }} · {{ league }}</title>
<link rel="icon" href="{{ url_for('assets_archivo', nombre='favicon.png') }}">
<style>{{ css }}</style>
</head>
<body>
<main class="acceso">
  <div class="acceso-caja centrado">
    <div class="acceso-logo-fallback">{{ codigo }}</div>
    <h1>{{ titulo }}</h1>
    <p class="sub">{{ mensaje }}</p>
    <a class="btn primario" href="{{ destino }}">{{ accion }}</a>
  </div>
</main>
</body>
</html>
"""
# ==============================================================================
#  PORTADA: LAS ONCE SECCIONES
# ==============================================================================

TPL_PORTADA = """
{% extends 'base.html' %}
{% block contenido %}
<main id="contenido">

  {# ---------------------------------------------------------------- HERO #}
  <section class="hero">
    <div class="envoltura">
      {% if escudo %}
        <img class="hero-escudo" src="{{ escudo }}" alt="Escudo de {{ ajustes.leagueName }}"
             width="104" height="104">
      {% else %}
        <div class="hero-escudo-fallback">{{ ajustes.shortName }}</div>
      {% endif %}
      <span class="etiqueta oro">{{ ajustes.season or 'Temporada activa' }}</span>
      <h1>{{ ajustes.leagueName }}</h1>
      <p class="lema">{{ ajustes.description or ajustes.tagline
        or 'Liga competitiva de HaxBall X5 con divisiones, premios y datos de cada jugador.' }}</p>

      <div class="hero-acciones">
        <a class="btn primario" href="#liga">Ver la liga</a>
        {% if proximo %}
        <a class="btn" href="#liga">Próximo partido: {{ proximo.home }} vs {{ proximo.away }}</a>
        {% endif %}
        {% if ajustes.server %}
        <a class="btn fantasma" href="{{ ajustes.server }}" rel="noopener" target="_blank">Servidor</a>
        {% endif %}
      </div>

      <div class="marcas">
        <div class="marca-dato"><b data-contar="{{ totales.equipos }}">{{ totales.equipos }}</b><span>Equipos</span></div>
        <div class="marca-dato"><b data-contar="{{ totales.jugadores }}">{{ totales.jugadores }}</b><span>Jugadores</span></div>
        <div class="marca-dato"><b data-contar="{{ totales.partidos }}">{{ totales.partidos }}</b><span>Partidos</span></div>
        <div class="marca-dato"><b data-contar="{{ totales.premios }}">{{ totales.premios }}</b><span>Premios</span></div>
        <div class="marca-dato"><b data-contar="{{ totales.divisiones }}">{{ totales.divisiones }}</b><span>Divisiones</span></div>
      </div>
    </div>
  </section>

  <div class="marquee" aria-hidden="true">
    <div class="marquee-pista">
      {% for _ in range(2) %}
        {% for clave, texto, ayuda in navegacion %}<span>{{ texto }}</span>{% endfor %}
      {% endfor %}
    </div>
  </div>

  {# -------------------------------------------------------------- LIGA #}
  <section class="seccion" id="liga" aria-labelledby="liga-titulo">
    <div class="envoltura">
      <div class="seccion-cab">
        <div class="txt">
          <span class="seccion-num">01 · LIGA</span>
          <h2 id="liga-titulo">Formato, divisiones, fechas, equipos y clasificación</h2>
          <p>{{ ajustes.modality or 'El formato, las divisiones, el calendario completo, los '
             'equipos con sus jugadores y la tabla de posiciones, todo en un solo sitio.' }}</p>
        </div>
      </div>

      <div class="pestanas" role="tablist" data-pestanas="liga-tabs" aria-label="Secciones de la liga">
        <button type="button" role="tab" aria-selected="true"  data-panel="panel-formato">Formato</button>
        <button type="button" role="tab" aria-selected="false" data-panel="panel-divisiones">Divisiones</button>
        <button type="button" role="tab" aria-selected="false" data-panel="panel-fechas">Fechas</button>
        <button type="button" role="tab" aria-selected="false" data-panel="panel-equipos">Equipos</button>
        <button type="button" role="tab" aria-selected="false" data-panel="panel-tabla">Clasificación</button>
      </div>

      {# ------------------------------------------------------- FORMATO #}
      <div class="panel-liga activo" id="panel-formato" role="tabpanel">
        <div class="rejilla r4" style="margin-bottom:20px">
          {% for par in ajustes.matchConfig %}
            <div class="tarjeta revelar">
              <h3 class="tenue" style="font-size:.72rem;letter-spacing:.12em;text-transform:uppercase">
                {{ par.label }}</h3>
              <div style="font-size:1.16rem;font-weight:800">{{ par.value }}</div>
            </div>
          {% endfor %}
          <div class="tarjeta revelar">
            <h3 class="tenue" style="font-size:.72rem;letter-spacing:.12em;text-transform:uppercase">Puntos</h3>
            <div style="font-size:1.16rem;font-weight:800">Victoria {{ ajustes.pointsWin }} ·
              Empate {{ ajustes.pointsDraw }}</div>
          </div>
          <div class="tarjeta revelar">
            <h3 class="tenue" style="font-size:.72rem;letter-spacing:.12em;text-transform:uppercase">Mapa</h3>
            <div style="font-size:1.16rem;font-weight:800">{{ ajustes.map or '—' }}</div>
          </div>
          <div class="tarjeta revelar">
            <h3 class="tenue" style="font-size:.72rem;letter-spacing:.12em;text-transform:uppercase">Duración</h3>
            <div style="font-size:1.16rem;font-weight:800">{{ ajustes.matchDuration or '—' }}</div>
          </div>
          <div class="tarjeta revelar">
            <h3 class="tenue" style="font-size:.72rem;letter-spacing:.12em;text-transform:uppercase">Tolerancia</h3>
            <div style="font-size:1.16rem;font-weight:800">{{ ajustes.tolerance or '—' }}</div>
          </div>
        </div>

        {% if reglas %}
          <h3 class="tenue" style="font-size:.78rem;letter-spacing:.15em;text-transform:uppercase">
            Reglamento</h3>
          <div class="rejilla r2" style="margin-top:12px">
            {% for regla in reglas %}
              <article class="tarjeta revelar">
                <h3>{{ regla.title }}</h3>
                {% if regla.summary %}<p class="cuerpo">{{ regla.summary }}</p>{% endif %}
                {% set puntos_regla = regla.get('items') %}
                {% if puntos_regla %}
                  <ul class="lista-puntos">
                    {% for item in puntos_regla %}
                      <li><strong>{{ item.title }}</strong>{% if item.text %} — {{ item.text }}{% endif %}</li>
                    {% endfor %}
                  </ul>
                {% endif %}
                {% for bloque in regla.blocks|default([], true) %}
                  <div class="sub-tarjeta">
                    <h4>{{ bloque.title }}</h4>
                    {% if bloque.subtitle %}<p class="cuerpo">{{ bloque.subtitle }}</p>{% endif %}
                    {% if bloque.text %}<p class="cuerpo">{{ bloque.text }}</p>{% endif %}
                    {% if bloque.list %}
                      <ul class="lista-puntos">
                        {% for punto in bloque.list %}<li>{{ punto }}</li>{% endfor %}
                      </ul>
                    {% endif %}
                  </div>
                {% endfor %}
                {% for tarjeta in regla.cards|default([], true) %}
                  <div class="sub-tarjeta">
                    {% if tarjeta.kicker %}<span class="etiqueta">{{ tarjeta.kicker }}</span>{% endif %}
                    <h4>{{ tarjeta.title }}</h4>
                    {% if tarjeta.text %}<p class="cuerpo">{{ tarjeta.text }}</p>{% endif %}
                    {% if tarjeta.list %}
                      <ul class="lista-puntos">
                        {% for punto in tarjeta.list %}<li>{{ punto }}</li>{% endfor %}
                      </ul>
                    {% endif %}
                  </div>
                {% endfor %}
              </article>
            {% endfor %}
          </div>
        {% endif %}
      </div>

      {# ----------------------------------------------------- DIVISIONES #}
      <div class="panel-liga" id="panel-divisiones" role="tabpanel">
        <div class="rejilla r2">
          {% for d in divisiones %}
            <article class="tarjeta revelar">
              <div class="tarjeta-cab">
                <h3>{{ d.name }}</h3>
                <span class="etiqueta diamante">{{ d.code or d.id|upper }}</span>
              </div>
              {% if d.summary %}<p class="cuerpo">{{ d.summary }}</p>{% endif %}
              <div style="display:flex;gap:7px;flex-wrap:wrap;margin:11px 0">
                <span class="etiqueta">{{ d.teams }} {{ plural(d.teams, 'equipo', 'equipos') }}</span>
                {% if d.journeys %}<span class="etiqueta">{{ d.journeys }} jornadas</span>{% endif %}
                {% if d.season %}<span class="etiqueta">{{ d.season }}</span>{% endif %}
              </div>
              {% if d.phases %}
                <div class="sub-tarjeta">
                  <h4>Fases</h4>
                  {% for fase in d.phases %}
                    <p class="cuerpo" style="margin-bottom:.6em">
                      <strong>{{ fase.label or fase.title }}</strong>
                      {% if fase.title and fase.label %} · {% endif %}
                      {{ fase.text }}{% if fase.note %} <span class="muy-tenue">{{ fase.note }}</span>{% endif %}
                    </p>
                  {% endfor %}
                </div>
              {% endif %}
              {% set movimiento = d.movement %}
          {% if movimiento and movimiento.get('items') %}
                <div class="sub-tarjeta">
                  <h4>{{ d.movement.title or 'Ascensos y descensos' }}</h4>
                  {% for item in movimiento.get('items') %}
                    <p class="cuerpo" style="margin-bottom:.4em">
                      {% if item.place %}<strong>{{ item.place }}</strong> {% endif %}
                      {% if item.label %}<strong>{{ item.label }}</strong>{% endif %}
                      {% if item.text %} — {{ item.text }}{% endif %}
                    </p>
                  {% endfor %}
                </div>
              {% endif %}
              {% if d.rules %}
                <div class="sub-tarjeta">
                  <h4>Reglas de la división</h4>
                  {% for regla in d.rules %}
                    <p class="cuerpo" style="margin-bottom:.5em">
                      <strong>{{ regla.title }}</strong>{% if regla.text %} — {{ regla.text }}{% endif %}
                    </p>
                  {% endfor %}
                </div>
              {% endif %}
              {% if d.playoffs or d.promotion or d.relegation %}
                <div style="display:flex;gap:7px;flex-wrap:wrap;margin-top:11px">
                  {% if d.playoffs %}<span class="etiqueta oro">Playoffs: {{ d.playoffs }}</span>{% endif %}
                  {% if d.promotion %}<span class="etiqueta verde">Ascenso: {{ d.promotion }}</span>{% endif %}
                  {% if d.relegation %}<span class="etiqueta rojo">Descenso: {{ d.relegation }}</span>{% endif %}
                </div>
              {% endif %}
            </article>
          {% else %}
            <p class="vacio">Todavía no hay divisiones configuradas.</p>
          {% endfor %}
        </div>
      </div>

      {# --------------------------------------------------------- FECHAS #}
      <div class="panel-liga" id="panel-fechas" role="tabpanel">
        {% if jornadas %}
          {% for jornada in jornadas %}
            <div style="margin-bottom:30px">
              <h3 class="tenue" style="font-size:.78rem;letter-spacing:.15em;text-transform:uppercase">
                {{ jornada.etiqueta }}
                {% if jornada.division %}<span class="etiqueta diamante">{{ jornada.division }}</span>{% endif %}
              </h3>
              <div class="partidos-lista" style="margin-top:11px">
                {% for p in jornada.partidos %}
                  <article class="partido">
                    <div class="lado">
                      {% if p.logo_home %}<img class="escudo sm" src="{{ p.logo_home }}" alt="" width="34" height="34">{% endif %}
                      <span class="nombre">{{ p.home }}</span>
                    </div>
                    <div style="text-align:center">
                      <span class="marcador {{ 'final' if p.status == 'finalizado' else ('vivo' if p.status == 'en-vivo' else '') }}">
                        {% if p.homeGoals is not none and p.awayGoals is not none %}
                          {{ p.homeGoals }} – {{ p.awayGoals }}
                        {% else %}<span class="tenue">vs</span>{% endif %}
                      </span>
                      <div class="partido-meta" style="justify-content:center;border:0;padding-top:3px">
                        <span class="etiqueta {{ 'verde' if p.status == 'finalizado' else ('rojo' if p.status == 'en-vivo' else '') }}">
                          {{ p.status|estado }}</span>
                        {% if p.date %}<span>{{ p.date|fecha }}</span>{% endif %}
                        {% if p.time %}<span>{{ p.time|hora }}</span>{% endif %}
                      </div>
                    </div>
                    <div class="lado der">
                      <span class="nombre">{{ p.away }}</span>
                      {% if p.logo_away %}<img class="escudo sm" src="{{ p.logo_away }}" alt="" width="34" height="34">{% endif %}
                    </div>
                    {% if p.stage == 'playoffs' %}
                      <div class="partido-meta"><span class="etiqueta violeta">{{ p.stage|fase }}</span></div>
                    {% endif %}
                    {% if p.informe %}
                      <div class="informe">
                        {% if p.informe.events %}
                          <h4>Goles y asistencias</h4>
                          <div class="eventos">
                            {% for ev in p.informe.events %}
                              <div class="evento">
                                <span class="min">{{ '%02d\' |format(ev.minute) if ev.minute is not none else '—' }}</span>
                                <span class="ico-balon">{{ '&#9917;'|safe if ev.kind == 'gol' else '&#128105;' }}</span>
                                <span class="quien">{{ ev.player }}
                                  <span class="muy-tenue">· {{ p.home if ev.side == 'local' else p.away }}</span></span>
                                <span class="tipo">{{ 'Gol' if ev.kind == 'gol' else 'Asistencia' }}</span>
                              </div>
                            {% endfor %}
                          </div>
                        {% endif %}
                        {% if p.informe.cleanSheets or p.informe.mvp %}
                          <h4 style="margin-top:13px">Reconocimientos</h4>
                          <div class="cronica">
                            {% if p.informe.mvp %}
                              <span class="mvp">&#127942; MVP: {{ p.informe.mvp }}</span>
                            {% endif %}
                            {% for cs in p.informe.cleanSheets %}
                              <span class="cs">&#129457; Portería a cero: {{ cs.player }}
                                ({{ cs.team }})</span>
                            {% endfor %}
                          </div>
                        {% endif %}
                        {% if p.notes %}<p class="cuerpo" style="margin-top:11px">{{ p.notes }}</p>{% endif %}
                      </div>
                    {% endif %}
                  </article>
                {% endfor %}
              </div>
            </div>
          {% endfor %}
        {% else %}
          <p class="vacio">Todavía no hay fechas cargadas.</p>
        {% endif %}
      </div>

      {# -------------------------------------------------------- EQUIPOS #}
      <div class="panel-liga" id="panel-equipos" role="tabpanel">
        {% if equipos %}
          <div class="equipos">
            {% for eq in equipos %}
              <article class="tarjeta revelar">
                <div class="equipo" style="margin-bottom:11px">
                  {% if eq.logo %}
                    <img class="escudo" src="{{ eq.logo }}" alt="Logo de {{ eq.name }}"
                         width="52" height="52">
                  {% else %}
                    <span class="escudo-ini">{{ eq.name[:2]|upper }}</span>
                  {% endif %}
                  <span style="min-width:0">
                    <strong>{{ eq.name }}</strong>
                    <span>{{ eq.division_name }}{% if eq.coach %} · DT {{ eq.coach }}{% endif %}</span>
                  </span>
                </div>
                {% if eq.colors %}
                  <div style="display:flex;gap:4px;margin-bottom:11px">
                    {% for color in eq.colors.split(',') %}
                      <span style="width:20px;height:8px;border-radius:3px;background:{{ color.strip() }}"></span>
                    {% endfor %}
                  </div>
                {% endif %}
                <details>
                  <summary style="cursor:pointer;color:var(--diamante);font-weight:700;font-size:.86rem">
                    Plantilla ({{ eq.jugadores|length }})
                    {{ plural(eq.jugadores|length, 'jugador', 'jugadores') }}</summary>
                  {% if eq.jugadores %}
                    <div class="tabla-caja" style="margin-top:11px">
                      <table style="min-width:auto">
                        <thead><tr><th class="num">#</th><th>Jugador</th><th>Puesto</th></tr></thead>
                        <tbody>
                          {% for j in eq.jugadores %}
                            <tr>
                              <td class="num">{{ j.jersey if j.jersey is not none else '—' }}</td>
                              <td>{{ j.name }}</td>
                              <td class="tenue">{{ j.position }}</td>
                            </tr>
                          {% endfor %}
                        </tbody>
                      </table>
                    </div>
                  {% else %}
                    <p class="vacio" style="margin-top:11px;padding:17px">
                      Aún no hay jugadores en esta plantilla.</p>
                  {% endif %}
                </details>
              </article>
            {% endfor %}
          </div>
        {% else %}
          <p class="vacio">Todavía no hay equipos inscritos.</p>
        {% endif %}
      </div>

      {# ----------------------------------------------------- CLASIFICACIÓN #}
      <div class="panel-liga" id="panel-tabla" role="tabpanel">
        {% for d in divisiones %}
          <div style="margin-bottom:26px">
            <h3 style="display:flex;align-items:center;gap:9px">
              {{ d.name }} <span class="etiqueta diamante">{{ d.code or d.id|upper }}</span>
            </h3>
            {% if tablas[d.id] %}
              <div class="tabla-caja">
                <table>
                  <caption>{{ ajustes.leagueName }} · {{ d.name }}</caption>
                  <thead>
                    <tr>
                      <th class="num">#</th><th>Equipo</th>
                      <th class="num">PJ</th><th class="num">G</th><th class="num">E</th>
                      <th class="num">P</th><th class="num">GF</th><th class="num">GC</th>
                      <th class="num">DG</th><th class="num">Pts</th>
                    </tr>
                  </thead>
                  <tbody>
                    {% for fila in tablas[d.id] %}
                      <tr>
                        <td class="num"><span class="pos {{ 'p1' if fila.position == 1 else ('p2' if fila.position == 2 else ('p3' if fila.position == 3 else '')) }}">{{ fila.position }}</span></td>
                        <td>{{ fila.name }}</td>
                        <td class="num">{{ fila.played }}</td>
                        <td class="num">{{ fila.won }}</td>
                        <td class="num">{{ fila.drawn }}</td>
                        <td class="num">{{ fila.lost }}</td>
                        <td class="num">{{ fila.goalsFor }}</td>
                        <td class="num">{{ fila.goalsAgainst }}</td>
                        <td class="num">{{ fila.goalDiff }}</td>
                        <td class="num"><strong>{{ fila.points }}</strong></td>
                      </tr>
                    {% endfor %}
                  </tbody>
                </table>
              </div>
            {% else %}
              <p class="vacio">Aún no hay partidos finalizados en esta división.</p>
            {% endif %}
          </div>
        {% else %}
          <p class="vacio">Todavía no hay divisiones configuradas.</p>
        {% endfor %}

        {% if estadisticas %}
          <h3 style="margin-top:26px">Estadísticas de la temporada</h3>
          <div class="tabla-caja">
            <table>
              <caption>Goles, asistencias, porterías a cero y MVP</caption>
              <thead>
                <tr>
                  <th class="num">#</th><th>Jugador</th><th>Equipo</th>
                  <th class="num">Goles</th><th class="num">Asist.</th>
                  <th class="num">CS</th><th class="num">MVP</th>
                </tr>
              </thead>
              <tbody>
                {% for s in estadisticas %}
                  <tr>
                    <td class="num">{{ loop.index }}</td>
                    <td><strong>{{ s.player }}</strong></td>
                    <td class="tenue">{{ s.team or '—' }}</td>
                    <td class="num">{{ s.goals or '' }}</td>
                    <td class="num">{{ s.assists or '' }}</td>
                    <td class="num">{{ s.cleanSheets or '' }}</td>
                    <td class="num">{{ s.mvp or '' }}</td>
                  </tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
        {% endif %}
      </div>
    </div>
  </section>

  {# -------------------------------------------------------------- PUBS #}
  <section class="seccion alt" id="pubs" aria-labelledby="pubs-titulo">
    <div class="envoltura">
      <div class="seccion-cab">
        <div class="txt">
          <span class="seccion-num">02 · PUBS</span>
          <h2 id="pubs-titulo">Salas de HaxBall de la liga</h2>
          <p>Entra a las salas públicas. Las que están cerradas se marcan en rojo.</p>
        </div>
      </div>
      <div class="rejilla r2">
        {% for sala in salas %}
          <article class="sala">
            <span class="punto {{ 'verde' if sala.status == 'ABIERTA' else ('roja' if sala.status == 'MANTENIMIENTO' else 'gris') }}"></span>
            <div class="info">
              <strong>{{ sala.label or sala.name }}</strong>
              <span>{{ sala.name }}{% if sala.note %} · {{ sala.note }}{% endif %}</span>
            </div>
            {% if sala.players %}
              <span class="etiqueta">{{ sala.players }} jugadores</span>
            {% endif %}
            <span class="etiqueta {{ 'verde' if sala.status == 'ABIERTA' else ('rojo' if sala.status != 'CERRADA' else '') }}">
              {{ sala.status }}</span>
            {% if sala.url %}
              <a class="btn pequeno primario" href="{{ sala.url }}" target="_blank" rel="noopener">Entrar</a>
            {% endif %}
          </article>
        {% else %}
          <p class="vacio">Todavía no hay salas publicadas.</p>
        {% endfor %}
      </div>
    </div>
  </section>

  {# ------------------------------------------------------------- MUSEO #}
  <section class="seccion" id="museo" aria-labelledby="museo-titulo">
    <div class="envoltura">
      <div class="seccion-cab">
        <div class="txt">
          <span class="seccion-num">03 · MUSEO</span>
          <h2 id="museo-titulo">Museo de premios</h2>
          <p>Todos los premios entregados, de los más antiguos a los más recientes:
            banqueros de oro, bota de oro, Guante de Oro, mejores equipos y campeones.</p>
        </div>
      </div>
      {% for grupo in premios_agrupados %}
        <div style="margin-bottom:30px">
          <h3 style="display:flex;align-items:center;gap:9px">
            {{ grupo.titulo }}
            {% set grupo_premios = grupo.get('items') %}
            <span class="etiqueta oro">{{ grupo_premios|length }}</span>
          </h3>
          <div class="rejilla r3" style="margin-top:13px">
            {% for p in grupo_premios %}
              <article class="tarjeta revelar">
                {% if p.image %}
                  <img class="tarjeta-img" src="{{ p.image }}" alt="{{ p.title }}" loading="lazy">
                {% endif %}
                <div class="tarjeta-cab">
                  <h3 style="font-size:1rem">{{ p.title }}</h3>
                  {% if p.year %}<span class="etiqueta">{{ p.year }}</span>{% endif %}
                </div>
                {% if p.team %}<div style="font-weight:700;margin-bottom:5px">{{ p.team }}</div>{% endif %}
                {% if p.text %}<p class="cuerpo">{{ p.text }}</p>{% endif %}
                <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:9px">
                  {% if p.division %}<span class="etiqueta diamante">{{ p.division }}</span>{% endif %}
                  {% if p.season %}<span class="etiqueta">{{ p.season }}</span>{% endif %}
                </div>
              </article>
            {% endfor %}
          </div>
        </div>
      {% else %}
        <p class="vacio">Todavía no hay premios en el museo.</p>
      {% endfor %}
    </div>
  </section>

  {# ---------------------------------------------------------- NOTICIAS #}
  <section class="seccion alt" id="noticias" aria-labelledby="noticias-titulo">
    <div class="envoltura">
      <div class="seccion-cab">
        <div class="txt">
          <span class="seccion-num">04 · NOTICIAS</span>
          <h2 id="noticias-titulo">Reportarios y noticias</h2>
          <p>Lo último que ha pasado en la liga, contado por el equipo de comunicación.</p>
        </div>
      </div>
      {% if noticias %}
        <div class="rejilla r2">
          {% for n in noticias %}
            <article class="tarjeta revelar">
              {% if n.image %}
                <img class="tarjeta-img" src="{{ n.image }}" alt="{{ n.title }}" loading="lazy">
              {% endif %}
              <div class="tarjeta-cab">
                <h3>{{ n.title }}</h3>
                {% if n.pinned %}<span class="etiqueta oro">Portada</span>{% endif %}
              </div>
              <div style="display:flex;gap:7px;flex-wrap:wrap;margin-bottom:9px">
                {% if n.category %}<span class="etiqueta diamante">{{ n.category }}</span>{% endif %}
                {% if n.date %}<span class="etiqueta">{{ n.date|fecha }}</span>{% endif %}
                {% if n.author %}<span class="etiqueta">{{ n.author }}</span>{% endif %}
              </div>
              {% if n.excerpt %}<p class="cuerpo">{{ n.excerpt }}</p>{% endif %}
              {% if n.body %}
                <details style="margin-top:9px">
                  <summary style="cursor:pointer;color:var(--diamante);font-weight:700;font-size:.86rem">
                    Leer el reportaje completo</summary>
                  <div style="margin-top:11px;white-space:pre-line" class="cuerpo">{{ n.body }}</div>
                </details>
              {% endif %}
            </article>
          {% endfor %}
        </div>
      {% else %}
        <p class="vacio">Todavía no hay noticias publicadas.</p>
      {% endif %}
    </div>
  </section>

  {# ---------------------------------------------------------- ANUNCIOS #}
  <section class="seccion" id="anuncios" aria-labelledby="anuncios-titulo">
    <div class="envoltura">
      <div class="seccion-cab">
        <div class="txt">
          <span class="seccion-num">05 · ANUNCIOS - NOVEDADES</span>
          <h2 id="anuncios-titulo">Novedades de la liga</h2>
          <p>Comunicados oficiales, fechas importantes y todo lo que cambia de una temporada a otra.</p>
        </div>
      </div>
      {% if anuncios %}
        <div class="rejilla r2">
          {% for a in anuncios %}
            <article class="tarjeta revelar">
              <div class="tarjeta-cab">
                <h3>{{ a.title }}</h3>
                <span class="etiqueta {{ 'oro' if a.kind == 'awards' else ('diamante' if a.kind == 'registration' else '') }}">
                  {{ {'awards':'Premios','registration':'Inscripción','general':'General'}.get(a.kind, 'General') }}</span>
              </div>
              {% if a.kicker %}<p style="font-weight:700;color:var(--oro);margin-bottom:7px">{{ a.kicker }}</p>{% endif %}
              <div style="display:flex;gap:7px;flex-wrap:wrap;margin-bottom:10px">
                {% if a.date %}<span class="etiqueta">{{ a.date|fecha }}</span>{% endif %}
                {% if a.season %}<span class="etiqueta">{{ a.season }}</span>{% endif %}
              </div>
              {% if a.text %}<p class="cuerpo">{{ a.text }}</p>{% endif %}
              {% if a.bullets %}
                <ul class="lista-puntos">
                  {% for punto in a.bullets %}<li>{{ punto }}</li>{% endfor %}
                </ul>
              {% endif %}
              {% if a.closing %}<p style="margin-top:11px;font-style:italic" class="tenue">{{ a.closing }}</p>{% endif %}
              {% if a.warning %}
                <div class="aviso error" style="margin:11px 0 0">&#9888; {{ a.warning }}</div>
              {% endif %}
            </article>
          {% endfor %}
        </div>
      {% else %}
        <p class="vacio">Todavía no hay anuncios.</p>
      {% endif %}
    </div>
  </section>

  {# ---------------------------------------------------------- ALIANZAS #}
  <section class="seccion alt" id="alianzas" aria-labelledby="alianzas-titulo">
    <div class="envoltura">
      <div class="seccion-cab">
        <div class="txt">
          <span class="seccion-num">06 · ALIANZAS</span>
          <h2 id="alianzas-titulo">Afiliaciones y aliados</h2>
          <p>Las alianzas activas y la próxima afiliación que está por confirmarse.</p>
        </div>
      </div>
      {% if alianzas %}
        {% if alianzas_proximas %}
          <h3 style="display:flex;align-items:center;gap:9px">Próxima afiliación
            <span class="etiqueta violeta">En camino</span></h3>
          <div class="rejilla r3" style="margin:13px 0 26px">
            {% for al in alianzas_proximas %}
              <article class="tarjeta revelar" style="border-color:rgba(168,107,255,.45)">
                <div class="tarjeta-cab">
                  <h3>{{ al.name }}</h3>
                  <span class="etiqueta violeta">{{ al.status }}</span>
                </div>
                {% if al.description %}<p class="cuerpo">{{ al.description }}</p>{% endif %}
                {% if al.href %}
                  <a class="btn pequeno" href="{{ al.href }}" target="_blank" rel="noopener">
                    {{ al.cta or 'Ver más' }}</a>
                {% endif %}
              </article>
            {% endfor %}
          </div>
        {% endif %}
        <div class="rejilla r3">
          {% for al in alianzas %}
            <article class="tarjeta revelar">
              {% if al.image %}
                <img class="tarjeta-img" src="{{ al.image }}" alt="{{ al.name }}" loading="lazy">
              {% endif %}
              <div class="tarjeta-cab">
                <h3>{{ al.name }}</h3>
                <span class="etiqueta verde">{{ al.status }}</span>
              </div>
              <span class="etiqueta" style="margin-bottom:9px">
                {{ {'afiliacion':'Afiliación','partner':'Partner','proxima':'Próxima',
                    'servidor':'Servidor'}.get(al.kind, al.kind) }}</span>
              {% if al.description %}<p class="cuerpo">{{ al.description }}</p>{% endif %}
              {% if al.href %}
                <a class="btn pequeno fantasma" href="{{ al.href }}" target="_blank" rel="noopener">
                  {{ al.cta or 'Visitar' }}</a>
              {% endif %}
            </article>
          {% endfor %}
        </div>
      {% else %}
        <p class="vacio">Todavía no hay alianzas publicadas.</p>
      {% endif %}
    </div>
  </section>

  {# ------------------------------------------------------------- REDES #}
  <section class="seccion" id="redes" aria-labelledby="redes-titulo">
    <div class="envoltura">
      <div class="seccion-cab">
        <div class="txt">
          <span class="seccion-num">07 · REDES SOCIALES</span>
          <h2 id="redes-titulo">La liga y nuestros streamers</h2>
          <p>Síguenos en todas las plataformas. Los streamers de la liga tienen su propia marca.</p>
        </div>
      </div>

      {% if streamers %}
        <h3 style="display:flex;align-items:center;gap:9px">Streamers
          <span class="etiqueta violeta">Directos</span></h3>
        <div class="rejilla r3" style="margin:13px 0 26px">
          {% for r in streamers %}
            <a class="tarjeta revelar" href="{{ r.url }}" target="_blank" rel="noopener"
               style="text-decoration:none;color:inherit">
              <div class="tarjeta-cab">
                <h3 style="font-size:1rem">{{ r.owner_name or r.handle }}</h3>
                <span class="etiqueta violeta">{{ r.network|red }}</span>
              </div>
              <p class="cuerpo" style="margin:0">{{ r.handle }}</p>
              {% if r.followers %}
                <div style="margin-top:9px"><span class="etiqueta">{{ r.followers|numero }} seguidores</span></div>
              {% endif %}
            </a>
          {% endfor %}
        </div>
      {% endif %}

      <h3>Cuentas oficiales</h3>
      <div class="rejilla r3" style="margin-top:13px">
        {% for r in redes %}
          <a class="tarjeta revelar" href="{{ r.url }}" target="_blank" rel="noopener"
             style="text-decoration:none;color:inherit">
            <div class="tarjeta-cab">
              <h3 style="font-size:1rem">{{ r.network|red }}</h3>
              {% if r.followers %}
                <span class="etiqueta">{{ r.followers|numero }}</span>
              {% endif %}
            </div>
            <p class="cuerpo" style="margin:0">
              {{ r.owner_name or 'La liga' }}{% if r.handle %} · {{ r.handle }}{% endif %}</p>
          </a>
        {% else %}
          <p class="vacio">Todavía no hay redes sociales publicadas.</p>
        {% endfor %}
      </div>
    </div>
  </section>

  {# ------------------------------------------------------------ EQUIPO #}
  <section class="seccion alt" id="equipo" aria-labelledby="equipo-titulo">
    <div class="envoltura">
      <div class="seccion-cab">
        <div class="txt">
          <span class="seccion-num">08 · EQUIPO ADMINISTRACION</span>
          <h2 id="equipo-titulo">Quiénes mantienen la liga</h2>
          <p>El owner, el desarrollador, los masters y el resto del staff de administración.</p>
        </div>
      </div>
      {% if personal %}
        <div class="rejilla r3">
          {% for p in personal %}
            <article class="tarjeta revelar">
              {% if p.banner %}
                <img class="tarjeta-img" src="{{ p.banner }}" alt="Banner de {{ p.name }}"
                     loading="lazy" style="aspect-ratio:3/1">
              {% endif %}
              <div class="equipo" style="margin-bottom:11px">
                {% if p.avatar %}
                  <img class="escudo lg" src="{{ p.avatar }}" alt="Foto de {{ p.name }}"
                       width="74" height="74">
                {% else %}
                  <span class="escudo-ini lg">{{ p.name[:2]|upper }}</span>
                {% endif %}
                <span style="min-width:0">
                  <strong style="font-size:1.08rem">{{ p.name }}</strong>
                  <span>{{ p.role }}{% if p.username %} · {{ p.username }}{% endif %}</span>
                </span>
              </div>
              {% if p.focus %}<div style="margin-bottom:7px"><span class="etiqueta oro">{{ p.focus }}</span></div>{% endif %}
              {% if p.bio %}<p class="cuerpo">{{ p.bio }}</p>{% endif %}
              {% if p.tags %}
                <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px">
                  {% for t in p.tags %}<span class="etiqueta">{{ t }}</span>{% endfor %}
                </div>
              {% endif %}
              <div style="display:flex;gap:7px;flex-wrap:wrap">
                {% if p.github %}<a class="btn pequeno fantasma" href="{{ p.github }}"
                   target="_blank" rel="noopener">GitHub</a>{% endif %}
                {% if p.instagram %}<a class="btn pequeno fantasma" href="{{ p.instagram }}"
                   target="_blank" rel="noopener">Instagram</a>{% endif %}
                {% if p.discord %}<a class="btn pequeno fantasma" href="{{ p.discord }}"
                   target="_blank" rel="noopener">Discord</a>{% endif %}
                {% if p.available %}<span class="etiqueta verde">Disponible</span>{% endif %}
              </div>
            </article>
          {% endfor %}
        </div>
      {% else %}
        <p class="vacio">Todavía no hay miembros del equipo cargados.</p>
      {% endif %}
    </div>
  </section>

  {# -------------------------------------------------------- LIVE FUTBOL #}
  <section class="seccion" id="live" aria-labelledby="live-titulo">
    <div class="envoltura">
      <div class="seccion-cab">
        <div class="txt">
          <span class="seccion-num">09 · LIVE FUTBOL</span>
          <h2 id="live-titulo">Fútbol en vivo</h2>
          <p>Los partidos del fútbol real se retransmiten aquí, tipo Kick o Twitch, con el
            marcador y el número de espectadores.</p>
        </div>
      </div>
      {% if directos %}
        <div class="rejilla r2">
          {% for d in directos %}
            <article class="tarjeta">
              <div class="tarjeta-cab">
                <h3 style="font-size:1rem">{{ d.league or 'Partido' }}</h3>
                {% if d.is_live %}
                  <span class="etiqueta rojo"><span class="punto roja"
                    style="display:inline-block;margin-right:5px"></span>EN VIVO</span>
                {% else %}
                  <span class="etiqueta">Programado</span>
                {% endif %}
              </div>
              {% if d.url and d.is_live and d.channel %}
                <div class="embed">
                  {% if d.platform == 'twitch' %}
                    <iframe src="https://player.twitch.tv/?channel={{ d.channel }}&parent={{ anfitrion }}&muted=true"
                           allowfullscreen loading="lazy" title="Directo de {{ d.league }}"></iframe>
                  {% elif d.platform == 'kick' %}
                    <iframe src="https://player.kick.com/{{ d.channel }}"
                            allowfullscreen loading="lazy" title="Directo de {{ d.league }}"></iframe>
                  {% elif d.platform == 'youtube' %}
                    <iframe src="https://www.youtube.com/embed/live_stream?channel={{ d.channel }}"
                            allowfullscreen loading="lazy" title="Directo de {{ d.league }}"></iframe>
                  {% else %}
                    <div class="cargando">Directo en {{ d.platform|red }}</div>
                  {% endif %}
                  <div class="cargando">Cargando el directo…</div>
                  <div class="meta">
                    <span class="etiqueta rojo">{{ d.platform|red }}</span>
                    {% if d.viewer_count %}
                      <span class="etiqueta">{{ d.viewer_count|numero }} espectadores</span>
                    {% endif %}
                  </div>
                </div>
              {% endif %}
              <div style="display:flex;align-items:center;gap:11px;margin-bottom:11px">
                <span style="flex:1;font-weight:700;text-align:right">{{ d.home or 'Local' }}</span>
                <span class="marcador {{ 'vivo' if d.is_live else 'final' }}">
                  {{ d.home_score or '0' }} – {{ d.away_score or '0' }}</span>
                <span style="flex:1;font-weight:700">{{ d.away or 'Visitante' }}</span>
              </div>
              {% if d.starts_at %}
                <div style="margin-bottom:9px"><span class="etiqueta">{{ d.starts_at|fecha_hora }}</span></div>
              {% endif %}
              {% if d.url %}
                <a class="btn pequeno primario" href="{{ d.url }}" target="_blank" rel="noopener">
                  Abrir en {{ d.platform|red }}</a>
              {% endif %}
            </article>
          {% endfor %}
        </div>
      {% else %}
        <p class="vacio">No hay directos programados ahora mismo.</p>
      {% endif %}
    </div>
  </section>

  {# ---------------------------------------------------------- DONACION #}
  <section class="seccion alt" id="donacion" aria-labelledby="donacion-titulo">
    <div class="envoltura">
      <div class="seccion-cab">
        <div class="txt">
          <span class="seccion-num">10 · DONACION</span>
          <h2 id="donacion-titulo">Donaciones y datos de la liga</h2>
          <p>Tu aportación mantiene los servidores y los premios. Y los números de la liga,
            de las divisiones y de los jugadores, todos aquí.</p>
        </div>
      </div>

      <div class="rejilla r2">
        <div>
          <h3>Métodos de donación</h3>
          <div class="rejilla r2" style="margin-top:12px">
            {% for d in donaciones %}
              <article class="tarjeta">
                <div class="tarjeta-cab">
                  <h3 style="font-size:1rem">{{ d.title }}</h3>
                  <span class="etiqueta {{ 'verde' if d.kind == 'metodo' else ('oro' if d.kind == 'meta' else '') }}">
                    {{ {'metodo':'Método','meta':'Meta','info':'Info'}.get(d.kind, d.kind) }}</span>
                </div>
                {% if d.description %}<p class="cuerpo">{{ d.description }}</p>{% endif %}
                {% if d.method %}<div class="fila-datos">
                  <span class="crece"><strong>{{ d.method }}</strong>
                    <br><span class="muy-tenue">{{ d.account }}</span></span>
                </div>{% endif %}
                {% if d.goal %}
                  <div class="meta-donacion">
                    <i style="width:{{ (100 * (d.raised|float / d.goal))|round(1) if d.goal else 0 }}%"></i>
                  </div>
                  <div style="display:flex;justify-content:space-between;font-size:.84rem" class="tenue">
                    <span>{{ d.raised|numero(2) }}</span>
                    <span>{{ d.goal|numero(2) }}</span>
                  </div>
                {% endif %}
                {% if d.amount %}
                  <div style="margin-top:9px"><span class="etiqueta oro">{{ d.amount|numero(2) }}</span></div>
                {% endif %}
              </article>
            {% else %}
              <p class="vacio">Todavía no hay métodos de donación cargados.</p>
            {% endfor %}
          </div>
          {% if ajustes.donationNote or ajustes.donationKey %}
            <div class="aviso aviso-info" style="margin-top:15px">
              {% if ajustes.donationNote %}{{ ajustes.donationNote }}<br>{% endif %}
              {% if ajustes.donationKey %}<strong>Clave:</strong> {{ ajustes.donationKey }}{% endif %}
            </div>
          {% endif %}
        </div>

        <div>
          <h3>Resumen de la liga</h3>
          <div class="estadisticas" style="margin-top:12px">
            <div class="estadistica"><b>{{ totales.divisiones }}</b><span>Divisiones</span></div>
            <div class="estadistica"><b>{{ totales.equipos }}</b><span>Equipos</span></div>
            <div class="estadistica"><b>{{ totales.jugadores }}</b><span>Jugadores</span></div>
            <div class="estadistica"><b>{{ totales.partidos }}</b><span>Partidos</span></div>
            <div class="estadistica"><b>{{ totales.goles }}</b><span>Goles</span></div>
            <div class="estadistica"><b>{{ totales.asistencias }}</b><span>Asistencias</span></div>
            <div class="estadistica"><b>{{ totales.porterias }}</b><span>Porterías a cero</span></div>
            <div class="estadistica"><b>{{ totales.mvp }}</b><span>Premios MVP</span></div>
          </div>

          <div class="sub-tarjeta">
            <h4>Divisiones</h4>
            {% for d in divisiones %}
              <div class="fila-datos">
                <span class="crece">
                  <strong>{{ d.name }}</strong>
                  <br><span class="muy-tenue">{{ d.teams }} equipos
                    {%- if d.journeys %} · {{ d.journeys }} jornadas{% endif %}</span>
                </span>
                {% if tablas[d.id] %}
                  <span class="etiqueta oro">{{ tablas[d.id][0].name }} líder</span>
                {% endif %}
              </div>
            {% else %}
              <p class="vacio">Sin divisiones todavía.</p>
            {% endfor %}
          </div>
        </div>
      </div>
    </div>
  </section>
</main>
{% endblock %}
"""
# ==============================================================================
#  PANEL DE ADMINISTRACIÓN
# ==============================================================================

VISTAS_PANEL = [
    ("resumen", "Resumen"),
    ("ajustes", "Ajustes"),
    ("divisiones", "Divisiones"),
    ("equipos", "Equipos y jugadores"),
    ("partidos", "Partidos e informes"),
    ("reglamento", "Reglamento"),
    ("salas", "Salas públicas"),
    ("noticias", "Noticias"),
    ("anuncios", "Anuncios"),
    ("premios", "Museo de premios"),
    ("accesos", "Accesos"),
    ("personal", "Equipo"),
    ("alianzas", "Alianzas"),
    ("redes", "Redes sociales"),
    ("directos", "Live fútbol"),
    ("donaciones", "Donaciones"),
    ("usuarios", "Usuarios"),
]

TPL_PANEL = """
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>Panel · {{ ajustes.leagueName }}</title>
<link rel="icon" href="{{ url_for('assets_archivo', nombre='favicon.png') }}">
<style>{{ css }}</style>
</head>
<body>
<div class="panel-envoltura">
  <aside class="panel-lateral">
    <a class="marca" href="{{ url_for('portada') }}" style="margin-bottom:15px">
      <span class="marca-escudo">{{ ajustes.shortName }}</span>
      <span class="marca-txt">
        <strong>{{ ajustes.leagueName }}</strong><span>Panel</span>
      </span>
    </a>
    {% for grupo, items in grupos_vistas %}
      <h2>{{ grupo }}</h2>
      <div class="panel-menu">
        {% for clave, texto in items %}
          <button type="button" data-vista="{{ clave }}"
                  {{ 'aria-current="true"' if vista == clave }}>{{ texto }}</button>
        {% endfor %}
      </div>
    {% endfor %}
    <form method="post" action="{{ url_for('salir') }}" style="margin-top:22px">
      {{ csrf_campo() }}
      <button class="btn pequeno fantasma" type="submit" style="width:100%">Salir de la liga</button>
    </form>
  </aside>

  <main class="panel-contenido">
    <div class="panel-cab">
      <h1>{{ titulo_panel }}</h1>
      <span class="sesion-chip"><span class="punto"></span>{{ usuario.username }}
        <span class="etiqueta violeta">ADMIN</span></span>
    </div>
    <div id="cuerpo-panel"><p class="tenue">Cargando…</p></div>
  </main>
</div>

<script id="datos-panel" type="application/json">{{ datos_iniciales }}</script>
<script id="config-panel" type="application/json">{{ config_panel }}</script>
<script>{{ js_panel }}</script>
</body>
</html>
"""


# ==============================================================================
#  JAVASCRIPT DEL PANEL
# ==============================================================================

JS_PANEL = r"""
(function(){
  "use strict";
  var d = document;
  var datos = JSON.parse(d.getElementById("datos-panel").textContent);
  var cfg   = JSON.parse(d.getElementById("config-panel").textContent);
  var cuerpo = d.getElementById("cuerpo-panel");
  var guardado = null;

  function esc(v){
    return String(v === null || v === undefined ? "" : v)
      .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
      .replace(/"/g,"&quot;").replace(/'/g,"&#39;");
  }
  function etiqueta(v){ return String(v === null || v === undefined ? "" : v); }
  function opcion(valor, actual, texto){
    return '<option value="' + esc(valor) + '"' + (valor === actual ? " selected" : "") + ">"
      + esc(texto === undefined ? valor : texto) + "</option>";
  }
  function num(v){ return (v === null || v === undefined || v === "") ? "" : Number(v); }

  function vacio(msg){ return '<p class="vacio">' + esc(msg) + "</p>"; }

  function opcionesDivision(campo, valor){
    return (datos.divisions || []).map(function(x){
      return opcion(x.id, valor, x.name);
    }).join("");
  }

  /* ---------- editor de registros ---------- */
  function camposCRUD(c, registro){
    registro = registro || {};
    return (datos.campos[c] || []).map(function(f){
      var bruto = registro[f.clave];
      var v = bruto === undefined || bruto === null ? f.valor : bruto;
      if (f.tipo === "lista") return "";
      if (f.tipo === "file") {
        return '<div class="campo"><label for="c_' + f.clave + '">' + esc(f.etiqueta) + "</label>"
          + (v ? '<span class="muy-tenue" style="display:block;margin-bottom:6px">' + esc(String(v))
              + ' &mdash; <a href="' + esc(String(v)) + '" target="_blank" rel="noopener">ver</a></span>' : "")
          + '<input id="c_' + f.clave + '" name="' + esc(f.clave) + '" type="file"></div>';
      }
      if (f.tipo === "sel") {
        var lista = f.opciones === "division"
          ? opcionesDivision(f.clave, v)
          : (f.opciones || []).map(function(o){
              return '<option value="' + esc(o) + '"' + (o === v ? " selected" : "") + ">"
                + esc(o) + "</option>";
            }).join("");
        return '<div class="campo"><label for="c_' + f.clave + '">' + esc(f.etiqueta) + "</label>"
          + '<select id="c_' + f.clave + '" name="' + esc(f.clave) + '">' + lista + "</select></div>";
      }
      if (f.tipo === "bool") {
        return '<div class="campo"><label class="casilla"><input type="checkbox" name="'
          + esc(f.clave) + '" value="1"' + (v ? " checked" : "") + "> <span>"
          + esc(f.etiqueta) + "</span></label></div>";
      }
      if (f.tipo === "textarea") {
        return '<div class="campo"><label for="c_' + f.clave + '">' + esc(f.etiqueta) + "</label>"
          + '<textarea id="c_' + f.clave + '" name="' + esc(f.clave) + '" rows="4">'
          + esc(etiqueta(v)) + "</textarea></div>";
      }
      var tipo = f.tipo === "bool" ? "checkbox" : f.tipo;
      return '<div class="campo"><label for="c_' + f.clave + '">' + esc(f.etiqueta) + "</label>"
        + '<input id="c_' + f.clave + '" name="' + esc(f.clave) + '" type="' + tipo + '" value="'
        + esc(etiqueta(v)) + '"></div>';
    }).join("");
  }

  function formCRUD(coleccion, registro){
    var c = cfg.colecciones[coleccion];
    var esNuevo = !registro;
    return '<form class="tarjeta" data-guardar="' + esc(coleccion) + '"'
      + (esNuevo ? "" : ' data-id="' + esc(registro.id) + '"') + ">"
      + '<h3 style="margin-bottom:15px">' + (esNuevo ? "Nuevo registro" : "Editando") + "</h3>"
      + camposCRUD(coleccion, registro)
      + '<div style="display:flex;gap:9px;flex-wrap:wrap">'
      + '<button class="btn primario" type="submit">Guardar</button>'
      + '<button class="btn fantasma" type="button" data-cancelar>Volver</button>'
      + "</div></form>";
  }

  function filaCRUD(coleccion, item){
    var c = cfg.colecciones[coleccion];
    var principal = c.principal;
    var etiquetas = (c.etiquetas || []).map(function(k){
      if (!item[k]) return "";
      return '<span class="etiqueta">' + esc(item[k]) + "</span>";
    }).join(" ");
    return '<div class="fila-datos">'
      + (item.logo || item.image || item.avatar || item.banner
          ? '<img class="escudo sm" src="' + esc(item.logo || item.image || item.avatar || item.banner)
            + '" alt="" width="34" height="34">'
          : '<span class="escudo sm" style="display:grid;place-items:center;font-weight:900;font-size:.7rem">'
            + esc(etiqueta(item[principal]).slice(0,2).toUpperCase()) + "</span>")
      + '<span class="crece"><strong>' + esc(etiqueta(item[principal])) + "</strong><br>"
      + '<span class="muy-tenue">' + etiquetas + "</span></span>"
      + '<span class="acciones">'
      + '<button class="btn pequeno" data-editar="' + esc(coleccion) + '" data-id="' + esc(item.id) + '">Editar</button>'
      + (cfg.especial[coleccion]
          ? '<button class="btn pequeno fantasma" data-detalle="' + esc(coleccion) + '" data-id="'
            + esc(item.id) + '">' + esc(cfg.especial[coleccion].boton) + "</button>"
          : "")
      + '<button class="btn pequeno peligro" data-borrar="' + esc(coleccion) + '" data-id="'
        + esc(item.id) + '">Borrar</button>'
      + "</span></div>";
  }

  /* ---------- Jugadores de un equipo ---------- */
  function editorJugadores(equipo){
    var jugadores = (datos.jugadores || []).filter(function(j){ return j.team_id === equipo.id; });
    var filas = jugadores.map(function(j){
      return '<div class="jug-fila">'
        + '<input type="number" name="jersey" min="0" max="99" placeholder="Dorsal" value="'
        + (j.jersey === null ? "" : esc(j.jersey)) + '">'
        + '<input type="text" name="name" placeholder="Nombre del jugador" value="' + esc(j.name) + '">'
        + '<select name="position">' + (cfg.posiciones || []).map(function(p){
            return opcion(p, j.position, p); }).join("") + "</select>"
        + '<input type="text" name="note" placeholder="Nota (opcional)" value="' + esc(j.note) + '">'
        + '<button class="btn pequeno peligro" type="button" data-quitar-jugador>&times;</button>'
        + "</div>";
    }).join("");

    return '<div class="sub-tarjeta"><h4>Plantilla de ' + esc(equipo.name)
      + " (" + jugadores.length + " jugadores)</h4>"
      + '<form data-jugadores="' + esc(equipo.id) + '">'
      + '<div data-filas-jugadores>' + filas + "</div>"
      + '<div style="display:flex;gap:9px;margin-top:11px;flex-wrap:wrap">'
      + '<button class="btn pequeno fantasma" type="button" data-anadir-jugador>+ Añadir jugador</button>'
      + '<button class="btn primario pequeno" type="submit">Guardar plantilla</button>'
      + "</div></form></div>";
  }

  function plantillaVacia(){
    return '<div class="jug-fila">'
      + '<input type="number" name="jersey" min="0" max="99" placeholder="Dorsal">'
      + '<input type="text" name="name" placeholder="Nombre del jugador">'
      + '<select name="position">' + (cfg.posiciones || []).map(function(p){
          return opcion(p, "", p); }).join("") + "</select>"
      + '<input type="text" name="note" placeholder="Nota (opcional)">'
      + '<button class="btn pequeno peligro" type="button" data-quitar-jugador>&times;</button>'
      + "</div>";
  }

  /* ---------- Goles y asistencias de un partido ---------- */
  function editorEventos(partido){
    var eventos = (datos.eventos || []).filter(function(e){ return e.match_id === partido.id; });
    var filas = eventos.map(function(e){
      return '<div class="ev-fila">'
        + '<input type="text" name="player" placeholder="Jugador" value="' + esc(e.player) + '">'
        + '<select name="side">' + opcion("local", e.side, "Local")
          + opcion("visitante", e.side, "Visitante") + "</select>"
        + '<input type="number" name="minute" min="0" max="200" placeholder="Min" value="'
        + (e.minute === null ? "" : esc(e.minute)) + '">'
        + '<select name="kind">' + opcion("gol", e.kind, "Gol")
          + opcion("asistencia", e.kind, "Asistencia") + "</select>"
        + '<button class="btn pequeno peligro" type="button" data-quitar-evento>&times;</button>'
        + "</div>";
    }).join("");

    return '<div class="sub-tarjeta"><h4>Goles y asistencias</h4>'
      + '<form data-eventos="' + esc(partido.id) + '">'
      + '<div data-filas-eventos>' + filas + "</div>"
      + '<div style="display:flex;gap:9px;margin-top:11px;flex-wrap:wrap">'
      + '<button class="btn pequeno fantasma" type="button" data-anadir-evento>+ Añadir</button>'
      + '<button class="btn primario pequeno" type="submit">Guardar informe</button>'
      + "</div></form></div>";
  }

  function eventoVacio(){
    return '<div class="ev-fila">'
      + '<input type="text" name="player" placeholder="Jugador">'
      + '<select name="side">' + opcion("local", "", "Local")
        + opcion("visitante", "", "Visitante") + "</select>"
      + '<input type="number" name="minute" min="0" max="200" placeholder="Min">'
      + '<select name="kind">' + opcion("gol", "", "Gol")
        + opcion("asistencia", "", "Asistencia") + "</select>"
      + '<button class="btn pequeno peligro" type="button" data-quitar-evento>&times;</button>'
      + "</div>";
  }

  /* ---------- Vistas ---------- */
  var VISTAS = {};

  VISTAS.resumen = function(){
    var t = datos.totales || {};
    var bloques = [
      ["equipos", "Equipos"], ["jugadores", "Jugadores"], ["partidos", "Partidos"],
      ["goles", "Goles"], ["asistencias", "Asistencias"], ["porterias", "Porterías a cero"],
      ["mvp", "Premios MVP"], ["premios", "Premios del museo"], ["noticias", "Noticias"],
      ["usuarios", "Cuentas de usuario"],
    ];
    return '<div class="estadisticas">'
      + bloques.map(function(b){
          return '<div class="estadistica"><b>' + esc(t[b[0]] || 0) + "</b><span>"
            + esc(b[1]) + "</span></div>";
        }).join("")
      + "</div>"
      + '<div class="sub-tarjeta"><h4>Accesos rápidos</h4>'
      + '<div style="display:flex;gap:9px;flex-wrap:wrap">'
      + '<button class="btn pequeno" data-ir="equipos">+ Nuevo equipo</button>'
      + '<button class="btn pequeno" data-ir="partidos">+ Nuevo partido</button>'
      + '<button class="btn pequeno" data-ir="noticias">+ Nueva noticia</button>'
      + '<button class="btn pequeno" data-ir="premios">+ Nuevo premio</button>'
      + '<button class="btn pequeno" data-ir="directos">+ Nuevo directo</button>'
      + "</div></div>"
      + (datos.proximo
          ? '<div class="sub-tarjeta"><h4>Próximo partido</h4><p class="cuerpo">'
            + esc(datos.proximo.home) + " vs " + esc(datos.proximo.away) + " · "
            + esc(datos.proximo.fecha || "") + " " + esc(datos.proximo.hora || "")
            + "</p></div>"
          : "");
  };

  VISTAS.ajustes = function(){
    var s = datos.settings;
    var campos = cfg.ajustes;
    var cuerpo = campos.map(function(f){
      var v = s[f.clave];
      var entrada = f.tipo === "textarea"
        ? '<textarea id="a_' + f.clave + '" name="' + f.clave + '">' + esc(etiqueta(v)) + "</textarea>"
        : '<input id="a_' + f.clave + '" name="' + f.clave + '" type="' + (f.tipo || "text")
          + '" value="' + esc(etiqueta(v)) + '">';
      return '<div class="campo"><label for="a_' + f.clave + '">' + esc(f.etiqueta)
        + "</label>" + entrada + "</div>";
    }).join("");
    return '<form class="tarjeta" data-ajustes>' + cuerpo
      + '<button class="btn primario" type="submit">Guardar ajustes</button></form>';
  };

  VISTAS.divisiones = function(){
    return (datos.divisions || []).map(function(x){
      return '<div class="tarjeta" style="margin-bottom:13px">'
        + '<div class="tarjeta-cab"><h3>' + esc(x.name) + "</h3>"
        + '<span class="etiqueta diamante">' + esc(x.code || x.id) + "</span></div>"
        + '<div class="rejilla r4" style="gap:11px">'
        + '<div><span class="muy-tenue">Equipos</span><br><strong>' + esc(x.teams) + "</strong></div>"
        + '<div><span class="muy-tenue">Jornadas</span><br><strong>' + esc(x.journeys) + "</strong></div>"
        + '<div><span class="muy-tenue">Ascenso</span><br><strong>' + esc(x.promotion || "—") + "</strong></div>"
        + '<div><span class="muy-tenue">Descenso</span><br><strong>' + esc(x.relegation || "—") + "</strong></div>"
        + "</div>"
        + '<form class="tarjeta" data-divisiones="' + esc(x.id) + '" style="margin-top:13px">'
        + '<div class="rejilla r2" style="gap:0 15px">'
        + '<div class="campo"><label>Nombre</label><input name="name" value="' + esc(x.name) + '"></div>'
        + '<div class="campo"><label>Código</label><input name="code" value="' + esc(x.code) + '"></div>'
        + '<div class="campo"><label>Temporada</label><input name="season" value="' + esc(x.season) + '"></div>'
        + '<div class="campo"><label>Nº de equipos</label><input name="teams" type="number" value="'
          + esc(x.teams) + '"></div>'
        + '<div class="campo"><label>Jornadas</label><input name="journeys" type="number" value="'
          + esc(x.journeys) + '"></div>'
        + '<div class="campo"><label>Playoffs</label><input name="playoffs" value="' + esc(x.playoffs) + '"></div>'
        + '<div class="campo"><label>Ascenso</label><input name="promotion" value="' + esc(x.promotion) + '"></div>'
        + '<div class="campo"><label>Descenso</label><input name="relegation" value="' + esc(x.relegation) + '"></div>'
        + "</div>"
        + '<div class="campo"><label>Resumen</label><textarea name="summary">' + esc(x.summary) + "</textarea></div>"
        + '<button class="btn primario pequeno" type="submit">Guardar división</button>'
        + "</form></div>";
    }).join("") || vacio("Sin divisiones.");
  };

  VISTAS.equipos = function(){
    var todas = (datos.teams || []).map(function(t){
      return '<div class="fila-datos" data-equipo="' + esc(t.id) + '">'
        + (t.logo
            ? '<img class="escudo sm" src="' + esc(t.logo) + '" alt="" width="34" height="34">'
            : '<span class="escudo sm" style="display:grid;place-items:center;font-weight:900;font-size:.7rem">'
              + esc(etiqueta(t.name).slice(0,2).toUpperCase()) + "</span>")
        + '<span class="crece"><strong>' + esc(t.name) + "</strong><br>"
        + '<span class="muy-tenue">' + esc(t.division) + " · " + esc(t.coach || "sin DT") + "</span></span>"
        + '<span class="acciones">'
        + '<button class="btn pequeno" data-plantilla="' + esc(t.id) + '">Plantilla</button>'
        + '<button class="btn pequeno" data-editar="teams" data-id="' + esc(t.id) + '">Editar</button>'
        + '<button class="btn pequeno peligro" data-borrar="teams" data-id="' + esc(t.id) + '">Borrar</button>'
        + "</span></div>";
    }).join("") || vacio("Sin equipos.");
    return '<div data-detalle-caja></div>'
      + '<div style="margin-top:15px"><button class="btn primario" data-nuevo="teams">+ Nuevo equipo</button></div>'
      + todas;
  };

  VISTAS.partidos = function(){
    var todos = (datos.matches || []).map(function(p){
      var informe = (datos.eventos || []).filter(function(e){ return e.match_id === p.id; });
      return '<div class="fila-datos" data-partido="' + esc(p.id) + '">'
        + '<span class="crece"><strong>' + esc(p.home) + " vs " + esc(p.away) + "</strong><br>"
        + '<span class="muy-tenue">' + esc(p.division) + " · " + esc(p.status) + " · "
        + esc(p.date || "sin fecha") + " " + esc(p.time || "") + "</span></span>"
        + '<span class="acciones">'
        + '<button class="btn pequeno" data-informe="' + esc(p.id) + '">Informe ('
          + informe.length + ")</button>"
        + '<button class="btn pequeno" data-editar="matches" data-id="' + esc(p.id) + '">Editar</button>'
        + '<button class="btn pequeno peligro" data-borrar="matches" data-id="' + esc(p.id) + '">Borrar</button>'
        + "</span></div>";
    }).join("") || vacio("Sin partidos.");
    return '<div data-detalle-caja></div>'
      + '<div style="margin-top:15px"><button class="btn primario" data-nuevo="matches">+ Nuevo partido</button></div>'
      + todos;
  };

  function crudSimple(coleccion){
    return function(){
      var lista = (datos[coleccion] || []).map(function(i){
        return filaCRUD(coleccion, i);
      }).join("");
      return '<div data-detalle-caja></div>' + (lista || vacio("Sin registros."))
        + '<div style="margin-top:15px"><button class="btn primario" data-nuevo="'
          + esc(coleccion) + '">+ Nuevo</button></div>';
    };
  }
  // `equipos` y `partidos` tienen editores propios, no se sobrescriben aquí.
  Object.keys(cfg.mapa).forEach(function(vista){
    if (VISTAS[vista]) return;
    VISTAS[vista] = crudSimple(cfg.mapa[vista]);
  });

  VISTAS.reglamento = function(){
    return '<div class="aviso aviso-info">El reglamento se edita como bloques: puntos, listas y '
      + 'tarjetas. Guarda cada bloque con su botón.</div>'
      + (datos.rules || []).map(function(r){
          return '<div class="tarjeta" style="margin-bottom:13px">'
            + '<h3>' + esc(r.title) + "</h3>"
            + '<p class="cuerpo">' + esc(r.summary || "") + "</p>"
            + '<form data-reglas="' + esc(r.id) + '">'
            + '<div class="campo"><label>Título</label><input name="title" value="' + esc(r.title) + '"></div>'
            + '<div class="campo"><label>Resumen</label><input name="summary" value="'
              + esc(r.summary || "") + '"></div>'
            + '<div class="campo"><label>Puntos (uno por línea)</label><textarea name="items">'
              + esc((r.items || []).map(function(i){ return i.title; }).join("\n"))
              + "</textarea></div>"
            + '<button class="btn primario pequeno" type="submit">Guardar</button>'
            + "</form></div>";
        }).join("") || vacio("Sin reglas.");
  };

  VISTAS.usuarios = function(){
    return '<div class="tabla-caja"><table><caption>Cuentas registradas</caption><thead><tr>'
      + "<th>Usuario</th><th>Correo</th><th>Alta</th><th>Último acceso</th>"
      + "<th>Premium</th><th>Admin</th></tr></thead><tbody>"
      + (datos.usuarios || []).map(function(u){
          return "<tr><td><strong>" + esc(u.username) + "</strong></td><td>" + esc(u.email)
            + "</td><td class=\"tenue\">" + esc(u.created_at) + "</td><td class=\"tenue\">"
            + esc(u.last_login_at || "—") + "</td>"
            + '<td>' + (u.is_premium ? '<span class="etiqueta oro">Sí</span>' : "No") + "</td>"
            + '<td>' + (u.is_admin ? '<span class="etiqueta violeta">Sí</span>' : "No") + "</td></tr>";
        }).join("")
      + "</tbody></table></div>";
  };

  /* ---------- pintado ---------- */
  function pintar(vista){
    cuerpo.innerHTML = (VISTAS[vista] || function(){ return vacio("Vista no disponible."); })();
    d.querySelectorAll(".panel-menu button").forEach(function(b){
      if (b.dataset.vista === vista) b.setAttribute("aria-current", "true");
      else b.removeAttribute("aria-current");
    });
  }

  /* Mete un bloque en el hueco [data-detalle-caja] o, si no existe, al principio. */
  function mostrarBloque(html){
    var hueco = d.querySelector("[data-detalle-caja]");
    var caja = d.createElement("div");
    caja.className = "data-detalle-caja";
    caja.innerHTML = html;
    if (hueco) hueco.replaceWith(caja); else cuerpo.prepend(caja);
    caja.scrollIntoView({ behavior:"smooth", block:"nearest" });
    return caja;
  }

  function mostrarForm(coleccion, registro){
    mostrarBloque(formCRUD(coleccion, registro));
  }

  /* ---------- red ---------- */
  function pedir(url, opciones){
    opciones = opciones || {};
    opciones.headers = Object.assign({
      "X-CSRF-Token": cfg.csrf, "X-Requested-With": "fetch"
    }, opciones.headers || {});
    if (opciones.form !== undefined) {
      opciones.method = opciones.method || "POST";
      opciones.body = opciones.form;
    } else if (opciones.json !== undefined) {
      opciones.method = opciones.method || "POST";
      opciones.headers["Content-Type"] = "application/json";
      opciones.body = JSON.stringify(opciones.json);
    }
    return fetch(url, opciones).then(function(r){
      return r.json().catch(function(){ return {}; }).then(function(j){
        if (!r.ok) throw new Error(j.error || ("Error " + r.status));
        return j;
      });
    });
  }

  function recargar(){
    return pedir("/api/admin/data", { method:"GET" }).then(function(j){
      datos = Object.assign(datos, j);
      guardar();
    });
  }
  function guardar(){ try{ sessionStorage.setItem("panel", JSON.stringify(datos)); }catch(e){} }

  /* ---------- eventos ---------- */
  document.addEventListener("click", function(ev){
    var t = ev.target.closest("[data-vista],[data-ir],[data-nuevo],[data-editar],[data-borrar],"
      + "[data-plantilla],[data-informe],[data-anadir-jugador],[data-quitar-jugador],"
      + "[data-anadir-evento],[data-quitar-evento],[data-cancelar]");
    if(!t) return;

    if (t.dataset.vista){ pintar(t.dataset.vista); location.hash = t.dataset.vista; return; }
    if (t.dataset.ir){ pintar(t.dataset.ir); location.hash = t.dataset.ir; return; }

    if (t.dataset.anadirJugador){
      var cajaJ = t.closest("form").querySelector("[data-filas-jugadores]");
      cajaJ.insertAdjacentHTML("beforeend", plantillaVacia()); return;
    }
    if (t.dataset.quitarJugador){
      var filaJ = t.closest(".jug-fila");
      if (document.querySelectorAll(".jug-fila").length > 1) filaJ.remove();
      return;
    }
    if (t.dataset.anadirEvento){
      var cajaE = t.closest("form").querySelector("[data-filas-eventos]");
      cajaE.insertAdjacentHTML("beforeend", eventoVacio()); return;
    }
    if (t.dataset.quitarEvento){
      var filaE = t.closest(".ev-fila");
      if (document.querySelectorAll(".ev-fila").length > 1) filaE.remove();
      return;
    }
    if (t.dataset.cancelar){ pintar(vistaActual()); return; }

    var coleccion = t.dataset.nuevo || t.dataset.editar || t.dataset.borrar
      || t.dataset.plantilla || t.dataset.informe;
    if(!coleccion) return;

    if (t.dataset.nuevo){ mostrarForm(t.dataset.nuevo, null); return; }

    if (t.dataset.editar){
      var col = t.dataset.editar;
      var item = (datos[col] || []).filter(function(x){ return x.id === t.dataset.id; })[0];
      if(!item) return;
      mostrarForm(col, item);
      return;
    }

    if (t.dataset.plantilla){
      var equipo = (datos.teams || []).filter(function(x){ return x.id === t.dataset.id; })[0];
      if(!equipo) return;
      mostrarBloque(editorJugadores(equipo));
      return;
    }

    if (t.dataset.informe){
      var partido = (datos.matches || []).filter(function(x){ return x.id === t.dataset.id; })[0];
      if(!partido) return;
      var informe = '<div class="sub-tarjeta"><h4>Informe de '
        + esc(partido.home) + " vs " + esc(partido.away) + "</h4>"
        + '<p class="cuerpo">En el editor del partido marca el <strong>MVP</strong> y los '
        + "dos <strong>porteros</strong> (para la portería a cero). Debajo van los goles y "
        + "las asistencias.</p>"
        + '<form data-informe-partido="' + esc(partido.id) + '">'
        + '<div class="rejilla r3" style="gap:0 13px">'
        + '<div class="campo"><label>MVP</label><input name="mvp" value="' + esc(partido.mvp || "") + '"></div>'
        + '<div class="campo"><label>Portero local</label><input name="keeperHome" value="'
          + esc(partido.keeperHome || "") + '"></div>'
        + '<div class="campo"><label>Portero visitante</label><input name="keeperAway" value="'
          + esc(partido.keeperAway || "") + '"></div>'
        + "</div>"
        + '<div class="rejilla r3" style="gap:0 13px">'
        + '<div class="campo"><label>Goles local</label><input name="homeGoals" type="number" value="'
          + esc(partido.homeGoals === null ? "" : partido.homeGoals) + '"></div>'
        + '<div class="campo"><label>Goles visitante</label><input name="awayGoals" type="number" value="'
          + esc(partido.awayGoals === null ? "" : partido.awayGoals) + '"></div>'
        + '<div class="campo"><label>Notas</label><input name="notes" value="'
          + esc(partido.notes || "") + '"></div>'
        + "</div>"
        + '<button class="btn primario pequeno" type="submit">Guardar marcador y reconocimientos</button>'
        + "</form></div>" + editorEventos(partido);
      mostrarBloque(informe);
      return;
    }

    if (t.dataset.borrar){
      var colB = t.dataset.borrar;
      if(!window.confirm("¿Borrar este registro? No se puede deshacer.")) return;
      pedir("/api/admin/" + colB + "/" + encodeURIComponent(t.dataset.id), { method:"DELETE" })
        .then(recargar)
        .then(function(){ pintar(vistaActual()); })
        .catch(function(e){ window.alert(e.message); });
    }
  });

  document.addEventListener("submit", function(ev){
    var f = ev.target;
    ev.preventDefault();

    if (f.dataset.guardar){
      var fd = new FormData(f);
      // Los checkboxes desmarcados no viajan en FormData: se envían como 0.
      (datos.campos[f.dataset.guardar] || []).forEach(function(campo){
        if (campo.tipo === "bool" && !fd.has(campo.clave)) fd.append(campo.clave, "0");
      });
      var destino = f.dataset.id ? "/api/admin/" + f.dataset.guardar + "/" + f.dataset.id
                                 : "/api/admin/" + f.dataset.guardar;
      pedir(destino, { method: f.dataset.id ? "PUT" : "POST", form: fd })
        .then(recargar).then(function(){ pintar(vistaActual()); })
        .catch(function(e){ window.alert(e.message); });
      return;
    }

    if (f.dataset.jugadores){
      var filas = Array.prototype.slice.call(f.querySelectorAll(".jug-fila")).map(function(fila){
        var q = function(n){ return fila.querySelector("[name=" + n + "]"); };
        return { name: q("name").value.trim(), jersey: q("jersey").value,
                 position: q("position").value, note: q("note").value };
      }).filter(function(j){ return j.name; });
      pedir("/api/admin/jugadores/" + f.dataset.jugadores, { json: { jugadores: filas } })
        .then(recargar).then(function(){ pintar("equipos"); })
        .catch(function(e){ window.alert(e.message); });
      return;
    }

    if (f.dataset.eventos){
      var partido = (datos.matches || []).filter(function(x){ return x.id === f.dataset.eventos; })[0] || {};
      var evs = Array.prototype.slice.call(f.querySelectorAll(".ev-fila")).map(function(fila){
        var q = function(n){ return fila.querySelector("[name=" + n + "]"); };
        return { player: q("player").value.trim(), side: q("side").value,
                 minute: q("minute").value, kind: q("kind").value };
      }).filter(function(x){ return x.player; });
      pedir("/api/admin/eventos/" + f.dataset.eventos, { json: { eventos: evs } })
        .then(recargar).then(function(){ pintar("partidos"); })
        .catch(function(e){ window.alert(e.message); });
      return;
    }

    if (f.dataset.informePartido){
      var fd2 = new FormData(f), cuerpo2 = {};
      fd2.forEach(function(v, k){ cuerpo2[k] = v; });
      pedir("/api/admin/matches/" + f.dataset.informePartido, { method:"PUT", json: cuerpo2 })
        .then(recargar).then(function(){ pintar("partidos"); })
        .catch(function(e){ window.alert(e.message); });
      return;
    }

    if (f.hasAttribute("data-ajustes")){
      var fd3 = new FormData(f), cuerpo3 = {};
      fd3.forEach(function(v, k){ cuerpo3[k] = v; });
      pedir("/api/admin/ajustes", { method:"PUT", json: cuerpo3 })
        .then(recargar).then(function(){ window.alert("Ajustes guardados."); })
        .catch(function(e){ window.alert(e.message); });
      return;
    }

    if (f.dataset.divisiones){
      var fd4 = new FormData(f), d4 = {};
      fd4.forEach(function(v, k){ d4[k] = v; });
      var lista = (datos.divisions || []).map(function(x){
        return x.id === f.dataset.divisiones ? Object.assign({}, x, d4) : x;
      });
      pedir("/api/admin/divisiones", { json: lista })
        .then(recargar).then(function(){ pintar("divisiones"); })
        .catch(function(e){ window.alert(e.message); });
      return;
    }

    if (f.dataset.reglas){
      var fd5 = new FormData(f);
      var texto = fd5.get("items") || "";
      var items = texto.split("\n").map(function(l){ return l.trim(); })
        .filter(Boolean).map(function(l){ return { title:l }; });
      var reglas = (datos.rules || []).map(function(r){
        return r.id === f.dataset.reglas
          ? { id:r.id, title:fd5.get("title"), summary:fd5.get("summary"), items:items,
              blocks:r.blocks || [], cards:r.cards || [] }
          : r;
      });
      pedir("/api/admin/reglas", { json: reglas })
        .then(recargar).then(function(){ pintar("reglamento"); })
        .catch(function(e){ window.alert(e.message); });
    }
  });

  function vistaActual(){
    return (location.hash || "#resumen").replace("#","") || "resumen";
  }

  try{
    var guardado = sessionStorage.getItem("panel");
    if (guardado) datos = Object.assign(datos, JSON.parse(guardado));
  }catch(e){}

  pintar(VISTAS[vistaActual()] ? vistaActual() : "resumen");
})();
"""
# ==============================================================================
#  PLANTILLAS Y CONTEXTO
# ==============================================================================

PLANTILLAS = {
    "base.html": TPL_BASE,
    "portada.html": TPL_PORTADA,
    "acceso.html": TPL_ACCESO,
    "cuenta.html": TPL_CUENTA,
    "privacidad.html": TPL_PRIVACIDAD,
    "panel.html": TPL_PANEL,
    "error.html": TPL_ERROR,
}
app.jinja_loader = DictLoader(PLANTILLAS)


def escudos_equipos() -> dict:
    """Nombre de equipo -> logo, para ponerlo junto a los partidos."""
    salida = {}
    for equipo in consultar("SELECT `name`, `logo` FROM `equipos` WHERE `logo` <> ''"):
        salida[sin_acentos(equipo["name"]).upper()] = equipo["logo"]
    return salida


def escudo_equipo(nombre, mapa=None) -> str:
    if not nombre:
        return ""
    mapa = escudos_equipos() if mapa is None else mapa
    return mapa.get(sin_acentos(str(nombre)).upper(), "")


def usuario_anonimo() -> dict:
    return {"username": "", "is_premium": False, "is_admin": False,
            "display_name": "", "email": "", "avatar_url": "", "google_id": ""}


def contexto_base() -> dict:
    ajustes = leer_ajustes()
    url_base = request.url_root.rstrip("/") if request else APP_URL
    anfitrion = url_base.split("//")[-1].split("/")[0].split(":")[0]
    return {
        "usuario": usuario_actual() or usuario_anonimo(),
        "ajustes": ajustes,
        "css": CSS,
        "js": JS,
        "js_panel": JS_PANEL,
        "navegacion": NAVEGACION,
        "google_activo": bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET),
        "url_base": url_base,
        "anfitrion": anfitrion,
        "csrf": csrf_token(),
        "anio": datetime.now().year,
        "escudo": escudo_equipo(ajustes.get("leagueName")),
        "noindex": True,
    }


def render(nombre: str, **extra):
    datos = contexto_base()
    datos.update(extra)
    return render_template(nombre, **datos)


# ==============================================================================
#  DATOS DE LA PORTADA
# ==============================================================================

def premios_agrupados() -> list:
    """Premios agrupados por temporada y categoría, como en el museo."""
    grupos: dict = {}
    for premio in leer_coleccion("awards"):
        temporada = str(premio.get("season") or "").strip()
        anio = str(premio.get("year") or "").strip()
        etiqueta = " · ".join([p for p in (temporada, anio) if p]) or "Historia de la liga"
        grupos.setdefault(etiqueta, {"titulo": etiqueta, "items": []})["items"].append(premio)
    orden = sorted(grupos.values(),
                   key=lambda g: str(g["titulo"])[-4:] if str(g["titulo"])[-4:].isdigit() else "0",
                   reverse=True)
    return orden


def jornadas_partidos(partidos: list) -> list:
    """Agrupa los partidos por división y jornada para la pestaña Fechas."""
    mapa: dict = {}
    for partido in partidos:
        clave = (partido.get("division") or "", partido.get("journey") or 0)
        etiqueta = partido.get("journeyLabel") or (
            "Jornada " + str(partido.get("journey")) if partido.get("journey") else "Sin jornada")
        grupo = mapa.setdefault(clave, {
            "etiqueta": etiqueta,
            "division": partido.get("divisionName") or "",
            "partidos": [],
        })
        grupo["partidos"].append(partido)
    for grupo in mapa.values():
        grupo["partidos"].sort(key=lambda p: (str(p.get("date") or ""), str(p.get("time") or "")))
    return sorted(mapa.values(), key=lambda g: (g["division"], str(g["etiqueta"])))


def totales_liga(ajustes: dict, divisiones: list, equipos: list, partidos: list) -> dict:
    """Cifras grandes de la liga: las de la portada, el panel y la статистика."""
    porterias, mvp = 0, 0
    for partido in partidos:
        if partido.get("status") != "finalizado":
            continue
        if partido.get("keeper_home") and int(partido.get("homeGoals") or 0) == 0:
            porterias += 1
        if partido.get("keeper_away") and int(partido.get("awayGoals") or 0) == 0:
            porterias += 1
        if partido.get("mvp"):
            mvp += 1
    eventos = leer_eventos()
    return {
        "divisiones": len(divisiones),
        "equipos": len(equipos),
        "jugadores": len(leer_jugadores()),
        "partidos": len(partidos),
        "goles": sum(1 for e in eventos if e.get("kind") == "gol"),
        "asistencias": sum(1 for e in eventos if e.get("kind") == "asistencia"),
        "porterias": porterias,
        "mvp": mvp,
        "premios": len(leer_coleccion("awards")),
        "noticias": len(leer_coleccion("news")),
        "usuarios": int(valor("SELECT COUNT(*) AS n FROM `usuarios`", (), 0) or 0),
    }


def datos_portada() -> dict:
    ajustes = leer_ajustes()
    divisiones = leer_divisiones()
    equipos = leer_coleccion("teams")
    partidos = leer_coleccion("matches")

    nombres_division = {d["id"]: d["name"] for d in divisiones}
    logotipos = escudos_equipos()

    for partido in partidos:
        partido["divisionName"] = nombres_division.get(partido.get("division"), "")
        partido["logo_home"] = escudo_equipo(partido.get("home"), logotipos)
        partido["logo_away"] = escudo_equipo(partido.get("away"), logotipos)
        partido["informe"] = resumen_partido(partido)

    por_equipo: dict = {}
    for jugador in leer_jugadores():
        por_equipo.setdefault(jugador["team_id"], []).append(jugador)
    for equipo in equipos:
        equipo["division_name"] = nombres_division.get(equipo.get("division"), "")
        equipo["jugadores"] = por_equipo.get(equipo["id"], [])

    alianzas = leer_coleccion("alliances")
    redes = leer_coleccion("social")
    return {
        "ajustes": ajustes,
        "divisiones": divisiones,
        "equipos": equipos,
        "partidos": partidos,
        "jornadas": jornadas_partidos(partidos),
        "tablas": clasificaciones(equipos, partidos, divisiones, ajustes),
        "estadisticas": estadisticas_jugadores(),
        "proximo": proximo_partido(partidos, divisiones),
        "reglas": leer_reglas(),
        "salas": leer_coleccion("pubs"),
        "premios_agrupados": premios_agrupados(),
        "noticias": leer_coleccion("news"),
        "anuncios": leer_coleccion("announcements"),
        "alianzas": [a for a in alianzas if a.get("status") != "proxima"],
        "alianzas_proximas": [a for a in alianzas if a.get("status") == "proxima"],
        "redes": [r for r in redes if not r.get("is_streamer")],
        "streamers": [r for r in redes if r.get("is_streamer")],
        "personal": leer_coleccion("staff"),
        "directos": leer_coleccion("live"),
        "donaciones": leer_coleccion("donations"),
        "totales": totales_liga(ajustes, divisiones, equipos, partidos),
    }


# ==============================================================================
#  ESTÁTICOS Y ERRORES
# ==============================================================================

class SesionCaducada(Exception):
    """CSRF inválido o ausente: 419, un código que Werkzeug no trae de serie."""


@app.errorhandler(SesionCaducada)
def manejar_sesion_caducada(error):
    if wants_json():
        return jsonify({"error": "Sesión caducada. Recarga la página."}), 419
    return pagina_error(419, "Sesión caducada",
                        "Vuelve a cargar la página e inténtalo de nuevo.")


@app.get("/assets/<path:nombre>")
def assets_archivo(nombre: str):
    """Sirve assets/ y bloquea cualquier ruta fuera de esa carpeta."""
    return send_from_directory(ASSETS, nombre)


@app.get("/uploads/<path:nombre>")
def uploads_archivo(nombre: str):
    return send_from_directory(UPLOADS, nombre)


@app.get("/robots.txt")
def robots():
    return Response("User-agent: *\nDisallow: /\n",
                    mimetype="text/plain; charset=utf-8")


def pagina_error(codigo: int, titulo: str, mensaje: str, destino: str = "/", accion: str = "Volver"):
    return render("error.html", codigo=codigo, titulo=titulo, mensaje=mensaje,
                  destino=destino, accion=accion, league=APP_NOMBRE,
                  descripcion=titulo), codigo


@app.errorhandler(400)
@app.errorhandler(401)
@app.errorhandler(403)
@app.errorhandler(404)
@app.errorhandler(405)
@app.errorhandler(413)
@app.errorhandler(500)
def manejar_error(error):
    codigo = getattr(error, "code", 500)
    if wants_json():
        return jsonify({"error": getattr(error, "description", "Error")}), codigo
    textos = {
        400: ("Solicitud incorrecta", "El navegador envió algo que no entendimos."),
        401: ("Necesitas iniciar sesión", "Esta zona es privada de la liga."),
        403: ("Acceso denegado", "Tu cuenta no tiene permiso para esta zona."),
        404: ("Página no encontrada", "Ese enlace no existe o cambió de sitio."),
        405: ("Método no permitido", "Esta ruta no acepta esa operación."),
        413: ("Archivo demasiado grande", "Las imágenes deben pesar menos de 4 MB."),
        500: ("Error del servidor", "Algo falló por nuestra parte. Inténtalo otra vez."),
    }
    titulo, mensaje = textos.get(codigo, textos[500])
    return pagina_error(codigo, titulo, mensaje)


@app.errorhandler(ValueError)
def manejar_valor(error):
    """Los errores de validación de los helpers llegan como ValueError."""
    if wants_json():
        return jsonify({"error": str(error)}), 400
    return pagina_error(400, "No se pudo guardar", str(error))


# ==============================================================================
#  ACCESO Y REGISTRO
# ==============================================================================

def pintar_acceso(modo: str, errores=None, datos=None, aviso=""):
    ajustes = leer_ajustes()
    return render("acceso.html",
                  modo=modo,
                  errores=errores or [],
                  datos=datos or {},
                  aviso=aviso,
                  primer_usuario=int(valor("SELECT COUNT(*) AS n FROM `usuarios`", (), 0) or 0) == 0,
                  logo=escudo_equipo(ajustes.get("leagueName")),
                  titulo=("Crear cuenta · " if modo == "registro" else "Entrar · ") + APP_NOMBRE,
                  encabezado=("Crea tu cuenta" if modo == "registro"
                              else "Bienvenido de nuevo"),
                  sub=("Regístrate con un usuario y un correo. El primero queda como "
                       "administrador de la liga."
                       if modo == "registro" else
                       "La liga es privada: entra con tu cuenta para ver todas las secciones."),
                  descripcion="Acceso privado a " + APP_NOMBRE)


@app.route("/entrar", methods=["GET", "POST"])
def entrar():
    if usuario_logueado():
        return redirect(url_for("portada"))
    if request.method == "GET":
        return pintar_acceso("entrar", aviso={
            "salida": "Has cerrado sesión.",
            "eliminada": "Tu cuenta se ha eliminado.",
        }.get(str(request.args.get("aviso") or "").strip().lower(), ""))

    entrada = request.form
    identificador = str(entrada.get("identificador") or "").strip()
    contrasena = str(entrada.get("password") or "")
    errores: list[str] = []

    if ip_bloqueada("entrar"):
        return pintar_acceso("entrar", ["Demasiados intentos. Espera unos minutos."],
                             {"identificador": identificador})
    if not identificador or not contrasena:
        errores.append("Escribe tu usuario y tu contraseña.")

    registro = usuario_credenciales(identificador, contrasena) if not errores else None
    if not errores:
        registrar_intento("entrar", identificador.lower(), registro is not None)
        if registro is None:
            errores.append("El usuario o la contraseña no son correctos.")
        else:
            usuario_entrar(registro)
            destino = request.args.get("volver") or ""
            if not destino.startswith("/") or destino.startswith("//"):
                destino = url_for("portada")
            return redirect(destino)
    return pintar_acceso("entrar", errores, {"identificador": identificador})


@app.route("/registro", methods=["GET", "POST"])
def registro():
    if usuario_logueado():
        return redirect(url_for("portada"))
    if request.method == "GET":
        return pintar_acceso("registro")

    entrada = request.form
    nuevo, errores = validar_registro(
        entrada.get("username", ""), entrada.get("email", ""),
        entrada.get("password", ""), entrada.get("confirmar", ""),
        bool(entrada.get("acepta")), bool(entrada.get("boletin")))
    if errores:
        return pintar_acceso("registro", errores, {
            "username": entrada.get("username", ""), "email": entrada.get("email", "")})

    usuario_entrar(nuevo)
    if nuevo["is_admin"]:
        return redirect(url_for("panel"))
    return redirect(url_for("portada"))


@app.post("/salir")
@requiere_csrf
def salir():
    usuario_cerrar()
    return redirect(url_for("entrar", aviso="salida"))


# ==============================================================================
#  GOOGLE
# ==============================================================================

@app.route("/cuenta/google", methods=["GET", "POST"])
def google_entrar():
    """Arranca el flujo OAuth de Google: sin librerías externas, con urllib."""
    if not (GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET and GOOGLE_REDIRECT):
        destino = url_for("perfil") if usuario_actual() else url_for("entrar")
        return redirect(destino)
    if request.method == "POST":
        csrf_exigir()

    estado = secrets.token_urlsafe(24)
    session["google_estado"] = estado
    session["google_vincular"] = bool(usuario_actual())
    consulta = urllib.parse.urlencode({
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "prompt": "select_account",
        "state": estado,
    })
    return redirect("https://accounts.google.com/o/oauth2/v2/auth?" + consulta)


@app.post("/cuenta/google/quitar")
@requiere_login
@requiere_csrf
def google_quitar():
    usuario = usuario_actual()
    if not usuario.get("google_id"):
        return redirect(url_for("perfil"))
    ejecutar("UPDATE `usuarios` SET `google_id` = NULL WHERE `id` = %s", (usuario["id"],))
    confirmar()
    return redirect(url_for("perfil", aviso="google"))


@app.get("/cuenta/google/callback")
def google_callback():
    if not GOOGLE_CLIENT_ID:
        return pagina_error(503, "Google no configurado",
                            "Faltan GOOGLE_CLIENT_ID y GOOGLE_CLIENT_SECRET.")
    esperado = session.pop("google_estado", "")
    vincular = bool(session.pop("google_vincular", False))
    if not esperado or not secrets.compare_digest(str(esperado), str(request.args.get("state") or "")):
        return pagina_error(400, "Estado no válido", "El enlace de Google caducó. Inténtalo otra vez.")

    codigo = request.args.get("code") or ""
    if not codigo:
        return pagina_error(400, "Google no devolvió permiso",
                            request.args.get("error") or "Cancelaste el acceso.")

    try:
        datos_token = urllib.parse.urlencode({
            "code": codigo,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT,
            "grant_type": "authorization_code",
        }).encode()
        peticion = urllib.request.Request(
            "https://oauth2.googleapis.com/token", data=datos_token,
            headers={"Content-Type": "application/x-www-form-urlencoded"})
        token = json.loads(urllib.request.urlopen(peticion, timeout=12).read())
        acceso = token.get("access_token") or ""
        if not acceso:
            raise ValueError("sin token")

        ficha = json.loads(urllib.request.urlopen(urllib.request.Request(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": "Bearer " + acceso}), timeout=12).read())
    except Exception:
        return pagina_error(400, "No se pudo leer tu cuenta de Google",
                            "Vuelve a intentarlo en unos minutos.")

    google_id = str(ficha.get("sub") or "").strip()
    correo = str(ficha.get("email") or "").strip().lower()
    if not google_id or not RE_EMAIL.match(correo):
        return pagina_error(400, "Cuenta de Google incompleta",
                            "Google no nos devolvió un correo válido.")

    actual = usuario_actual()
    existente = fila("SELECT * FROM `usuarios` WHERE google_id = %s OR email = %s LIMIT 1",
                     (google_id, correo))

    if actual:
        if existente and int(existente["id"]) != int(actual["id"]):
            return pagina_error(409, "Esa cuenta ya existe",
                                "El correo de Google ya está en uso por otra cuenta de la liga.")
        ejecutar("UPDATE `usuarios` SET `google_id` = %s, `avatar_url` = COALESCE(avatar_url, %s)"
                 " WHERE `id` = %s",
                 (google_id, str(ficha.get("picture") or ""), actual["id"]))
        confirmar()
        return redirect(url_for("perfil", aviso="google"))

    if existente is None:
        nombre = usuario_normalizado(str(ficha.get("name") or correo.split("@")[0]))
        if not RE_USUARIO.match(nombre):
            nombre = "jugador"
        candidato = nombre
        numero = 1
        while valor("SELECT id FROM `usuarios` WHERE username = %s", (candidato,)):
            numero += 1
            candidato = f"{nombre}-{numero}"
        ejecutar("INSERT INTO `usuarios` (`username`,`email`,`password_hash`,`display_name`,"
                 "`avatar_url`,`google_id`,`newsletter`,`terms_accepted_at`,`created_at`,`last_login_at`)"
                 " VALUES (%s,%s,%s,%s,%s,%s,0,NOW(),NOW(),NOW())",
                 (candidato, correo, SEÑUELO,
                  str(ficha.get("name") or candidato)[:80],
                  str(ficha.get("picture") or ""), google_id))
        nuevo_id = int(valor("SELECT LAST_INSERT_ID() AS n") or 0)
        registrar_consentimiento(nuevo_id)
        existente = fila("SELECT * FROM `usuarios` WHERE `id` = %s", (nuevo_id,))
    elif not existente.get("google_id"):
        # La cuenta ya existía con contraseña: se vincula automáticamente.
        ejecutar("UPDATE `usuarios` SET `google_id` = %s WHERE `id` = %s",
                 (google_id, existente["id"]))
        existente["google_id"] = google_id

    confirmar()
    usuario_entrar(existente)
    return redirect(url_for("perfil", aviso="google"))


# ==============================================================================
#  CUENTA
# ==============================================================================

def aviso_cuenta(usuario: dict, clave: str = "") -> str:
    """Traduce el parámetro ?aviso= de las rutas de cuenta a un mensaje."""
    mensajes = {
        "bienvenida": "¡Cuenta creada! Ya puedes gestionar tu perfil desde la tuerca.",
        "premium": ("Modo premium activado." if usuario.get("is_premium")
                    else "Modo premium desactivado."),
        "perfil": "Perfil actualizado.",
        "google": "Cuenta de Google vinculada correctamente.",
        "google-desvinculado": "Cuenta de Google desvinculada.",
    }
    return mensajes.get(str(clave or "").strip().lower(), "")


@app.route("/cuenta", methods=["GET"])
@app.route("/perfil", methods=["GET", "POST"])
@requiere_login
def perfil():
    usuario = usuario_actual()
    errores, ok = [], ""
    if request.method == "POST":
        entrada = request.form.to_dict()
        entrada["avatar"] = request.files.get("avatar")
        errores = usuario_perfil_actualizar(usuario, entrada)
        if not errores:
            confirmar()
            return redirect(url_for("perfil", aviso="perfil"))
    ok = aviso_cuenta(usuario, request.args.get("aviso", ""))
    return render("cuenta.html", modo="perfil",
                  encabezado="Tu perfil", sub="Así te ven dentro de la liga.",
                  errores=errores, ok=ok,
                  equipos=leer_coleccion("teams"), usuario=usuario)


@app.route("/cuenta/contrasena", methods=["GET", "POST"])
@requiere_login
def password():
    usuario = usuario_actual()
    errores = []
    if request.method == "POST":
        errores = usuario_password_actualizar(
            usuario, request.form.get("actual", ""), request.form.get("nueva", ""),
            request.form.get("confirmar", ""), exigir_actual=usuario["tiene_password"])
        if not errores:
            return redirect(url_for("password", aviso="Contrasena cambiada."))
    return render("cuenta.html", modo="password",
                  encabezado="Cambiar contraseña",
                  sub="Mínimo 8 caracteres.", errores=errores, ok="", usuario=usuario)


@app.get("/cuenta/datos")
@requiere_login
def datos():
    return render("cuenta.html", modo="datos", encabezado="Tus datos",
                  sub="Todo lo que la liga guarda de tu cuenta.",
                  errores=[], ok="", usuario=usuario_actual())


@app.get("/cuenta/datos.json")
@requiere_login
def datos_json():
    carga = usuario_exportar(usuario_actual())
    respuesta = Response(json.dumps(carga, indent=2, ensure_ascii=False, default=str),
                         mimetype="application/json")
    respuesta.headers["Content-Disposition"] = 'attachment; filename="mis-datos.json"'
    return respuesta


@app.route("/cuenta/eliminar", methods=["GET", "POST"])
@requiere_login
def eliminar_cuenta():
    usuario = usuario_actual()
    if request.method == "POST":
        if request.form.get("confirmar") != "BORRAR":
            return render("cuenta.html", modo="eliminar", encabezado="Eliminar cuenta",
                          sub="Esta acción no se puede deshacer.",
                          errores=["Marca la casilla para confirmar."], ok="", usuario=usuario)
        usuario_eliminar(usuario)
        return redirect(url_for("entrar", aviso="eliminada"))
    return render("cuenta.html", modo="eliminar", encabezado="Eliminar tu cuenta",
                  sub="Borra tu cuenta y todos tus datos de la liga.",
                  errores=[], ok="", usuario=usuario)


@app.post("/cuenta/premium")
@requiere_csrf
def premium():
    usuario = usuario_actual()
    usuario_premium_actualizar(usuario, not usuario["is_premium"])
    return redirect(url_for("portada"))


@app.get("/privacidad")
def privacidad():
    usuario = usuario_actual()
    if usuario is None:
        return render("privacidad.html", version=POLITICA_VERSION,
                      fecha=POLITICA_FECHA, empresa=POLITICA_EMPRESA, contacto=POLITICA_CONTACTO,
                      titulo="Privacidad · " + APP_NOMBRE,
                      descripcion="Política de privacidad de " + APP_NOMBRE,
                      ajustes=leer_ajustes(), css=CSS, navegacion=NAVEGACION,
                      google_activo=False, url_base=APP_URL, anio=datetime.now().year,
                      escudo="", csrf=csrf_token(), anfitrion=APP_URL,
                      js=JS, js_panel=JS_PANEL, noindex=True,
                      usuario={"username": "", "is_premium": False, "is_admin": False,
                               "display_name": "", "email": "", "avatar_url": ""})
    return render("privacidad.html", version=POLITICA_VERSION, fecha=POLITICA_FECHA,
                  empresa=POLITICA_EMPRESA, contacto=POLITICA_CONTACTO)


# ==============================================================================
#  PORTADA
# ==============================================================================

@app.get("/")
@requiere_login
def portada():
    datos = datos_portada()
    ajustes = datos["ajustes"]
    return render("portada.html",
                  titulo=f"{ajustes['leagueName']} · {ajustes['season'] or 'Liga de HaxBall'}",
                  descripcion=(ajustes["description"] or ajustes["tagline"]
                               or "Liga competitiva de HaxBall X5 con divisiones, premios y datos."),
                  noindex=False, **datos)


# ==============================================================================
#  PANEL DE ADMINISTRACIÓN
# ==============================================================================

CAMPOS_PANEL = {
    "teams": {"principal": "name", "etiquetas": ["division", "coach"],
              "campos": ["name", "division", "coach", "colors", "logo", "note", "sort_order"]},
    "matches": {"principal": "home", "etiquetas": ["away", "date", "status"],
                "campos": ["division", "stage", "journey", "journeyLabel", "date", "time",
                           "home", "away", "homeGoals", "awayGoals", "status", "replay", "notes"]},
    "pubs": {"principal": "label", "etiquetas": ["name", "status"],
             "campos": ["label", "name", "url", "status", "players", "note", "sort_order"]},
    "news": {"principal": "title", "etiquetas": ["category", "date"],
             "campos": ["title", "category", "excerpt", "body", "date", "author",
                        "image", "pinned"]},
    "announcements": {"principal": "title", "etiquetas": ["season", "kind"],
                      "campos": ["title", "kicker", "season", "kind", "date",
                                 "text", "closing", "warning"]},
    "awards": {"principal": "title", "etiquetas": ["team", "year", "category"],
               "campos": ["title", "team", "text", "season", "division",
                          "category", "image", "year"]},
    "important": {"principal": "title", "etiquetas": ["kind", "cta"],
                  "campos": ["title", "description", "kind", "href", "cta", "sort_order"]},
    "staff": {"principal": "name", "etiquetas": ["role", "username"],
              "campos": ["name", "username", "role", "bio", "avatar", "banner",
                         "focus", "github", "instagram", "discord", "available",
                         "tags", "sort_order"]},
    "alliances": {"principal": "name", "etiquetas": ["kind", "status"],
                  "campos": ["name", "kind", "description", "href", "cta",
                             "image", "status", "sort_order"]},
    "social": {"principal": "handle", "etiquetas": ["network", "followers"],
               "campos": ["network", "owner_name", "handle", "url", "followers",
                          "is_streamer", "sort_order"]},
    "live": {"principal": "league", "etiquetas": ["home", "away", "platform"],
             "campos": ["league", "home", "away", "home_score", "away_score", "channel",
                        "platform", "url", "viewer_count", "starts_at", "is_live", "sort_order"]},
    "donations": {"principal": "title", "etiquetas": ["kind", "method"],
                  "campos": ["title", "description", "kind", "amount", "method",
                             "account", "goal", "raised", "is_active", "sort_order"]},
}

VISTA_COLECCION = {
    "salas": "pubs", "noticias": "news", "anuncios": "announcements", "premios": "awards",
    "accesos": "important", "personal": "staff", "alianzas": "alliances", "redes": "social",
    "directos": "live", "donaciones": "donations", "equipos": "teams", "partidos": "matches",
}

TIPOS_PANEL = {
    "division": "sel", "status": "sel", "kind": "sel", "category": "sel", "role": "sel",
    "network": "sel", "platform": "sel", "stage": "sel",
    "body": "textarea", "text": "textarea", "excerpt": "textarea", "description": "textarea",
    "closing": "textarea", "warning": "textarea", "summary": "textarea", "note": "textarea",
    "logo": "file", "avatar": "file", "banner": "file", "image": "file",
    "pinned": "bool", "available": "bool", "is_live": "bool", "is_active": "bool",
    "journey": "number", "sort_order": "number", "year": "number", "players": "number",
    "homeGoals": "number", "awayGoals": "number", "followers": "number",
    "viewer_count": "number", "amount": "number", "goal": "number", "raised": "number",
    "date": "date", "starts_at": "datetime-local", "time": "time",
    "home_score": "text", "away_score": "text",
}

ETIQUETAS_CAMPO = {
    "name": "Nombre", "label": "Título", "title": "Título", "division": "División",
    "stage": "Fase", "journey": "Jornada", "journeyLabel": "Nombre de la jornada",
    "date": "Fecha", "time": "Hora", "home": "Equipo local", "away": "Equipo visitante",
    "homeGoals": "Goles local", "awayGoals": "Goles visitante", "status": "Estado",
    "coach": "Director deportivo", "colors": "Colores (separados por comas)",
    "logo": "Logo del equipo", "note": "Nota", "sort_order": "Orden",
    "replay": "Enlace de repetición", "notes": "Notas", "mvp": "MVP",
    "keeperHome": "Portero local", "keeperAway": "Portero visitante",
    "url": "Enlace", "players": "Jugadores", "category": "Categoría", "kicker": "Subtítulo",
    "season": "Temporada", "text": "Texto", "team": "Equipo", "excerpt": "Entradilla",
    "body": "Cuerpo", "author": "Autor", "image": "Imagen", "pinned": "Fijado arriba",
    "cta": "Botón", "kind": "Tipo", "description": "Descripción", "href": "Enlace",
    "username": "Usuario", "role": "Puesto", "bio": "Biografía", "avatar": "Foto",
    "banner": "Banner", "focus": "Foco", "github": "GitHub", "instagram": "Instagram",
    "discord": "Discord", "available": "Disponible", "tags": "Etiquetas (separadas por comas)",
    "owner_name": "Responsable", "handle": "Usuario de la red", "network": "Red",
    "followers": "Seguidores", "is_streamer": "Es streamer", "league": "Competición",
    "channel": "Canal", "platform": "Plataforma", "viewer_count": "Espectadores",
    "starts_at": "Empieza", "is_live": "En vivo", "amount": "Importe", "method": "Método",
    "account": "Cuenta", "goal": "Meta", "raised": "Recaudado", "is_active": "Activo",
    "closing": "Cierre", "warning": "Aviso",
}

AJUSTES_PANEL = [
    {"clave": "leagueName", "etiqueta": "Nombre de la liga"},
    {"clave": "shortName", "etiqueta": "Siglas"},
    {"clave": "tagline", "etiqueta": "Lema", "tipo": "textarea"},
    {"clave": "description", "etiqueta": "Descripción", "tipo": "textarea"},
    {"clave": "season", "etiqueta": "Temporada"},
    {"clave": "seasonNumber", "etiqueta": "Número de temporada", "tipo": "number"},
    {"clave": "modality", "etiqueta": "Modalidad"},
    {"clave": "status", "etiqueta": "Estado de la liga"},
    {"clave": "statusNote", "etiqueta": "Nota de estado"},
    {"clave": "server", "etiqueta": "Servidor"},
    {"clave": "map", "etiqueta": "Mapa"},
    {"clave": "matchDuration", "etiqueta": "Duración del partido"},
    {"clave": "tolerance", "etiqueta": "Tolerancia"},
    {"clave": "pointsWin", "etiqueta": "Puntos por victoria", "tipo": "number"},
    {"clave": "pointsDraw", "etiqueta": "Puntos por empate", "tipo": "number"},
    {"clave": "founded", "etiqueta": "Año de fundación", "tipo": "number"},
    {"clave": "tiktok", "etiqueta": "TikTok de la liga"},
    {"clave": "tiktokHandle", "etiqueta": "Usuario de TikTok"},
    {"clave": "donationNote", "etiqueta": "Nota de donación", "tipo": "textarea"},
    {"clave": "donationKey", "etiqueta": "Clave de donación"},
    {"clave": "donationGoal", "etiqueta": "Meta de donación", "tipo": "number"},
]


def campos_panel(coleccion: str, valores: dict) -> list:
    definicion = COLECCIONES.get(coleccion) or {"campos": {}}
    salida = []
    for campo in CAMPOS_PANEL.get(coleccion, {}).get("campos", []):
        if campo not in definicion["campos"]:
            continue
        tipo = TIPOS_PANEL.get(campo, "text")
        entrada = {"clave": campo, "etiqueta": ETIQUETAS_CAMPO.get(campo, campo), "tipo": tipo}
        if tipo == "sel":
            entrada["opciones"] = definicion["campos"][campo][1]
        elif tipo == "file":
            entrada["valor"] = str(valores.get(campo) or "")
        else:
            valor = valores.get(campo)
            entrada["valor"] = "" if valor is None else valor
        salida.append(entrada)
    return salida


def datos_panel() -> dict:
    ajustes = leer_ajustes()
    divisiones = leer_divisiones()
    equipos = leer_coleccion("teams")
    partidos = leer_coleccion("matches")
    nombres = {d["id"]: d["name"] for d in divisiones}

    for partido in partidos:
        partido["division"] = partido.get("division") or ""
        partido["divisionName"] = nombres.get(partido.get("division"), "")
    for equipo in equipos:
        equipo["divisionName"] = nombres.get(equipo.get("division"), "")

    totales = totales_liga(ajustes, divisiones, equipos, partidos)
    proximo = proximo_partido(partidos, divisiones) or {}
    return {
        "settings": ajustes,
        "divisions": divisiones,
        "teams": equipos,
        "matches": partidos,
        "rules": leer_reglas(),
        "jugadores": leer_jugadores(),
        "eventos": leer_eventos(),
        "usuarios": [{clave: (str(v) if isinstance(v, (datetime, date)) else v)
                      for clave, v in u.items()}
                     for u in consultar(
                         "SELECT id, username, email, is_premium, is_admin, created_at,"
                         " last_login_at FROM `usuarios` ORDER BY created_at DESC")],
        "totales": totales,
        "proximo": {"home": proximo.get("home", ""), "away": proximo.get("away", ""),
                    "fecha": proximo.get("date", ""), "hora": proximo.get("time", "")},
        "campos": {c: campos_panel(c, {}) for c in CAMPOS_PANEL},
    }


def config_panel() -> dict:
    colecciones = {}
    for vista, coleccion in VISTA_COLECCION.items():
        if coleccion not in CAMPOS_PANEL:
            continue
        colecciones[coleccion] = {
            "principal": CAMPOS_PANEL[coleccion]["principal"],
            "etiquetas": CAMPOS_PANEL[coleccion]["etiquetas"],
            "lista": coleccion,
        }
    return {
        "csrf": csrf_token(),
        "posiciones": POSICIONES,
        "mapa": VISTA_COLECCION,
        "colecciones": colecciones,
        "especial": {},
        "ajustes": AJUSTES_PANEL,
    }


@app.get("/panel")
@requiere_admin
def panel():
    grupos = [
        ("Liga", [("resumen", "Resumen"), ("ajustes", "Ajustes"),
                 ("divisiones", "Divisiones"), ("equipos", "Equipos y jugadores"),
                 ("partidos", "Partidos e informes"), ("reglamento", "Reglamento")]),
        ("Salas y avisos", [("salas", "Salas públicas"), ("noticias", "Noticias"),
                            ("anuncios", "Anuncios"), ("premios", "Museo de premios"),
                            ("accesos", "Accesos")]),
        ("Comunidad", [("personal", "Equipo"), ("alianzas", "Alianzas"),
                      ("redes", "Redes sociales"), ("directos", "Live fútbol"),
                      ("donaciones", "Donaciones")]),
        ("Sistema", [("usuarios", "Usuarios")]),
    ]
    return render("panel.html", vista=request.args.get("v", "resumen"),
                  titulo_panel="Panel de administración", grupos_vistas=grupos,
                  datos_iniciales=json.dumps(datos_panel(), default=str, ensure_ascii=False),
                  config_panel=json.dumps(config_panel(), default=str, ensure_ascii=False))


# ==============================================================================
#  API DEL PANEL
# ==============================================================================

@app.get("/api/admin/data")
@requiere_admin
def api_datos():
    return jsonify(datos_panel())


@app.post("/api/admin/<coleccion>")
@requiere_admin
@requiere_csrf
def api_crear(coleccion: str):
    return jsonify(crear_registro(coleccion, cuerpo_archivos())), 201


@app.put("/api/admin/<coleccion>/<id_>")
@requiere_admin
@requiere_csrf
def api_actualizar(coleccion: str, id_: str):
    return jsonify(actualizar_registro(coleccion, id_, cuerpo_archivos()))


@app.delete("/api/admin/<coleccion>/<id_>")
@requiere_admin
@requiere_csrf
def api_borrar(coleccion: str, id_: str):
    if not borrar_registro(coleccion, id_):
        return jsonify({"error": "El registro no existe."}), 404
    return jsonify({"ok": True})


@app.put("/api/admin/jugadores/<team_id>")
@requiere_admin
@requiere_csrf
def api_jugadores(team_id: str):
    entrada = cuerpo()
    lista = entrada.get("jugadores") if isinstance(entrada.get("jugadores"), list) else []
    return jsonify({"jugadores": guardar_jugadores(team_id, lista)})


@app.put("/api/admin/eventos/<match_id>")
@requiere_admin
@requiere_csrf
def api_eventos(match_id: str):
    entrada = cuerpo()
    lista = entrada.get("eventos") if isinstance(entrada.get("eventos"), list) else []
    return jsonify({"eventos": guardar_eventos(match_id, lista)})


@app.put("/api/admin/ajustes")
@requiere_admin
@requiere_csrf
def api_ajustes():
    return jsonify(guardar_ajustes(cuerpo()))


@app.put("/api/admin/divisiones")
@requiere_admin
@requiere_csrf
def api_divisiones():
    entrada = cuerpo()
    lista = entrada if isinstance(entrada, list) else entrada.get("divisiones") or []
    return jsonify({"divisions": guardar_divisiones(lista)})


@app.put("/api/admin/reglas")
@requiere_admin
@requiere_csrf
def api_reglas():
    entrada = cuerpo()
    lista = entrada if isinstance(entrada, list) else entrada.get("rules") or []
    return jsonify({"rules": guardar_reglas(lista)})


# ==============================================================================
#  ARRANQUE
# ==============================================================================

def preparar():
    """Crea el esquema, carga el contenido inicial y marca la cookie de sesión."""
    # La conexión usa `g`, que exige un contexto de aplicación activo.
    with app.app_context():
        instalar_esquema()
        cargar_semilla()


if __name__ == "__main__":
    try:
        preparar()
    except pymysql.err.MySQLError as fallo:
        print("No se pudo conectar con MySQL:", fallo)
        raise SystemExit(1)
    print("The Diamonds League en http://localhost:%s" % APP_PUERTO)
    app.run(host=APP_HOST, port=APP_PUERTO, debug=APP_DEBUG)