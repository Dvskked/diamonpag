# The Diamonds League

Sitio público y panel de administración de **The Diamonds League**, la liga competitiva de HaxBall X5.
Reconstruido desde cero: interfaz moderna y responsive, renderizado en servidor, optimizado para
buscadores y con un backend propio para que el staff publique contenido sin tocar código.

---

## Puesta en marcha

```bash
npm install
npm start
```

Abre <http://localhost:3000>. El panel está en <http://localhost:3000/entrar>.

Durante el desarrollo, `npm run dev` reinicia el servidor solo al guardar.

### Accesos por defecto

| Usuario  | Contraseña       |
| -------- | ---------------- |
| `admin`  | `adminmascapito` |

**Cambíalos antes de publicar el sitio.** Copia `.env.example` a `.env` y define tus propias claves.

---

## Variables de entorno

| Variable          | Por defecto                              | Para qué sirve                                       |
| ----------------- | ---------------------------------------- | ---------------------------------------------------- |
| `PORT`            | `3000`                                   | Puerto del servidor.                                 |
| `SITE_URL`        | `http://localhost:3000`                  | URL canónica: Open Graph, sitemap y `robots.txt`.     |
| `DATA_FILE`       | `data/db.json`                           | Ruta de la base de datos.                            |
| `ADMIN_USER`      | `admin`                                  | Usuario del panel.                                   |
| `ADMIN_PASSWORD`  | `adminmascapito`                         | Contraseña del panel.                                |
| `SESSION_SECRET`  | valor de desarrollo                      | Firma las cookies de sesión. **Obligatorio cambiarlo.** |
| `COOKIE_SECURE`   | `false`                                  | `true` en producción (HTTPS).                        |
| `NODE_ENV`        | `development`                            | `production` activa avisos de configuración insegura. |

```bash
cp .env.example .env
```

---

## Estructura

```
src/
  server.js          Servidor Express, SSR, login, SEO y archivos estáticos
  config.js          Configuración y carga de .env
  db.js              Lectura y escritura atómica de data/db.json
  seed.js            Contenido inicial migrado del sitio anterior
  auth.js            Sesiones firmadas, credenciales y límite de intentos
  standings.js       Clasificación y próximo partido
  routes/admin.js    API del panel (CRUD + ajustes + reglas + competición)
  views/
    layout.js        Metadatos SEO, JSON-LD y shell HTML
    home.js          Página pública con los 8 módulos
    login.js         Formulario de acceso
    admin-page.js    Estructura del panel
    helpers.js       Utilidades de plantilla
public/
  css/site.css       Diseño público
  css/admin.css      Diseño del panel
  js/site.js         Pestañas, filtros, lightbox y menú (sin dependencias)
  js/admin.js        SPA CRUD del panel (sin dependencias)
  assets/            Logo, premios y fotos del staff
tests/               Suite de pruebas (ver abajo)
data/db.json         Base de datos (se crea sola, está en .gitignore)
```

Sin framework de front-end: solo Express en el servidor y JavaScript nativo en el navegador.

---

## Los 8 módulos

La navegación pública tiene exactamente estas secciones, en este orden:

1. **Competición** — formato, clasificación por división, fases y ascensos.
2. **Fechas** — calendario por jornadas con fecha, hora, estado y resultado.
3. **Reglas** — reglamento en cuatro secciones.
4. **Pubs** — salas de HaxBall enlazadas.
5. **Noticias** — tarjetas con acordeón de contenido completo.
6. **Anuncios** — comunicados de la liga.
7. **Importante** — accesos rápidos y estado de la liga.
8. **Equipos** — owner, master y staff con avatar y banner.

---

## El panel de administración

`/entrar` → introduce usuario y contraseña. Las sesiones duran 8 horas y se guardan en una
cookie `HttpOnly` firmada con HMAC-SHA256 (`tld_session`). Tras 8 intentos fallidos se bloquea
el acceso 10 minutos.

Doce vistas disponibles:

| Vista          | Qué manages                                                        |
| -------------- | ------------------------------------------------------------------ |
| Resumen        | Contadores, próxima jornada, estado de la liga y accesos directos. |
| Partidos       | Calendario completo y las dos clasificaciones en vivo.              |
| Equipos        | Los 14 equipos de D1 y D2.                                         |
| Competición    | Formato, fases, movimientos y reglas de cada división.             |
| Noticias       | Tarjetas de noticias y cuál sale como portada.                      |
| Anuncios       | Comunicados con fecha y badge.                                      |
| Premios        | Galería de premios, rankings y campeones.                           |
| Salas públicas | Links de HaxBall y su estado.                                      |
| Importante     | Accesos rápidos del inicio.                                        |
| Equipo         | Owner, master y staff.                                             |
| Reglas         | Secciones del reglamento en formato de texto.                      |
| Ajustes        | Nombre de la liga, temporada, mapa, puntos y configuración.        |

