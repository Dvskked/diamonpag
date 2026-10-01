# The Diamonds League

Sitio público y panel de administración de **The Diamonds League**, la liga competitiva de HaxBall X5.
PHP 8 + MySQL/MariaDB, renderizado en servidor, optimizado para buscadores y con un backend propio
para que el staff publique contenido sin tocar código.

> La versión anterior en Node/Express con `data/db.json` quedó aislada en [`legacy-node/`](legacy-node)
> solo como referencia histórica y de diseño. **npm ya no es necesario**: el sitio activo es PHP.

---

## Requisitos

| Pieza      | Versión mínima                       |
| ---------- | ------------------------------------ |
| PHP        | 8.1 (probado en 8.3)                 |
| MySQL      | 5.7 / 8.0, o MariaDB 10.4+          |
| Servidor   | Apache con `mod_rewrite` o Nginx     |
| Extensiones | `pdo_mysql`, `mbstring`, `json`      |

---

## Puesta en marcha

### 1. Base de datos

```bash
mysql -u root -p -e "CREATE DATABASE diamonds_league CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u root -p diamonds_league < sql/esquema.sql
mysql -u root -p diamonds_league < sql/datos.sql
```

- `sql/esquema.sql` crea todas las tablas (liga, cuentas, consentimientos, intentos de acceso).
- `sql/datos.sql` carga el contenido migrado: ajustes, divisiones, equipos, partidos, reglas,
  noticias, anuncios, premios, salas, accesos, staff, alianzas, redes, directos y donaciones.

### 2. Configuración

```bash
cp .env.example .env
```

Edita `.env` con tus credenciales. Como mínimo son obligatorias `DB_NAME`, `DB_USER` y
`DB_PASSWORD`; también conviene `SITE_URL`, `ADMIN_USER` y `ADMIN_PASSWORD`.

Genera un secreto de sesión con:

```bash
php -r "echo bin2hex(random_bytes(48)), PHP_EOL;"
```

### 3. Servidor

En local:

```bash
php -S localhost:8000
```

Abre <http://localhost:8000>. El panel del staff está en <http://localhost:8000/entrar>.

En Apache, el `.htaccess` incluido ya reescribe todo a `index.php` y sirve `css/`, `js/` y
`assets/` directamente. En Nginx usa `try_files $uri /index.php$is_args$args;`.

### 4. Primer acceso

Entra en `/entrar` con `ADMIN_USER` y `ADMIN_PASSWORD` de tu `.env` y **cámbialos al entrar**.

---

## Variables de entorno

Todas son opcionales: si faltan, se usa el valor por defecto de `config.php`.

| Variable             | Por defecto                 | Para qué sirve                                          |
| -------------------- | --------------------------- | ------------------------------------------------------- |
| `APP_NAME`           | `The Diamonds League`       | Nombre en `<title>` y metadatos.                        |
| `APP_TIMEZONE`       | `America/Bogota`            | Zona horaria de las fechas.                             |
| `APP_DEBUG`          | `0`                         | `1` muestra los errores. **Nunca en producción.**       |
| `DB_HOST`            | `127.0.0.1`                 | Host de MySQL/MariaDB.                                  |
| `DB_PORT`            | `3306`                      | Puerto de la base de datos.                             |
| `DB_NAME`            | `diamonds_league`           | Nombre de la base de datos.                             |
| `DB_USER`            | `root`                      | Usuario de MySQL/MariaDB.                               |
| `DB_PASSWORD`        | vacío                       | Contraseña de MySQL/MariaDB.                            |
| `DB_CHARSET`         | `utf8mb4`                   | Charset de la conexión PDO.                             |
| `SITE_URL`           | `http://localhost:8000`     | URL canónica: Open Graph, `sitemap.xml` y `robots.txt`. |
| `SESSION_NAME`       | `tld_sesion`                | Nombre de la cookie de sesión.                          |
| `SESSION_HOURS`      | `8`                          | Duración de la sesión.                                  |
| `SESSION_SECURE`     | auto                        | `1` fuerza cookie solo por HTTPS.                       |
| `ADMIN_USER`         | `admin`                     | Usuario del panel.                                      |
| `ADMIN_PASSWORD`     | vacío                       | Contraseña del panel.                                   |
| `LOGIN_MAX_ATTEMPTS` | `8`                          | Intentos antes de bloquear.                             |
| `LOGIN_LOCK_MINUTES` | `10`                         | Minutos de bloqueo tras fallar.                         |
| `POLICY_VERSION`     | `1.0`                       | Versión del documento legal.                            |
| `POLICY_DATE`        | `2026-09-30`                | Fecha de la última revisión de privacidad.              |
| `POLICY_CONTACT`     | `admin@diamondsleague.app`  | Contacto para consultas de datos.                       |
| `POLICY_OWNER`       | `The Diamonds League`       | Responsable del tratamiento.                            |
| `GOOGLE_CLIENT_ID`   | vacío                       | Google OAuth. **Vacío = desactivar.**                   |
| `GOOGLE_CLIENT_SECRET` | vacío                     | Google OAuth.                                           |
| `GOOGLE_REDIRECT`    | `{SITE_URL}/cuenta/google/callback` | Callback de OAuth.                             |

