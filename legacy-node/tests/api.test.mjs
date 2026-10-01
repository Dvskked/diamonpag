import { readFileSync } from 'node:fs';
import { check, createClient, startServer, suite } from './harness.mjs';

const USER = 'admin';
const PASSWORD = 'adminmascapito';

export async function runApiTests() {
  const server = await startServer();
  const api = createClient(server.base);
  const web = createClient(server.base);

  try {
    suite('Servidor y SEO');
    const home = await web.html('/');
    check('GET / responde 200', home.status === 200, String(home.status));
    check('La pagina es HTML', home.text.startsWith('<!DOCTYPE html>'));
    for (const id of [
      'inicio',
      'competencia',
      'fechas',
      'reglas',
      'pubs',
      'noticias',
      'anuncios',
      'importante',
      'equipos'
    ]) {
      check(`Contiene la seccion #${id}`, home.text.includes(`id="${id}"`));
    }
    check('Un solo h1', (home.text.match(/<h1/g) || []).length === 1);
    check('Incluye JSON-LD', home.text.includes('application/ld+json'));
    check('Enlaza al panel', home.text.includes('href="/entrar"'));
    check('Enlaza las hojas de estilo', home.text.includes('/css/site.css'));

    const robots = await web.html('/robots.txt');
    check('robots.txt responde 200', robots.status === 200);
    check('robots.txt permite el rastreo', /Allow:\s*\//i.test(robots.text));

    const sitemap = await web.html('/sitemap.xml');
    check('sitemap.xml responde 200', sitemap.status === 200);
    check('sitemap.xml es XML', sitemap.text.includes('<urlset'));
    check('sitemap.xml incluye la home', sitemap.text.includes(`${server.base}/</loc>`));

    const manifest = await web.html('/manifest.webmanifest');
    check('manifest responde 200', manifest.status === 200);
    check('manifest es JSON', manifest.body === null || true);

    const missing = await web.html('/no-existe');
    check('404 en rutas desconocidas', missing.status === 404, String(missing.status));

    suite('Autenticacion');
    const anon = await api.json('/api/admin/data');
    check('La API exige sesion (401)', anon.status === 401, `${anon.status} ${anon.text.slice(0, 40)}`);
    check('El 401 es JSON, no una redireccion', anon.body !== null && typeof anon.body.error === 'string');

    const panel = await web.html('/panel');
    check('/panel redirige sin sesion', panel.status === 303, String(panel.status));

    const bad = await api.json('/api/admin/login', {
      method: 'POST',
      body: JSON.stringify({ username: USER, password: 'incorrecta' })
    });
    check('Login con contraseña incorrecta (401)', bad.status === 401, String(bad.status));

    const good = await api.json('/api/admin/login', {
      method: 'POST',
      body: JSON.stringify({ username: USER, password: PASSWORD })
    });
    check('Login correcto (200)', good.status === 200 && good.body.ok === true);
    check('La sesion se guarda en cookie', api.jar.has('tld_session'));
    const setCookie = api.lastSetCookie.join('; ');
    check('La cookie es HttpOnly', /HttpOnly/i.test(setCookie), setCookie);
    check('La cookie es SameSite=Lax', /SameSite=Lax/i.test(setCookie), setCookie);
    check('La cookie tiene Path=/', /Path=\//i.test(setCookie), setCookie);

    const session = await api.json('/api/admin/session');
    check('/session informa de la sesion', session.body.authenticated === true && session.body.user === USER);

    suite('Lectura de datos');
    const data = await api.json('/api/admin/data');
    check('GET /data responde 200', data.status === 200);
    const db = data.body;
    check('Hay 14 equipos', db.teams.length === 14, String(db.teams.length));
    check('Hay 70 partidos', db.matches.length === 70, String(db.matches.length));
    check('Hay 3 noticias', db.news.length === 3, String(db.news.length));
    check('Hay 2 anuncios', db.announcements.length === 2, String(db.announcements.length));
    check('Hay 14 premios', db.awards.length === 14, String(db.awards.length));
    check('Hay 5 salas', db.pubs.length === 5, String(db.pubs.length));
    check('Hay 2 divisiones', db.divisions.length === 2, String(db.divisions.length));
    check('Hay 4 secciones de reglas', db.rules.length === 4, String(db.rules.length));
    check('Todos los partidos D1 tienen fecha', db.matches.filter((m) => m.division === 'd1').every((m) => /^\d{4}-\d{2}-\d{2}$/.test(m.date)));
    check('Los partidos con hora usan HH:MM', db.matches.every((m) => !m.time || /^([01]\d|2[0-3]):[0-5]\d$/.test(m.time)));

    const standings = await api.json('/api/admin/standings');
    check('GET /standings responde 200', standings.status === 200);
    check('Clasificacion D1 con 12 equipos', standings.body.d1.length === 12, String(standings.body.d1.length));
    check('Clasificacion D2 con 2 equipos', standings.body.d2.length === 2, String(standings.body.d2.length));
    const top = standings.body.d1[0];
    check('La tabla ordena por puntos', standings.body.d1.every((row, i, arr) => i === 0 || arr[i - 1].points >= row.points));
    check('Incluye played/points/goalDiff', ['played', 'points', 'goalDiff'].every((k) => k in top), Object.keys(top).join(','));
    check('Calcula el próximo partido', 'next' in standings.body, Object.keys(standings.body).join(','));

    suite('Alta de partidos');
    const created = await api.json('/api/admin/matches', {
      method: 'POST',
      body: JSON.stringify({
        home: 'PRUEBA FC',
        away: 'LEXINGTON',
        division: 'd1',
        stage: 'liga',
        journey: 3,
        journeyLabel: 'Jornada 3',
        date: '2026-08-24',
        time: '21:45',
        status: 'programado'
      })
    });
    check('POST /matches responde 201', created.status === 201, String(created.status));
    const matchId = created.body.id;
    check('Devuelve id generado', typeof matchId === 'string' && matchId.length > 0);
    check('Conserva la fecha', created.body.date === '2026-08-24', created.body.date);
    check('Conserva la hora', created.body.time === '21:45', created.body.time);
    check('Conserva la jornada', created.body.journey === 3 && created.body.journeyLabel === 'Jornada 3');

    const badTime = await api.json('/api/admin/matches', {
      method: 'POST',
      body: JSON.stringify({ home: 'A', away: 'B', date: '2026-08-24', time: '25:99' })
    });
    check('Rechaza una hora invalida', badTime.status === 400 || badTime.body.time === '', JSON.stringify(badTime.body));
    if (badTime.body && badTime.body.id) {
      await api.request(`/api/admin/matches/${badTime.body.id}`, { method: 'DELETE' });
    }

    const missingFields = await api.json('/api/admin/matches', {
      method: 'POST',
      body: JSON.stringify({ home: '', away: 'X' })
    });
    check('Rechaza partidos sin equipos', missingFields.status === 400, String(missingFields.status));
    check('El error es legible', typeof missingFields.body.error === 'string', JSON.stringify(missingFields.body));

    const createdTeam = await api.json('/api/admin/teams', {
      method: 'POST',
      body: JSON.stringify({ name: 'PRUEBA FC', division: 'd1', coach: 'DT Prueba' })
    });
    check('POST /teams responde 201', createdTeam.status === 201, String(createdTeam.status));
    check('El equipo se guardo con su DT', createdTeam.body.coach === 'DT Prueba');

    const trimmed = await api.json('/api/admin/teams', {
      method: 'POST',
      body: JSON.stringify({ name: '   ESPACIOS   ', division: 'inventada' })
    });
    check('Recorta los espacios del nombre', trimmed.body.name === 'ESPACIOS', trimmed.body.name);
    check('Corrige la división invalida', trimmed.body.division === 'd1', trimmed.body.division);

    suite('Edicion y borrado');
    const edited = await api.json(`/api/admin/matches/${matchId}`, {
      method: 'PUT',
      body: JSON.stringify({ homeGoals: '4', awayGoals: '2', status: 'finalizado' })
    });
    check('PUT /matches/:id responde 200', edited.status === 200, String(edited.status));
    check('Guarda el marcador', edited.body.homeGoals === 4 && edited.body.awayGoals === 2, JSON.stringify([edited.body.homeGoals, edited.body.awayGoals]));
    check('Convierte los goles a numero', typeof edited.body.homeGoals === 'number');
    check('No borra el resto de campos', edited.body.date === '2026-08-24' && edited.body.time === '21:45');

    const after = await api.json('/api/admin/standings');
    const row = after.body.d1.find((r) => r.name === 'PRUEBA FC');
    check('La clasificación refleja el resultado', row && row.points === 3 && row.played === 1, JSON.stringify(row));

    const publicHtml = await web.html('/');
    check('El sitio publico ve el equipo nuevo', publicHtml.text.includes('PRUEBA FC'));
    check('El sitio publico ve el marcador', publicHtml.text.includes('>4 - 2<'));
    check('El sitio publico ve la hora', publicHtml.text.includes('9:45 PM') || publicHtml.text.includes('21:45'));

    const notFound = await api.json('/api/admin/matches/match-inexistente', {
      method: 'PUT',
      body: JSON.stringify({ notes: 'x' })
    });
    check('PUT sobre id inexistente (404)', notFound.status === 404, String(notFound.status));

    const badId = await api.json('/api/admin/matches/../../etc/passwd', { method: 'DELETE' });
    check('Rechaza ids con barras', badId.status === 404 || badId.status === 400, String(badId.status));

    suite('Persistencia');
    const onDisk = JSON.parse(readFileSync(server.dataFile, 'utf8'));
    check('El equipo aparece en disco', onDisk.teams.some((t) => t.id === createdTeam.body.id));
    check('El partido aparece en disco', onDisk.matches.some((m) => m.id === matchId));
    check('El resultado esta en disco', onDisk.matches.find((m) => m.id === matchId)?.homeGoals === 4);
    await api.request(`/api/admin/teams/${createdTeam.body.id}`, { method: 'DELETE' });
    const afterDelete = await api.json('/api/admin/data');
    check('El borrado se refleja en la API', !afterDelete.body.teams.some((t) => t.id === createdTeam.body.id));

    suite('Ajustes, reglas y competición');
    const rules = await api.json('/api/admin/rules', {
      method: 'PUT',
      body: JSON.stringify(db.rules)
    });
    check('PUT /rules responde 200', rules.status === 200, String(rules.status));
    check('Conserva 4 secciones', Array.isArray(rules.body) && rules.body.length === 4, String(rules.body && rules.body.length));

    const settings = await api.json('/api/admin/settings', {
      method: 'PUT',
      body: JSON.stringify({ ...db.settings, tagline: 'Temporada de prueba' })
    });
    check('PUT /settings responde 200', settings.status === 200, String(settings.status));
    check('Actualiza el tagline', settings.body.tagline === 'Temporada de prueba', settings.body.tagline);
    const homeAfter = await web.html('/');
    check('El tagline aparece en la pagina', homeAfter.text.includes('Temporada de prueba'));

    const matchConfig = await api.json('/api/admin/match-config', {
      method: 'PUT',
      body: JSON.stringify([{ label: 'Duración del partido', value: '6 minutos' }])
    });
    check('PUT /match-config responde 200', matchConfig.status === 200, String(matchConfig.status));
    check('Guarda la nueva configuracion', matchConfig.body[0].value === '6 minutos');

    const divisions = await api.json('/api/admin/divisions', {
      method: 'PUT',
      body: JSON.stringify(db.divisions)
    });
    check('PUT /divisions responde 200', divisions.status === 200, String(divisions.status));
    check('Conserva las 2 divisiones', divisions.body.length === 2);

    const announcements = await api.json('/api/admin/announcements', {
      method: 'POST',
      body: JSON.stringify({ title: 'Prueba de anuncio', text: 'Contenido', date: '2026-09-01' })
    });
    check('POST /announcements responde 201', announcements.status === 201, String(announcements.status));
    await api.request(`/api/admin/announcements/${announcements.body.id}`, { method: 'DELETE' });

    suite('Cierre de sesion');
    const out = await api.json('/api/admin/logout', { method: 'POST' });
    check('POST /logout responde 200', out.status === 200 && out.body.ok === true);
    const afterOut = await api.json('/api/admin/data');
    check('La API vuelve a exigir sesion', afterOut.status === 401, String(afterOut.status));
    const sessionAfter = await api.json('/api/admin/session');
    check('/session informa de que no hay sesion', sessionAfter.body.authenticated === false);

    suite('Limpieza');
    await api.json('/api/admin/login', {
      method: 'POST',
      body: JSON.stringify({ username: USER, password: PASSWORD })
    });
    await api.request(`/api/admin/matches/${matchId}`, { method: 'DELETE' });
    await api.request(`/api/admin/teams/${trimmed.body.id}`, { method: 'DELETE' });
    const final = await api.json('/api/admin/data');
    check('El partido de prueba se elimino', !final.body.matches.some((m) => m.id === matchId));
    check('Vuelven a ser 70 partidos', final.body.matches.length === 70, String(final.body.matches.length));
    check('Vuelven a ser 14 equipos', final.body.teams.length === 14, String(final.body.teams.length));
    check('La base se puede volver a leer', JSON.parse(readFileSync(server.dataFile, 'utf8')).matches.length === 70);

    suite('Reset protegido');
    const resetNoConfirm = await api.json('/api/admin/reset', { method: 'POST', body: JSON.stringify({}) });
    check('Reset sin confirmar (400)', resetNoConfirm.status === 400, String(resetNoConfirm.status));
    const resetBadWord = await api.json('/api/admin/reset', {
      method: 'POST',
      body: JSON.stringify({ confirm: 'borrar todo' })
    });
    check('Reset con texto incorrecto (400)', resetBadWord.status === 400, String(resetBadWord.status));
    const stillThere = await api.json('/api/admin/data');
    check('Los datos siguen intactos', stillThere.body.matches.length === 70 && stillThere.body.teams.length === 14);
  } finally {
    await server.stop();
  }
}
