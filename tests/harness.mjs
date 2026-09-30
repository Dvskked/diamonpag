import { spawn } from 'node:child_process';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

export const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

let failures = 0;
let checks = 0;
let currentSuite = '';

export function suite(name) {
  currentSuite = name;
  console.log(`\n--- ${name} ---`);
}

export function check(label, condition, detail = '') {
  checks += 1;
  if (condition) {
    console.log(`  PASS  ${label}`);
  } else {
    failures += 1;
    console.log(`  FAIL  ${label}${detail ? ` -> ${detail}` : ''}`);
  }
  return Boolean(condition);
}

export function summary() {
  console.log(`\n${checks} comprobaciones, ${failures} fallo(s)`);
  return failures;
}

export function addFailure(label) {
  failures += 1;
  console.log(`  FAIL  ${label}`);
}

/* ---------------- Servidor real en un puerto libre ---------------- */

export async function startServer() {
  const dir = mkdtempSync(path.join(tmpdir(), 'tdl-test-'));
  const dataFile = path.join(dir, 'db.json');
  const port = 3000 + Math.floor(Math.random() * 2000);
  const base = `http://127.0.0.1:${port}`;

  const child = spawn(process.execPath, [path.join(rootDir, 'src', 'server.js')], {
    env: {
      ...process.env,
      PORT: String(port),
      SITE_URL: base,
      DATA_FILE: dataFile,
      NODE_ENV: 'test'
    },
    stdio: ['ignore', 'pipe', 'pipe']
  });

  const logs = [];
  child.stdout.on('data', (b) => logs.push(String(b)));
  child.stderr.on('data', (b) => logs.push(String(b)));

  for (let i = 0; i < 100; i += 1) {
    try {
      const res = await fetch(`${base}/api/salud`);
      if (res.ok) {
        return {
          base,
          dataFile,
          logs,
          async stop() {
            child.kill();
            await new Promise((r) => child.once('exit', r));
            rmSync(dir, { recursive: true, force: true });
          }
        };
      }
    } catch {
      await new Promise((r) => setTimeout(r, 100));
    }
  }
  child.kill();
  throw new Error(`El servidor no arranco en ${base}:\n${logs.join('')}`);
}

/* ---------------- Cliente HTTP con cookies ---------------- */

export function createClient(base) {
  const jar = new Map();

  const cookieHeader = () =>
    [...jar.entries()].map(([name, value]) => `${name}=${value}`).join('; ');

  const store = (res) => {
    const raw = res.headers.getSetCookie ? res.headers.getSetCookie() : [];
    for (const line of raw) {
      const [pair] = line.split(';');
      const eq = pair.indexOf('=');
      if (eq === -1) continue;
      jar.set(pair.slice(0, eq).trim(), pair.slice(eq + 1).trim());
    }
  };

  return {
    jar,
    lastSetCookie: [],
    async request(url, options = {}) {
      const headers = { ...(options.headers || {}) };
      if (options.body) headers['Content-Type'] = 'application/json';
      if (jar.size) headers.Cookie = cookieHeader();
      const res = await fetch(base + url, { ...options, headers, redirect: 'manual' });
      const raw = res.headers.getSetCookie ? res.headers.getSetCookie() : [];
      this.lastSetCookie = raw;
      store(res);
      return res;
    },
    async json(url, options) {
      const res = await this.request(url, options);
      const text = await res.text();
      let body = null;
      try {
        body = JSON.parse(text);
      } catch {
        body = null;
      }
      return { status: res.status, body, text, res };
    },
    async html(url) {
      const res = await this.request(url);
      return { status: res.status, text: await res.text() };
    }
  };
}

/* ---------------- JSDOM ---------------- */

export async function loadDom(html, url = 'http://localhost/') {
  const { JSDOM } = await import('jsdom');
  // 'outside-only' permite ejecutar window.eval dentro del contexto del DOM.
  const dom = new JSDOM(html, { url, runScripts: 'outside-only' });
  const { window } = dom;
  return { dom, window, document: window.document };
}

/** Ejecuta un bundle de navegador dentro de un JSDOM y expone los helpers del DOM. */
export function exposeDomGlobals(window) {
  globalThis.window = window;
  globalThis.document = window.document;
  globalThis.Node = window.Node;
  globalThis.Event = window.Event;
  globalThis.MouseEvent = window.MouseEvent;
  globalThis.FormData = window.FormData;
}

/**
 * Carga un modulo de navegador dentro de Node: recorta el bloque de arranque,
 * le anade una linea de export y lo importa para poder invocar sus funciones.
 * Los globals (document, fetch, FormData...) deben estar fijados antes.
 */
export async function loadBrowserModule(source, { exports: exportNames, globals = '' }) {
  const tail = source.lastIndexOf("$$('[data-app-nav] button')");
  const cut = tail > 0 ? tail : source.length;
  const body = `${globals}\n${source.slice(0, cut)}\n\nexport { ${exportNames.join(', ')} };\n`;

  const dir = mkdtempSync(path.join(tmpdir(), 'tdl-mod-'));
  const file = path.join(dir, 'module.mjs');
  const { writeFileSync } = await import('node:fs');
  writeFileSync(file, body, 'utf8');
  return import(pathToFileURL(file).href);
}