---

## Estructura

```
index.php              Front controller: rutas públicas, cuentas, panel y API
config.php             Constantes, carga de .env y política de datos
conexion.php           Conexión PDO (sin emular prepares)
api/router.php         API JSON del panel
includes/
  helpers.php          Escape, fechas, URL segura, JSON y respuestas
  bd.php               Colecciones, saneado, CRUD, reglas y clasificaciones
  auth.php             Sesiones, CSRF, admin, usuarios, premium y rate limit
  google.php           OAuth 2.0 de Google (opcional)
  layout.php           Layout público, SEO, JSON-LD, cabecera de 12 entradas y pie
views/
  inicio.php           Portada con las 11 secciones + la tuerca
  cuenta.php           Registro, acceso, perfil, contraseña, datos y borrado
  acceso.php           Acceso del staff
  panel.php            Shell del panel de administración
  privacidad.php       Política de privacidad
  informacion.php      404, 500 y sitemap.xml
css/site.css           Diseño público
css/admin.css          Diseño del panel
js/site.js             Pestañas, filtros, lightbox, ficha y menú (sin dependencias)
js/admin.js            SPA CRUD del panel (sin dependencias)
assets/                Logo, premios y fotos del staff
sql/esquema.sql        Esquema de MySQL/MariaDB
sql/datos.sql          Contenido inicial migrado
legacy-node/           Versión anterior en Node (solo referencia, no se despliega)
```

Sin framework de front-end: PHP en el servidor y JavaScript nativo en el navegador.

---

## Las 12 entradas de la cabecera

La navegación pública tiene exactamente estas entradas, en este orden:

| # | Entrada                          | Ancla      | Contenido                                        |
| - | -------------------------------- | ---------- | ------------------------------------------------ |
| 1 | `LIGA`                           | `#liga`    | Reglamento, formato, D1 y D2, equipos y accesos. |
| 2 | `FECHAS`                         | `#fechas`  | Calendario por jornadas, horarios y resultados.   |
| 3 | `PUBS`                           | `#pubs`    | Salas de HaxBall con aviso en rojo si no abren.  |
| 4 | `MUSEO`                          | `#museo`   | Premios entregados, rankings y campeones.         |
| 5 | `NOTICIAS`                       | `#noticias`| Reportajes y noticias de la liga.                 |
| 6 | `ANUNCIOS - NOVEDADES`           | `#anuncios`| Comunicados y novedades.                         |
| 7 | `ALIANZAS`                       | `#alianzas`| Afiliaciones, partners y servidores.              |
| 8 | `REDES SOCIALES`                 | `#redes`   | Cuentas de la liga y de los streamers.           |
| 9 | `EQUIPO ADMINISTRACION`          | `#equipo`  | Owner, desarrollador, master y staff.             |
| 10| `TUERCA DE CONFIGURACION`        | `#tuerca`  | Acceso, cuenta, contraseña, premium, admin y privacidad. |
| 11| `LIVE FUTBOL`                    | `#live`    | Directos tipo Kick o Twitch.                     |
| 12| `DONACION`                       | `#donacion`| Métodos de pago, claves y objetivo de la meta.   |

