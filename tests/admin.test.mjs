import { readFileSync } from 'node:fs';
import path from 'node:path';
import {
  check,
  createClient,
  exposeDomGlobals,
  loadBrowserModule,
  loadDom,
  rootDir,
  startServer,
  suite
} from './harness.mjs';

const adminJs = readFileSync(path.join(rootDir, 'public', 'js', 'admin.js'), 'utf8');

const VIEWS = {
  matches: 70,
  teams: 14,
  divisions: 2,
  news: 3,
  announcements: 2,
  awards: 14,
  pubs: 5,
  important: 8,
  staff: 5,
  rules: 4,
  settings: 2
};

export async function runAdminTests() {
  const server = await startServer();
  const client = createClient(server.base);

  try {
    // Sesion real para poder renderizar /panel
    await client.json('/api/admin/login', {
      method: 'POST',
      body: JSON.stringify({ username: 'admin', password: 'adminmascapito' })
    });
    const panelHtml = (await client.html('/panel')).text;
    const data = (await client.json('/api/admin/data')).body;

    const { window, document } = await loadDom(panelHtml, `${server.base}/panel`);

    const calls = [];
    let seeded = JSON.parse(JSON.stringify(data));

    window.fetch = async (url, opts = {}) => {
      const apiPath = String(url).replace('/api/admin', '');
      const collection = apiPath.replace(/^\//, '');
      const method = opts.method || 'GET';
      calls.push(`${method} ${apiPath}`);
      if (apiPath === '/data') {
        return { ok: true, status: 200, json: async () => JSON.parse(JSON.stringify(seeded)) };
      }
      if (apiPath === '/standings') {
        const { computeStandings, nextMatch } = await import('../src/standings.js');
        const out = {};
        for (const id of ['d1', 'd2']) {
          out[id] = computeStandings({
            teams: seeded.teams,
            matches: seeded.matches,
            divisionId: id,
            settings: seeded.settings
          });
          out[id].next = nextMatch(seeded.matches, seeded.divisions);
        }
        return { ok: true, status: 200, json: async () => out };
      }
      if (method === 'POST') {
        const item = { ...JSON.parse(opts.body), id: `test-${collection}-${seeded[collection].length}` };
        seeded[collection].push(item);
        return { ok: true, status: 201, json: async () => item };
      }
      if (method === 'PUT' && apiPath.includes('/')) {
        const [, coll, id] = apiPath.split('/');
        const target = seeded[coll].find((x) => x.id === id);
        if (!target) return { ok: false, status: 404, json: async () => ({ error: 'No existe' }) };
        Object.assign(target, JSON.parse(opts.body));
        return { ok: true, status: 200, json: async () => target };
      }
      if (method === 'DELETE') {
        const [, coll, id] = apiPath.split('/');
        seeded[coll] = seeded[coll].filter((x) => x.id !== id);
        return { ok: true, status: 200, json: async () => ({ ok: true }) };
      }
      return { ok: true, status: 200, json: async () => ({}) };
    };
    exposeDomGlobals(window);
    globalThis.fetch = window.fetch;

    const mod = await loadBrowserModule(adminJs, {
      exports: ['go', 'refresh', 'VIEWS', 'BLOCK_FORMS', 'linesToArray', 'splitParts']
    });

    const body = document.querySelector('[data-view-body]');
    const title = document.querySelector('[data-view-title]');
    const click = (node) =>
      node.dispatchEvent(new window.MouseEvent('click', { bubbles: true, cancelable: true }));
    const wait = (ms = 60) => new Promise((r) => setTimeout(r, ms));

    suite('Carga inicial del panel');
    await mod.refresh();
    check('Pide los datos al arrancar', calls.includes('GET /data'));
    check('Abre en Resumen', title.textContent === 'Resumen', title.textContent);
    check('Muestra tarjetas de resumen', body.querySelectorAll('.app-card').length > 0);
    check('Muestra accesos rapidos', body.querySelectorAll('.app-stat').length > 0, String(body.querySelectorAll('.app-stat').length));

    const navButtons = Array.from(document.querySelectorAll('[data-app-nav] button'));
    check('El panel tiene 12 vistas', navButtons.length === 12, String(navButtons.length));
    check(
      'Las vistas cubren los 8 modulos',
      ['matches', 'teams', 'divisions', 'news', 'announcements', 'awards', 'pubs', 'important', 'staff', 'rules', 'settings'].every(
        (v) => navButtons.some((b) => b.dataset.view === v)
      )
    );

    suite('Navegación por vistas');
    for (const [view, expected] of Object.entries(VIEWS)) {
      try {
        mod.go(view);
        const cards = body.querySelectorAll('.app-card').length;
        check(`Vista ${view}`, cards === expected, `${cards} tarjetas, esperado ${expected}`);
        check(`Vista ${view} tiene título`, title.textContent.length > 0, title.textContent);
      } catch (error) {
        check(`Vista ${view}`, false, error.message);
      }
    }
    mod.go('matches');
    check('La vista activa se marca en el menú', document.querySelector('[data-app-nav] button.is-active').dataset.view === 'matches');

    suite('Clasificaciones dentro de Partidos');
    mod.go('matches');
    await wait();
    check('Pide las clasificaciones', calls.includes('GET /standings'));
    const tables = body.querySelectorAll('table.standings');
    check('Muestra 2 clasificaciones', tables.length === 2, String(tables.length));
    check('La clasificación lista 14 filas', body.querySelectorAll('table.standings tbody tr').length === 14);
    check('Desaparece el mensaje de carga', body.querySelectorAll('[data-standings]').length === 0);

    suite('Formularios de bloques');
    for (const view of ['divisions', 'rules', 'settings']) {
      try {
        mod.go(view);
        const cards = body.querySelectorAll('.app-card');
        check(`${view} lista sus bloques`, cards.length === VIEWS[view], String(cards.length));
        const publish = body.querySelector('.app-publish button');
        check(`${view} tiene botón Publicar`, Boolean(publish));
        check(`${view} oculta Publicar hasta editar`, publish.hidden === true);
        click(cards[0].querySelector('.app-card-actions button'));
        check(`${view} abre el editor`, document.querySelector('[data-modal]').hidden === false);
        check(
          `${view} precarga valores`,
          Array.from(document.querySelectorAll('[data-modal-fields] [name]')).some((n) => n.value !== '')
        );
        click(document.querySelector('[data-modal-cancel]'));
      } catch (error) {
        check(`Vista ${view}`, false, error.message);
      }
    }

    suite('Alta de un partido con fecha y hora');
    mod.go('matches');
    await wait();
    const addBtn = Array.from(body.querySelectorAll('button')).find((b) =>
      b.textContent.includes('Nuevo partido')
    );
    check('Hay botón de alta', Boolean(addBtn));
    click(addBtn);
    const form = document.querySelector('[data-modal-form]');
    const fields = Array.from(form.querySelectorAll('[name]')).map((n) => n.name);
    check('El formulario pide local y visitante', fields.includes('home') && fields.includes('away'), fields.join(','));
    check('El formulario pide fecha y hora', fields.includes('date') && fields.includes('time'));
    check('El formulario pide el estado', fields.includes('status'));

    form.querySelector('[name="home"]').value = 'ALFA FC';
    form.querySelector('[name="away"]').value = 'OMEGA FC';
    form.querySelector('[name="date"]').value = '2026-11-21';
    form.querySelector('[name="time"]').value = '20:30';
    form.querySelector('[name="journey"]').value = '7';
    form.querySelector('[name="journeyLabel"]').value = 'Jornada 7';
    form.dispatchEvent(new window.Event('submit', { bubbles: true, cancelable: true }));
    await wait();

    const created = seeded.matches[seeded.matches.length - 1];
    check('Llama a POST /matches', calls.includes('POST /matches'));
    check('Guarda la fecha', created.date === '2026-11-21', created.date);
    check('Guarda la hora', created.time === '20:30', created.time);
    check('Guarda la jornada', created.journey === '7' && created.journeyLabel === 'Jornada 7');
    check('Cierra el modal', document.querySelector('[data-modal]').hidden === true);
    check('El partido aparece en la lista', body.textContent.includes('ALFA FC'));

    suite('Edición de un resultado');
    const card = Array.from(body.querySelectorAll('.app-card')).find((c) =>
      c.textContent.includes('ALFA FC')
    );
    click(card.querySelector('.app-card-actions button'));
    const editForm = document.querySelector('[data-modal-form]');
    check('Precarga el equipo local', editForm.querySelector('[name="home"]').value === 'ALFA FC');
    check('Precarga la hora', editForm.querySelector('[name="time"]').value === '20:30', editForm.querySelector('[name="time"]').value);
    check('Precarga la fecha', editForm.querySelector('[name="date"]').value === '2026-11-21');
    editForm.querySelector('[name="homeGoals"]').value = '5';
    editForm.querySelector('[name="awayGoals"]').value = '1';
    editForm.querySelector('[name="status"]').value = 'finalizado';
    editForm.dispatchEvent(new window.Event('submit', { bubbles: true, cancelable: true }));
    await wait();
    check('Llama a PUT /matches/:id', calls.some((c) => c.startsWith('PUT /matches/')));
    check('Guarda el marcador 5-1', created.homeGoals === '5' && created.awayGoals === '1');
    check('Guarda el estado finalizado', created.status === 'finalizado', created.status);
    check('La tarjeta muestra el marcador', body.textContent.includes('5 - 1'));
    check('La tarjeta muestra la fecha', body.textContent.includes('21/11/26'));

    suite('Borrado');
    window.confirm = () => true;
    const toDelete = Array.from(body.querySelectorAll('.app-card')).find(
      (c) => c.textContent.includes('ALFA FC') && c.querySelector('.is-danger')
    );
    click(toDelete.querySelector('.is-danger'));
    await wait();
    check('Llama a DELETE /matches/:id', calls.some((c) => c.startsWith('DELETE /matches/')));
    check('El partido desaparece', !body.textContent.includes('ALFA FC'));

    suite('Campos de cada colección');
    for (const [view, config] of Object.entries(mod.VIEWS)) {
      const fields = typeof config.fields === 'function' ? config.fields({}) : config.fields || [];
      const valid = fields.every((f) => f.name && f.label && f.type);
      check(`${view}: campos completos`, fields.length > 0 && valid, `${fields.length} campos`);
      const unique = new Set(fields.map((f) => f.name)).size === fields.length;
      check(`${view}: sin nombres repetidos`, unique);
    }

    suite('Helpers de texto');
    check('linesToArray quita vacios', JSON.stringify(mod.linesToArray('a\n\n  \nb')) === '["a","b"]');
    check('splitParts reparte por |', JSON.stringify(mod.splitParts('A | B | C')) === '["A","B","C"]');
    check('splitParts tolera un solo campo', JSON.stringify(mod.splitParts('Sola')) === '["Sola"]');

    suite('Avisos al usuario');
    mod.go('teams');
    await wait(30);
    click(body.querySelector('.app-card-actions button'));
    const errorModal = document.querySelector('[data-modal]');
    const submitBtn = document.querySelector('[data-modal-submit]');
    check('El botón Guardar existe', Boolean(submitBtn));
    check('El modal tiene aria-modal', errorModal.getAttribute('aria-modal') === 'true');
    document.dispatchEvent(new window.KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    check('Escape cierra el modal', errorModal.hidden === true);

    suite('Barra lateral agrupada');
    const navGroups = Array.from(document.querySelectorAll('.app-nav-group'));
    check('El menú se agrupa', navGroups.length === 4, String(navGroups.length));
    check('Los grupos tienen título', navGroups.every((g) => Boolean(g.querySelector('.app-nav-title'))));
    check('Los botones del menú llevan icono', Array.from(document.querySelectorAll('[data-app-nav] button')).every((b) => Boolean(b.querySelector('svg'))));

    suite('Búsqueda y filtros en vivo');
    mod.go('teams');
    await wait(30);
    const search = document.querySelector('[data-app-search]');
    const teamsTotal = body.querySelectorAll('.app-card').length;
    check('El buscador está habilitado en colecciones', search.disabled === false);
    const firstTeam = body.querySelector('.app-card h3').textContent;
    search.value = 'zzzz-no-existe';
    search.dispatchEvent(new window.Event('input', { bubbles: true }));
    const visibleAfterMiss = body.querySelectorAll('.app-card:not([hidden])').length;
    check('La búsqueda sin resultados oculta las tarjetas', visibleAfterMiss === 0, String(visibleAfterMiss));
    check('Aparece el estado vacío', body.querySelectorAll('.app-empty-box:not([hidden])').length === 1);
    search.value = firstTeam;
    search.dispatchEvent(new window.Event('input', { bubbles: true }));
    const visibleAfterHit = body.querySelectorAll('.app-card:not([hidden])').length;
    check('La búsqueda encuentra el equipo', visibleAfterHit === 1, String(visibleAfterHit));
    check('El contador refleja el filtro', body.querySelector('.app-count').textContent.includes('de'));
    check('La búsqueda no borra los datos', body.querySelectorAll('.app-card').length === teamsTotal, String(teamsTotal));

    mod.go('matches');
    await wait(30);
    const filterSets = body.querySelectorAll('.app-filter-set');
    const divisionChips = filterSets[0];
    const statusChips = filterSets[1];
    check('Partidos ofrece filtro por división', Boolean(divisionChips.querySelector('.app-chip[data-value="d1"]')));
    check('Partidos ofrece filtro por estado', Boolean(statusChips.querySelector('.app-chip[data-value="finalizado"]')));
    const shown = () => body.querySelectorAll('.app-list .app-card:not([hidden])').length;

    click(statusChips.querySelector('.app-chip[data-value="programado"]'));
    check('El chip activo queda marcado', statusChips.querySelector('[data-value="programado"]').getAttribute('aria-pressed') === 'true');
    check('El filtro deja solo los programados', shown() === 66, String(shown()));
    click(statusChips.querySelector('.app-chip[data-value="por-definir"]'));
    check('El filtro cambia a por definir', shown() === 4, String(shown()));
    check('El contador refleja el filtro', body.querySelector('.app-count').textContent.includes('de'));
    click(statusChips.querySelector('.app-chip[data-value="all"]'));
    check('El filtro “todas” restaura la lista', shown() === 70, String(shown()));
    check('Las clasificaciones no se filtran', body.querySelectorAll('table.standings').length === 2);

    suite('Atajos de teclado');
    const key = (k) => document.dispatchEvent(new window.KeyboardEvent('keydown', { key: k, bubbles: true }));
    search.blur();
    key('/');
    check('La tecla / enfoca la búsqueda', document.activeElement === search);
    search.blur();
    key('n');
    check('La tecla n abre el alta', document.querySelector('[data-modal]').hidden === false);
    document.dispatchEvent(new window.KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    check('Escape cierra el alta', document.querySelector('[data-modal]').hidden === true);
  } finally {
    await server.stop();
  }
}