Las colecciones (Partidos, Equipos, Noticias, Anuncios, Premios, Salas, Importante, Equipo) se
guardan al instante. Reglas, Competición y Ajustes usan borradores: editas lo que quieras y
publicas con un botón, para no dejar la liga a medias.

### Añadir un campo nuevo

El panel se construye a partir de una sola tabla, así que un campo nuevo sale en la UI
automáticamente:

1. Añádelo a `fields` en el `sanitize` de la colección, dentro de `src/routes/admin.js`.
2. Añádelo a `fields` en la vista correspondiente de `public/js/admin.js`.
3. Añádelo a `FEATURES` en `src/views/home.js` para que se vea en el sitio público.

---

## Comandos

| Comando          | Qué hace                                                     |
| ---------------- | ------------------------------------------------------------ |
| `npm start`      | Arranca el servidor.                                          |
| `npm run dev`    | Arranca con recarga automática.                                |
| `npm run check`  | Comprueba la sintaxis de los 20 ficheros JavaScript.           |
| `npm test`       | Levanta un servidor de prueba y ejecuta 250 comprobaciones.   |

Las pruebas no tocan `data/db.json`: usan un directorio temporal. Cubren la API y la
persistencia, el renderizado de los 8 módulos en el navegador y el CRUD completo del panel
(alta de un partido con fecha y hora, edición de resultados y borrado).

---

## Despliegue

El sitio funciona en cualquier hosting Node. En Vercel:

```bash
vercel
```

Configura estas variables de entorno en el proyecto:

```
ADMIN_USER
ADMIN_PASSWORD
SESSION_SECRET
SITE_URL=https://tu-dominio.com
COOKIE_SECURE=true
```

### Aviso importante sobre los datos

`data/db.json` es un fichero en disco. **En Vercel (serverless) el disco es efímero**: cada
función se ejecuta en un contenedor limpio, así que los cambios del panel se perderán al
desplegar o al reiniciar la instancia.

Opciones, de menos a más trabajo:

- **Mantenerlo así** — vale para un panel de lectura, pruebas o un despliegue en un VPS propio
  (Railway, Render, Fly.io, un servidor con systemd). Es lo que hace el código ahora mismo.
- **Migrar a PostgreSQL** (Neon, Supabase) — cambia `src/db.js` y las consultas de
  `src/routes/admin.js`. El resto del proyecto no cambia.
- **Subir el JSON a un bucket** (Vercel Blob, S3) y leerlo/escribirlo en cada petición.

Mientras no migres, **no publiques en Vercel un panel desde el que dependa la liga**: perderías
los equipos, fechas y resultados que hayas cargado.

---

## Seguridad

- Contraseñas comparadas en tiempo constante (SHA-256 + `timingSafeEqual`).
- Cookies `HttpOnly`, `SameSite=Lax` y `Secure` en producción.
- Sesión firmada con HMAC-SHA256 y con caducidad; `SESSION_SECRET` aleatorio la hace
  imposible de falsificar.
- Límite de 8 intentos de acceso por IP cada 10 minutos.
- La API responde `401` en JSON cuando falta la sesión, nunca redirige.
- El servidor valida y recorta todos los campos antes de guardarlos, y rechaza ids con barras
  o rutas.
- Cabeceras HSTS, `X-Content-Type-Options`, `Referrer-Policy`, `X-Frame-Options` y
  `Permissions-Policy`.

---

## SEO

- Renderizado en servidor: el contenido está en el HTML, no se genera con JavaScript.
- Un solo `<h1>`, jerarquía de encabezados y HTML semántico (`<table>`, `<details>`, `<article>`).
- `title` y `description` únicos, etiqueta canónica, Open Graph y Twitter Cards.
- JSON-LD con `SportsOrganization`, `WebSite`, `ItemList` y `FAQPage`.
- `robots.txt`, `sitemap.xml` y `manifest.webmanifest` generados en cada petición.
- Imágenes locales con `alt`, `width`/`height` y `loading="lazy"`.
- Alternativa sin JavaScript: sin él se muestran todas las secciones en vez de solo la primera.

---

## Contenido heredado

`src/seed.js` conserva la información del sitio anterior. Dos cosas que conviene revisar desde
el panel antes de abrir la liga:

- **División 2** solo tiene los 2 equipos que se conocían (`DEPORTIVO PEREIRA` y `KIOSKO FC`).
  El resto del roster se completa en Equipos.
- Los **4 partidos de playoffs** están como plantilla, sin equipos ni fecha. Se editan en Partidos.

`src/routes/admin.js` tiene un endpoint `POST /api/admin/reset` que devuelve la base a su
contenido inicial. Solo está disponible desde el panel.