En la píldora del menú se ve la forma corta (`ANUNCIOS`, `EQUIPO`, `LIVE`, `DONACIÓN`) y el nombre
completo está en el `title`, en el `aria-label`, en la marquesina del hero y en el mapa de módulos.

### El inicio

- **Hero cinematográfico** con el escudo sobre tres órbitas luminosas, esquinas y destellos.
- **Barra de datos** con cinco métricas y contador animado al entrar en pantalla.
- **Tarjetas de resumen** con el próximo partido y la cabeza de tabla de D1.
- **Marquesina** con los nombres de las 12 entradas, **barra de progreso** de lectura y
  **botón de volver arriba**.
- **Aparición progresiva** de tarjetas al hacer scroll, respetando `prefers-reduced-motion`.

---

## Cuentas de usuario

La tuerca de configuración da acceso a las cuentas, independientes del acceso del staff:

| Ruta                  | Qué hace                                                    |
| --------------------- | ----------------------------------------------------------- |
| `/registro`           | Alta con usuario, correo, contraseña y aceptación de datos.  |
| `/cuenta`             | Acceso con usuario o correo.                                |
| `/cuenta/google`      | Acceso con Google (si hay credenciales OAuth configuradas).  |
| `/cuenta/perfil`      | Editar perfil, cambiar correo, bio, foto y equipo favorito.  |
| `/cuenta/password`    | Cambiar la contraseña.                                       |
| `/cuenta/premium`     | Activar o desactivar el modo premium.                        |
| `/cuenta/datos`       | Ver y descargar todos los datos en JSON.                    |
| `/cuenta/eliminar`    | Borrado definitivo de la cuenta y sus consentimientos.       |
| `/privacidad`         | Política de privacidad y protección de datos.                |

Las contraseñas se guardan con `password_hash()` (bcrypt) y nunca se muestran. El borrado es real:
elimina perfil, contraseña, vinculación con Google y consentimientos de la base de datos.

---

## El panel de administración

`/entrar` → usuario y contraseña del staff. La sesión de administración es **independiente** de la
de los usuarios. Tras `LOGIN_MAX_ATTEMPTS` intentos fallidos se bloquea `LOGIN_LOCK_MINUTES` minutos.

| Vista          | Qué manages                                                        |
| -------------- | ------------------------------------------------------------------ |
| Resumen        | Contadores, próxima jornada, estado de la liga y accesos directos. |
| Ajustes        | Nombre de la liga, temporada, estado, mapa, puntos y donación.     |
| Divisiones     | Formato, fases, movimientos y reglas de cada división.             |
| Equipos        | Los equipos inscritos y sus colores.                               |
| Partidos       | Calendario completo y las dos clasificaciones en vivo.              |
| Reglamento     | Secciones del reglamento en formato estructurado.                  |
| Salas públicas | Links de HaxBall y su estado.                                      |
| Noticias       | Tarjetas de noticias, portada y contenido.                         |
| Anuncios       | Comunicados con fecha, badge y listas.                              |
| Museo de premios| Premios, rankings y campeones.                                    |
| Accesos        | Accesos rápidos del inicio.                                        |
| Equipo         | Owner, desarrollador, master y staff, con sus redes sociales.       |
| Alianzas       | Afiliaciones, partners y servidores.                               |
| Redes sociales | Cuentas de la liga y de los streamers.                             |
| Live fútbol    | Directos, marcador, canal y espectadores.                          |
| Donaciones     | Métodos de pago, claves y objetivo de la meta.                      |

Las colecciones se guardan al instante; Ajustes, Reglamento y Divisiones usan borradores con botón
de publicar. Todas las escrituras pasan por token CSRF (`X-CSRF-Token`) y exigen sesión de
administración.

`POST /api/admin/reset` con `{"confirm":"RESTABLECER"}` devuelve la base al contenido de
`sql/datos.sql`. Destructive: úsalo solo si sabes lo que haces.

### Contrato de la API

```
GET    /api/admin/session
POST   /api/admin/login | /api/admin/logout | /api/admin/reset
GET    /api/admin/data | /api/admin/standings
GET    /api/admin/{coleccion}
POST   /api/admin/{coleccion}
PUT    /api/admin/{coleccion}/{id}
DELETE /api/admin/{coleccion}/{id}
PUT    /api/admin/settings | /match-config | /rules | /divisions
```

