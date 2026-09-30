import { readFileSync } from 'node:fs';
import path from 'node:path';
import { check, loadDom, rootDir, startServer, suite } from './harness.mjs';

const siteJs = readFileSync(path.join(rootDir, 'public', 'js', 'site.js'), 'utf8');

export async function runPublicTests() {
  const server = await startServer();

  try {
    const res = await fetch(`${server.base}/`);
    const html = await res.text();
    const { window, document } = await loadDom(html, server.base);
    window.eval(siteJs);

    const click = (node) =>
      node.dispatchEvent(new window.MouseEvent('click', { bubbles: true, cancelable: true }));

    suite('Pestañas de división');
    const divTabs = document.querySelector('[data-tabs="division"]');
    check('Hay un grupo de pestañas de división', Boolean(divTabs));
    const divButtons = Array.from(divTabs.querySelectorAll('[data-tab]'));
    const divPanels = Array.from(divTabs.querySelectorAll('[data-tab-panel]'));
    check('Hay 2 divisiones', divButtons.length === 2 && divPanels.length === 2);
    check('D1 visible al cargar', divPanels[0].hidden === false && divPanels[1].hidden === true);
    click(divButtons[1]);
    check('D2 visible al pulsar', divPanels[1].hidden === false && divPanels[0].hidden === true);
    check(
      'aria-selected se actualiza',
      divButtons[1].getAttribute('aria-selected') === 'true' &&
        divButtons[0].getAttribute('aria-selected') === 'false'
    );
    click(divButtons[0]);
    check('Vuelve a D1', divPanels[0].hidden === false && divPanels[1].hidden === true);

    suite('Calendario por jornadas');
    const journeyRoots = Array.from(document.querySelectorAll('[data-tabs="journey"]'));
    check('Hay al menos un grupo de jornadas', journeyRoots.length > 0, String(journeyRoots.length));
    const jr = journeyRoots[0];
    const jrButtons = Array.from(jr.querySelectorAll('[data-journey-tab]'));
    const jrPanels = Array.from(jr.querySelectorAll('[data-journey-panel]'));
    check('11 jornadas + 4 playoffs', jrButtons.length === 15 && jrPanels.length === 15, String(jrButtons.length));
    check('Cada botón tiene su propia clave', new Set(jrButtons.map((b) => b.dataset.journeyTab)).size === 15);
    check(
      'Las claves coinciden con los paneles',
      jrButtons.every((b, i) => b.dataset.journeyTab === jrPanels[i].dataset.journeyPanel)
    );
    check('Jornada 1 activa al cargar', jrPanels[0].hidden === false);
    check('Solo hay un panel visible', jrPanels.filter((p) => p.hidden === false).length === 1);
    click(jrButtons[3]);
    check('Jornada 4 se muestra', jrPanels[3].hidden === false && jrPanels[0].hidden === true);
    check('aria-selected de la jornada activa', jrButtons[3].getAttribute('aria-selected') === 'true');
    click(jrButtons[10]);
    check('Jornada 11 se muestra', jrPanels[10].hidden === false, jrPanels[10].dataset.journeyPanel);
    check('La jornada 11 tiene 6 partidos', jrPanels[10].querySelectorAll('.match').length === 6);
    check('Se sigue viendo un solo panel', jrPanels.filter((p) => p.hidden === false).length === 1);
    const playoff = jrPanels[14];
    check('El playoff existe', playoff.dataset.journeyPanel.startsWith('p-'), playoff.dataset.journeyPanel);

    suite('Pestañas de reglas');
    const ruleRoot = document.querySelector('[data-tabs="rules"]');
    check('Hay pestañas de reglas', Boolean(ruleRoot));
    const rButtons = Array.from(ruleRoot.querySelectorAll('[data-rule-tab]'));
    const rPanels = Array.from(ruleRoot.querySelectorAll('[data-rule-panel]'));
    check('4 secciones de reglas', rButtons.length === 4 && rPanels.length === 4, String(rButtons.length));
    click(rButtons[2]);
    check('La tercera sección se muestra', rPanels[2].hidden === false && rPanels[0].hidden === true);

    suite('Galería de premios');
    const filters = document.querySelector('[data-filters]');
    check('Hay fila de filtros', Boolean(filters));
    const filterButtons = Array.from(filters.querySelectorAll('[data-filter]'));
    const awards = Array.from(document.querySelectorAll('.award[data-category]'));
    check('Hay 14 premios', awards.length === 14, String(awards.length));
    check('El filtro "todos" arranca activo', filterButtons[0].dataset.filter === 'all');
    click(filterButtons.find((b) => b.dataset.filter === 'd2'));
    const shown = awards.filter((a) => a.hidden === false);
    check('El filtro D2 deja 7 premios', shown.length === 7, String(shown.length));
    check('Los visibles son de D2', shown.every((a) => a.dataset.division === 'd2'));
    click(filterButtons.find((b) => b.dataset.filter === 'rankings'));
    const ranked = awards.filter((a) => a.hidden === false);
    check('El filtro rankings solo deja rankings', ranked.every((a) => a.dataset.category === 'rankings'), String(ranked.length));
    click(filterButtons[0]);
    check('El filtro "todos" restaura los 14', awards.filter((a) => a.hidden === false).length === 14);

    suite('Lightbox');
    const box = document.querySelector('[data-lightbox-box]');
    check('Existe el lightbox', Boolean(box));
    check('Empieza cerrado', box.hidden === true);
    const trigger = document.querySelector('[data-lightbox]');
    check('Hay imagenes con lightbox', Boolean(trigger));
    click(trigger);
    check('Se abre al pulsar', box.hidden === false);
    check(
      'Carga la imagen correcta',
      document.querySelector('[data-lightbox-img]').getAttribute('src') === trigger.dataset.lightbox
    );
    check('Pone el pie de foto', document.querySelector('[data-lightbox-caption]').textContent === trigger.dataset.caption);
    check('Bloquea el scroll', document.body.classList.contains('is-locked'));
    click(document.querySelector('[data-lightbox-close]'));
    check('Se cierra con el botón', box.hidden === true);
    check('Desbloquea el scroll', !document.body.classList.contains('is-locked'));
    click(trigger);
    document.dispatchEvent(new window.KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    check('Escape lo cierra', box.hidden === true);

    suite('Navegación');
    const navLinks = Array.from(document.querySelectorAll('[data-nav]'));
    check('El menú tiene 8 entradas', navLinks.length === 8, navLinks.map((l) => l.dataset.nav).join(','));
    check(
      'Los destinos son los 8 módulos',
      ['competencia', 'fechas', 'reglas', 'pubs', 'noticias', 'anuncios', 'importante', 'equipos'].every(
        (id) => navLinks.some((l) => l.dataset.nav === id)
      )
    );
    const missing = navLinks.filter((l) => !document.getElementById(l.dataset.nav));
    check('Todos los enlaces tienen destino', missing.length === 0, missing.map((l) => l.dataset.nav).join(','));

    const toggle = document.querySelector('.nav-toggle');
    const nav = document.getElementById('site-nav');
    check('Hay botón de menú móvil', Boolean(toggle) && Boolean(nav));
    check('aria-expanded empieza en false', toggle.getAttribute('aria-expanded') === 'false');
    click(toggle);
    check('El menú se abre', nav.classList.contains('is-open') && toggle.getAttribute('aria-expanded') === 'true');
    click(nav.querySelector('a'));
    check('El menú se cierra al pulsar un enlace', !nav.classList.contains('is-open'));

    suite('Contenido heredado');
    const standings = document.querySelectorAll('#competencia table.standings');
    check('Hay 2 tablas de clasificación', standings.length === 2, String(standings.length));
    check('La clasificación D1 lista 12 equipos', standings[0].querySelectorAll('tbody tr').length === 12);
    check('La clasificación D2 lista 2 equipos', standings[1].querySelectorAll('tbody tr').length === 2);
    const first = standings[0].querySelector('tbody tr');
    check('La fila tiene 10 celdas', first.querySelectorAll('td, th').length === 10, String(first.querySelectorAll('td, th').length));
    check('La cabecera tiene 10 columnas', standings[0].querySelectorAll('thead th').length === 10);

    const rooms = Array.from(document.querySelectorAll('#pubs a[href^="https://www.haxball.com"]'));
    check('Hay 5 salas de HaxBall', rooms.length === 5, String(rooms.length));

    const newsDetails = Array.from(document.querySelectorAll('.news-body details'));
    check('Las noticias tienen acordeón', newsDetails.length === 3, String(newsDetails.length));
    check('Los acordeones empiezan cerrados', newsDetails.every((d) => d.open === false));

    const awardsImgs = Array.from(document.querySelectorAll('.award img'));
    check('Los premios tienen imagen', awardsImgs.length > 0, String(awardsImgs.length));
    check(
      'Las imagenes son locales',
      awardsImgs.every((img) => img.getAttribute('src').startsWith('/assets/'))
    );
    const broken = awardsImgs.filter((img) => !img.getAttribute('alt'));
    check('Las imagenes tienen alt', broken.length === 0, String(broken.length));

    const staffCards = document.querySelectorAll('#equipos .member');
    check('Se listan los miembros del equipo', staffCards.length === 5, String(staffCards.length));
    check('El owner está marcado', document.querySelectorAll('#equipos .member.is-owner').length === 1);
    check(
      'Los miembros traen avatar o marcador',
      Array.from(staffCards).every((c) => c.querySelector('.member-avatar'))
    );

    const matches = document.querySelectorAll('.match');
    check('Se muestran 70 partidos', matches.length === 70, String(matches.length));

    suite('Hero y animaciones');
    const stage = document.querySelector('.hero-stage');
    check('El hero monta el escenario del logo', Boolean(stage));
    check('El logo va sobre tres órbitas', stage.querySelectorAll('.hero-orbit').length === 3);
    check('Cada órbita lleva su punto luminoso', stage.querySelectorAll('.hero-orbit i').length === 3);
    check('El emblema usa el logo del sitio', stage.querySelector('img').getAttribute('src') === '/assets/logo-mark.png');
    check('El hero tiene esquinas decorativas', stage.querySelectorAll('.hero-corner').length === 4);
    check('El titular es único', document.querySelectorAll('h1').length === 1);
    check('El titular divide el nombre de la liga', /The Diamonds/.test(document.querySelector('h1').textContent));
    check('La barra de datos tiene 5 métricas', document.querySelectorAll('.stat-strip li').length === 5);
    check('El marquee lista los 8 módulos', document.querySelectorAll('.marquee-group:first-child .marquee-item').length === 8);
    check('Hay barra de progreso de lectura', Boolean(document.querySelector('.scroll-progress [data-scroll-bar]')));
    const toTop = document.querySelector('[data-to-top]');
    check('El botón de volver arriba empieza oculto', toTop.hidden === true);
    check('El botón de volver arriba es un control', toTop.tagName === 'BUTTON');

    suite('Sin JavaScript');
    const noscripts = Array.from(document.querySelectorAll('noscript'));
    check('Hay un bloque noscript', noscripts.length > 0, String(noscripts.length));
    const noscriptCss = noscripts.map((n) => n.textContent).join(' ');
    check('El noscript enseña los paneles ocultos', noscriptCss.includes('panel[hidden]'), noscriptCss.slice(0, 80));
    check('El noscript oculta los controles', noscriptCss.includes('tablist'));

    // fetch no se usa en el sitio público: debe seguir funcionando sin API
    check('El sitio público no depende de la API', !/fetch\(['"]\/api/.test(siteJs));
  } finally {
    await server.stop();
  }
}