---

## Añadir un campo nuevo

1. Añádelo a la definición de la colección en `includes/bd.php`.
2. Añádelo a `sql/esquema.sql` con su `ALTER TABLE` correspondiente.
3. Añádelo a los `fields` de la vista en `js/admin.js`.
4. Añádelo a la sección pública en `views/inicio.php`.

---

## Comprobaciones

```bash
# Lint de todo el PHP
for f in index.php config.php conexion.php includes/*.php views/*.php api/*.php; do php -l "$f"; done

# Sintaxis del JavaScript
node --check js/site.js && node --check js/admin.js
```

La suite de pruebas de la versión Node sigue en `legacy-node/tests/` y se ejecuta con `npm test`
desde `legacy-node/`. No es requisito para desplegar el sitio PHP.

---

## Despliegue

1. Sube el proyecto a un hosting con PHP 8 y MySQL/MariaDB.
2. Importa `sql/esquema.sql` y `sql/datos.sql`.
3. Copia `.env.example` a `.env` y ajusta las credenciales y `SITE_URL`.
4. Pon `SESSION_SECURE=1` y `APP_DEBUG=0`.
5. En Apache, el `.htaccess` incluido se encarga; en Nginx añade el `try_files`.
6. Entra en `/entrar` y cambia la contraseña de administración.

A diferencia de la versión Node, aquí los datos viven en la base de datos, así que el sitio
funciona igual en un VPS o en un hosting de PHP tradicional.

---

## Autoría

Proyecto desarrollado por **neptun · andres · [Dvskked](https://github.com/Dvskked)**.

- GitHub: [@Dvskked](https://github.com/Dvskked)
- Instagram: [@_andres.nox](https://instagram.com/_andres.nox)
- Discord: `andresneptunzinho`
- Disponible para desarrollo de software web, sitios y aplicaciones a medida.

Cada fichero del proyecto lleva una cabecera de marca de agua con esta firma. Si reutilizas el
código, conserva ese aviso.

---

## Seguridad

- Contraseñas de usuarios con `password_hash()`/`password_verify()` (bcrypt).
- Acceso de administración separado, con comparación en tiempo constante.
- Cookies `HttpOnly`, `SameSite=Lax` y `Secure` con `SESSION_SECURE=1`.
- Token anti-CSRF en **todos** los formularios y en toda escritura de la API.
- Consultas preparadas con `PDO::ATTR_EMULATE_PREPARES => false` en toda la aplicación.
- Límite de intentos de acceso por usuario y registro de IP para el bloqueo.
- Saneado de toda entrada: recorte de longitudes, validación de URL y de rutas de imagen.
- `.env`, `*.sql` y `legacy-node/data/` bloqueados por `.htaccess` y por `.gitignore`.
- Cabeceras `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` y `Permissions-Policy`.
- `/panel` y `/api/` con `noindex` y excluidos de `robots.txt`.

---

## SEO

- Renderizado en servidor: el contenido está en el HTML, no se genera con JavaScript.
- Un solo `<h1>`, jerarquía de encabezados y HTML semántico (`<table>`, `<details>`, `<article>`).
- `title` y `description` únicos, etiqueta canónica, Open Graph y Twitter Cards.
- JSON-LD con `SportsOrganization`, `WebSite` y `FAQPage`.
- `robots.txt` y `sitemap.xml` generados en cada petición.
- Imágenes locales con `alt`, `width`/`height` y `loading="lazy"`.

---

## Contenido heredado

`sql/datos.sql` conserva la información del sitio anterior. Dos cosas que conviene revisar desde
el panel antes de abrir la liga:

- **División 2** solo tiene los 2 equipos que se conocían (`DEPORTIVO PEREIRA` y `KIOSKO FC`).
  El resto del roster se completa en Equipos.
- Los **4 partidos de playoffs** están como plantilla, sin equipos ni fecha. Se editan en Partidos.

---

## Revisión legal pendiente

`views/privacidad.php` es una plantilla redactada para la liga. Antes de abrir al público conviene
que el responsable del tratamiento la revise y la adapte a su jurisdicción, y que verifique el
plazo real de conservación de IP y consentimientos.
